import re
import difflib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from scipy import sparse
from sklearn.feature_extraction.text import CountVectorizer
import time

# ----------------------------
# Utility
# ----------------------------

_MONEY = re.compile(r"(?:\$|usd)?\s*(\d{2,7})(?:\s*(?:usd|dollars)?)", re.I)

def _safe_str(x) -> str:
    if pd.isna(x):
        return ""
    return str(x)

def _normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def _lower(s: str) -> str:
    return s.lower()

def _log1p(x):
    return np.log1p(x)

# ----------------------------
# Prompt parsing
# ----------------------------

@dataclass
class ParsedPrompt:
    raw: str
    budget_min: Optional[float]
    budget_max: Optional[float]
    brands: List[str]
    negative_terms: List[str]
    cleaned_query: str

prompt = '''You are a helpful chatbot that extract the user's shopping needs into a phrase that contains these attributes:
1/ What type of product are they looking for?
2/ What brand do they mention prefer?
3/ What price are they expecting?
4/ Do they expect the weight of the product to be light or heavy?
5/ Do they want products they has many ratings?
6/ Are they expecting a discount?
7/ What type of return policy are they expecting?'''

def parse_prompt(prompt: str, brand_vocab: List[str]) -> ParsedPrompt:
    p = prompt.strip()
    pl = p.lower()

    # budgets
    prices = [int(m.group(1)) for m in _MONEY.finditer(pl)]
    budget_min = None
    budget_max = None
    if any(k in pl for k in ["under", "less than", "<", "upto", "up to"]):
        if prices:
            budget_max = prices[0]
    elif "between" in pl and "and" in pl and len(prices) >= 2:
        budget_min, budget_max = prices[:2]
    elif any(k in pl for k in ["over", "more than", ">", "at least", "min"]):
        if prices:
            budget_min = prices[0]
    elif prices:
        budget_max = prices[0]

    # negatives (simple)
    neg = re.findall(r"(?:no|not|avoid|without)\s+([a-z0-9\s]+)", pl)
    negative_terms = [t.strip() for t in neg if t.strip()]

    # brand mention (exact + fuzzy)
    brands_exact = [b for b in brand_vocab if re.search(rf"\b{re.escape(b)}\b", pl)]
    brands_fuzzy = []
    if not brands_exact and brand_vocab:
        tokens = re.findall(r"[a-z0-9\-]+", pl)
        # try 1-gram and 2-gram candidates
        cands = set(tokens + [f"{a} {b}" for a, b in zip(tokens, tokens[1:])])
        for c in cands:
            match = difflib.get_close_matches(c, brand_vocab, n=1, cutoff=0.92)
            if match:
                brands_fuzzy.append(match[0])
    brands = sorted(set(brands_exact + brands_fuzzy))

    # cleaned query (drop obvious money tokens/symbols)
    cleaned = re.sub(r"\$|usd|dollars|under|less than|more than|over|between|and|<|>", " ", pl, flags=re.I)
    cleaned = re.sub(r"\b\d{2,7}\b", " ", cleaned)
    cleaned_query = _normalize_space(cleaned)

    return ParsedPrompt(raw=p, budget_min=budget_min, budget_max=budget_max,
                        brands=brands, negative_terms=negative_terms, cleaned_query=cleaned_query)

# ----------------------------
# BM25 (multi-field)
# ----------------------------

@dataclass
class BM25FieldSpec:
    name: str
    weight: float
    

class MultiFieldBM25:
    def __init__(self, fields: List[BM25FieldSpec], max_features: int = 120000):
        self.fields = fields
        self.max_features = max_features
        self.vectorizer = CountVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=max_features,
            dtype=np.uint32
        )
        self.vocabulary_: Dict[str, int] = {}
        self.field_mats_: Dict[str, sparse.csr_matrix] = {}
        self.idf_: Optional[np.ndarray] = None
        self.avgdl_: Dict[str, float] = {}
        self.k1 = 1.2
        self.b = 0.7

    def fit(self, docs_by_field: Dict[str, List[str]]):
        # Fit vocabulary on concatenated text
        joined = [" ".join(parts) for parts in zip(*[docs_by_field[f.name] for f in self.fields])]
        self.vectorizer.fit(joined)
        self.vocabulary_ = self.vectorizer.vocabulary_

        # Transform each field individually
        for f in self.fields:
            mat = self.vectorizer.transform(docs_by_field[f.name])
            self.field_mats_[f.name] = mat.tocsr()
            # avg doc length for field
            dl = np.asarray(mat.sum(axis=1)).ravel()
            self.avgdl_[f.name] = float(dl.mean() + 1e-9)

        # IDF (global, across joined corpus)
        X = self.vectorizer.transform(joined)
        df = np.bincount(X.indices, minlength=X.shape[1])
        N = X.shape[0]
        # classic BM25 idf
        self.idf_ = np.log((N - df + 0.5) / (df + 0.5) + 1.0)

    def _score_field(self, q_idx: np.ndarray, field_name: str) -> np.ndarray:
        mat = self.field_mats_[field_name]  # [n_docs x n_terms]
        # get tf for query terms only
        mat_q = mat[:, q_idx]  # [n_docs x |q|]
        dl = np.asarray(mat.sum(axis=1)).ravel()
        avgdl = self.avgdl_[field_name]
        # BM25 core
        tf = np.asarray(mat_q.todense()).astype(np.float64)
        if tf.ndim == 1:
            tf = tf.reshape(-1, 1)
        denom = tf + self.k1 * (1 - self.b + self.b * (dl / (avgdl + 1e-9)))[:, None]
        num = tf * (self.k1 + 1.0)
        score = (num / (denom + 1e-9)) * self.idf_[q_idx]
        # sum over query terms; optionally weight by query tf (rarely matters in web search)
        return np.asarray(score.sum(axis=1)).ravel()
    def query(self, q: str, topn: int = 200) -> Tuple[np.ndarray, np.ndarray]:
        # transform query to vector
        q_vec = self.vectorizer.transform([q])
        if q_vec.nnz == 0:
            # nothing in vocab
            n_docs = next(iter(self.field_mats_.values())).shape[0]
            return np.arange(n_docs), np.zeros(n_docs, dtype=float)

        q_idx = q_vec.indices

        # combine per-field scores with weights
        scores = None
        for f in self.fields:
            s = self._score_field(q_idx, f.name)
            s *= f.weight
            scores = s if scores is None else (scores + s)

        # Return indices sorted by scores
        order = np.argsort(-scores)
        if topn is not None:
            order = order[:topn]
        return order, scores

# ----------------------------
# Main Ranker
# ----------------------------

DEFAULT_FIELDS = [
    BM25FieldSpec("title", 3.0),
    BM25FieldSpec("brand", 2.0),
    BM25FieldSpec("description", 1.0),
]

class ProductSearchRanker:
    def __init__(self, csv_path: str = None, df: Optional[pd.DataFrame] = None,
                 fields: List[BM25FieldSpec] = None, max_features: int = 120000):
        
        if csv_path:
            df = pd.read_csv(csv_path)
        self.df = df
        if df is None:
            raise FileNotFoundError("Could not locate processed_data.csv; pass csv_path explicitly.")

        self._normalize_columns()

        # Prepare BM25
        self.fields = fields or [f for f in DEFAULT_FIELDS if f.name in self.df.columns]
        if not self.fields:
            # fall back to any available text-ish column
            candidates = [c for c in self.df.columns if c not in ["final_price", "initial_price", "reviews_count", "availability", "currency"]]
            # choose at most 3
            self.fields = [BM25FieldSpec(c, 1.0) for c in candidates[:3]]

        docs_by_field = {f.name: self.df[f.name].fillna("").astype(str).tolist() for f in self.fields}
        self.bm25 = MultiFieldBM25(self.fields, max_features=max_features)
        self.bm25.fit(docs_by_field)

        # brand vocab for parsing
        self.brand_vocab = []
        if "brand" in self.df.columns:
            self.brand_vocab = sorted(self.df["brand"].dropna().astype(str).str.lower().unique().tolist())

    # ---------- helpers ----------

    def _normalize_columns(self):
        for col in ["initial_price", "final_price", "reviews_count"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        if "availability" in self.df.columns:
            self.df["availability"] = self.df["availability"].astype(str).str.lower()
        # composed text
        if "title" not in self.df.columns:
            # attempt to find a likely title-like column
            for cand in ["name", "product_name"]:
                if cand in self.df.columns:
                    self.df.rename(columns={cand: "title"}, inplace=True)
                    break
        if "description" not in self.df.columns:
            for cand in ["desc", "product_description"]:
                if cand in self.df.columns:
                    self.df.rename(columns={cand: "description"}, inplace=True)

    def _availability_mask(self) -> np.ndarray:
        if "availability" not in self.df.columns:
            return np.ones(len(self.df), dtype=bool)
        avail = self.df["availability"].fillna("")
        mask = (avail == "") | avail.str.contains("in stock|available|true|yes|1")
        return mask.values

    def _phrase_boost(self, q: str) -> np.ndarray:
        # boost exact phrase in title more than in any text col
        n = len(self.df)
        boost = np.ones(n, dtype=float)
        q_esc = re.escape(q)
        title_hit = self.df.get("title", pd.Series([""] * n)).str.lower().str.contains(q_esc, regex=True, na=False).values
        any_hit = pd.Series(
            (self.df.get("title", "").astype(str) + " " +
             self.df.get("brand", "").astype(str) + " " +
             self.df.get("description", "").astype(str)).str.lower()
        ).str.contains(q_esc, regex=True, na=False).values
        boost *= np.where(any_hit, 1.05, 1.0)
        boost *= np.where(title_hit, 1.12, 1.0)
        return boost

    # ---------- public ----------

    def search(self, prompt: str, topk: int = 10, pool: int = 500) -> Tuple[pd.DataFrame, ParsedPrompt]:
        parsed = parse_prompt(prompt, self.brand_vocab)

        # primary retrieval on cleaned query; if empty, fall back to raw
        qtext = parsed.cleaned_query or parsed.raw
        idx, scores = self.bm25.query(qtext, topn=None)  # full ranking once; we'll slice later

        # field phrase boost
        boost = self._phrase_boost(qtext)
        scores = scores * boost

        # availability
        avail_mask = self._availability_mask().astype(float)
        scores = scores * avail_mask

        # price-aware reweighting
        if "final_price" in self.df.columns:
            price = self.df["final_price"].values.astype(float)
            # normalize price to [0, 1]
            pnorm = (price - np.nanmin(price)) / (np.nanmax(price) - np.nanmin(price) + 1e-9)
            scores *= (1.05 - 0.1 * pnorm)  # prefer slightly cheaper

            if parsed.budget_max is not None:
                within = price <= parsed.budget_max
                scores *= np.where(within, 1.18, 0.72)
            if parsed.budget_min is not None:
                above = price >= parsed.budget_min
                scores *= np.where(above, 1.06, 0.75)

        # brand nudges
        if parsed.brands and "brand" in self.df.columns:
            brand_l = self.df["brand"].astype(str).str.lower().values
            is_brand = np.isin(brand_l, parsed.brands)
            scores *= np.where(is_brand, 1.2, 1.0)

        # negative keyword penalty
        if parsed.negative_terms:
            text = (self.df.get("title", "").astype(str).str.lower() + " " +
                    self.df.get("brand", "").astype(str).str.lower() + " " +
                    self.df.get("description", "").astype(str).str.lower())
            neg_hit = np.array([any(t in row for t in parsed.negative_terms) for row in text])
            scores *= np.where(neg_hit, 0.6, 1.0)

        # popularity & discount boosts
        if "reviews_count" in self.df.columns:
            rc = self.df["reviews_count"].fillna(0).values.astype(float)
            scores *= (1.0 + 0.05 * _log1p(rc))  # saturating

        if "initial_price" in self.df.columns and "final_price" in self.df.columns:
            ip = self.df["initial_price"].values.astype(float)
            fp = self.df["final_price"].values.astype(float)
            with np.errstate(divide='ignore', invalid='ignore'):
                disc = np.where((ip > 0) & np.isfinite(ip), (ip - fp) / ip, 0.0)
            scores *= (1.0 + 0.05 * np.clip(disc, 0, 0.8))

        # Final rank (take a decent pool, then topk)
        order = np.argsort(-scores)[:max(pool, topk)]
        top_idx = order[:topk]

        cols = [c for c in ["title", "brand", "final_price", "currency", "availability", "reviews_count", "url"] if c in self.df.columns]
        res = self.df.iloc[top_idx][cols].copy()
        res.insert(0, "score", scores[top_idx])
        res["score"] = res["score"].round(4)
        return res.reset_index(drop=True), parsed

# ----------------------------
# CLI demo (optional)
# ----------------------------

def test(query):
    start = time.time()

    ranker = ProductSearchRanker(csv_path=r'D:\Python\Projects\Shopping\classifier\processed_data.csv')
    out, parsed = ranker.search(query, topk=1)
    print(time.time() - start)
    print(out['title'])

