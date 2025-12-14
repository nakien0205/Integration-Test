import pandas as pd
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, OrderedDict
from dataclasses import dataclass
import time
import json
from crawler.crawl import crawl
from supabase import create_client, Client
import os
from utils import (
    tokenize_text,
    normalize_score,
    calculate_bm25_score,
    detect_exact_matches,
    calculate_price_competitiveness,
    calculate_popularity_score
)

SUPABASE_URL = os.getenv("SUPABASE_URL")  # or your Supabase URL
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # or your Supabase anon key

@dataclass
class SearchResult:
    """Container for search results with metadata"""
    results: List[Dict]
    search_time: float
    total_results: int
    from_cache: bool
    cache_hit_rate: float

class EcommerceSearchEngine:
    """
    High-performance e-commerce search engine with BM25 and multi-signal ranking.
    
    Features:
    - BM25 algorithm (superior to TF-IDF)
    - Multi-signal ranking (relevance + exact matches + brand + popularity + price)
    - Inverted index for fast search
    - LRU caching system
    - Multiple specialized indexes
    """
    
    def __init__(self, cache_size: int = 100):
        # Core data structures
        self.products = pd.DataFrame()
        self.inverted_index: Dict[str, Set[int]] = defaultdict(set)
        self.brand_index: Dict[str, List[int]] = defaultdict(list)
        self.price_index: List[Tuple[int, float]] = []
        
        # BM25 specific data
        self.term_doc_freq: Dict[str, int] = {}  # Document frequency for each term
        self.doc_lengths: Dict[int, int] = {}  # Length of each document
        self.avg_doc_length: float = 0.0
        
        # Caching system
        self.cache = OrderedDict()
        self.cache_size = cache_size
        self.cache_hits = 0
        self.total_searches = 0
        
        # Performance metrics
        self.index_build_time = 0
        self.avg_search_time = 0
        
    def load_data(self, csv_path: str = None, df: pd.DataFrame = None):
        """Load product data from CSV or DataFrame"""
        start_time = time.time()
        
        if csv_path:
            self.products = pd.read_csv(csv_path)
        elif df is not None:
            self.products = df
        else:
            raise ValueError("Either csv_path or df must be provided")
        
        # Ensure required columns exist
        self._validate_data()
        
        # Build all indexes
        self._build_indexes()
        
        self.index_build_time = time.time() - start_time
    
    def _validate_data(self):
        """Validate that required columns exist"""
        required_columns = ['title', 'price', 'brand']
        for col in required_columns:
            if col not in self.products.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Add optional columns with defaults if missing
        if 'product_description' not in self.products.columns:
            self.products['product_description'] = ''
        if 'rating_count' not in self.products.columns:
            self.products['rating_count'] = 0
        if 'availability' not in self.products.columns:
            self.products['availability'] = True
    
    def _build_indexes(self):
        """Build all search indexes including BM25 data structures"""
        total_length = 0
        
        for idx, row in self.products.iterrows():
            # Get searchable text
            searchable_text = f"{row['title']} {row['product_description']} {row['brand']}"
            tokens = tokenize_text(searchable_text)
            
            # Store document length
            self.doc_lengths[idx] = len(tokens)
            total_length += len(tokens)
            
            # Build inverted index and count term document frequency
            unique_terms = set(tokens)
            for term in unique_terms:
                self.inverted_index[term].add(idx)
                self.term_doc_freq[term] = self.term_doc_freq.get(term, 0) + 1
            
            # Build brand index
            if row['brand']:
                self.brand_index[str(row['brand'])].append(idx)
            
            # Build price index
            self.price_index.append((idx, float(row['price'])))
        
        # Calculate average document length for BM25
        if self.doc_lengths:
            self.avg_doc_length = total_length / len(self.doc_lengths)
        
        # Sort price index for range queries
        self.price_index.sort(key=lambda x: x[1])
    
    def _calculate_bm25_scores(self, query_terms: List[str]) -> Dict[int, float]:
        """Calculate BM25 scores for all matching documents"""
        doc_scores = defaultdict(float)
        
        # Find all documents that contain at least one query term
        candidate_docs = set()
        for term in query_terms:
            if term in self.inverted_index:
                candidate_docs.update(self.inverted_index[term])
        
        # Calculate BM25 score for each candidate
        total_docs = len(self.products)
        
        for doc_id in candidate_docs:
            # Get document tokens
            row = self.products.loc[doc_id]
            searchable_text = f"{row['title']} {row['product_description']} {row['brand']}"
            doc_terms = tokenize_text(searchable_text)
            doc_length = self.doc_lengths.get(doc_id, len(doc_terms))
            
            # Calculate BM25 score
            score = calculate_bm25_score(
                query_terms=query_terms,
                doc_terms=doc_terms,
                doc_length=doc_length,
                avg_doc_length=self.avg_doc_length,
                term_doc_freq=self.term_doc_freq,
                total_docs=total_docs
            )
            
            doc_scores[doc_id] = score
        
        return doc_scores
    
    def _calculate_multi_signal_score(
        self, 
        doc_id: int, 
        query: str,
        bm25_score: float,
        all_bm25_scores: List[float]
    ) -> float:
        """
        Calculate final ranking score using multiple signals.
        
        Combines:
        - BM25 relevance (40%)
        - Exact match bonuses (20%)
        - Brand match (15%)
        - Popularity (15%)
        - Price competitiveness (10%)
        """
        product = self.products.loc[doc_id]
        
        # Normalize BM25 score (0-100)
        if all_bm25_scores:
            min_bm25 = min(all_bm25_scores)
            max_bm25 = max(all_bm25_scores)
            normalized_bm25 = normalize_score(bm25_score, min_bm25, max_bm25)
        else:
            normalized_bm25 = 0.0
        
        # Exact match detection
        title_matches = detect_exact_matches(query, str(product['title']))
        desc_matches = detect_exact_matches(query, str(product.get('product_description', '')))
        
        # Exact match score (0-100)
        exact_match_score = 0.0
        if title_matches['exact_match']:
            exact_match_score = 100.0
        elif title_matches['word_boundary_match']:
            exact_match_score = 80.0
        elif title_matches['starts_with']:
            exact_match_score = 60.0
        elif title_matches['contains']:
            exact_match_score = 40.0
        elif desc_matches['contains']:
            exact_match_score = 20.0
        
        # Brand match score (0-100)
        brand_match_score = 0.0
        query_lower = query.lower()
        brand_lower = str(product['brand']).lower() if product['brand'] else ""
        if brand_lower and brand_lower in query_lower:
            brand_match_score = 100.0
        
        # Popularity score (0-100)
        rating_count = int(product.get('rating_count', 0))
        max_rating_count = int(self.products['rating_count'].max()) if len(self.products) > 0 else 1
        popularity_score = calculate_popularity_score(rating_count, max_rating_count)
        
        # Price competitiveness score (0-100)
        if self.price_index:
            min_price = self.price_index[0][1]
            max_price = self.price_index[-1][1]
            price_score = calculate_price_competitiveness(float(product['price']), min_price, max_price)
        else:
            price_score = 50.0
        
        # Weighted combination
        final_score = (
            0.40 * normalized_bm25 +
            0.20 * exact_match_score +
            0.15 * brand_match_score +
            0.15 * popularity_score +
            0.10 * price_score
        )
        
        return final_score
    
    def search(self, 
               query: str = "", 
               filters: Optional[Dict[str, Any]] = None,
               limit: int = 50) -> SearchResult:
        """
        Main search function with BM25 scoring, multi-signal ranking, caching and filtering.
        
        Args:
            query: Search query string
            filters: Dictionary of filters (min_price, max_price, brand, availability, sort_by)
            limit: Maximum number of results to return
        
        Returns:
            SearchResult object containing results and metadata
        """
        start_time = time.time()
        self.total_searches += 1
        
        if filters is None:
            filters = {}
        
        # Check cache
        cache_key = json.dumps({'query': query, 'filters': filters, 'limit': limit}, sort_keys=True)
        if cache_key in self.cache:
            self.cache_hits += 1
            # Move to end (LRU)
            self.cache.move_to_end(cache_key)
            cached_result = self.cache[cache_key]
            cached_result.from_cache = True
            cached_result.cache_hit_rate = self._get_cache_hit_rate()
            return cached_result
        
        # Perform search
        if query:
            results = self._text_search(query)
        else:
            # Return all products if no query
            results = [(idx, 50.0) for idx in range(len(self.products))]
        
        # Apply filters
        results = self._apply_filters(results, filters)
        
        # Sort results
        results = self._sort_results(results, filters.get('sort_by', 'relevance'))
        
        # Limit results
        results = results[:limit]
        
        # Prepare response
        search_time = time.time() - start_time
        result_data = []
        
        for doc_id, score in results:
            product = self.products.loc[doc_id].to_dict()
            product['relevance_score'] = round(score, 2)
            product['id'] = int(doc_id)
            result_data.append(product)
        
        search_result = SearchResult(
            results=result_data,
            search_time=search_time * 1000,  # Convert to milliseconds
            total_results=len(results),
            from_cache=False,
            cache_hit_rate=self._get_cache_hit_rate()
        )
        
        # Add to cache (with LRU eviction)
        if len(self.cache) >= self.cache_size:
            self.cache.popitem(last=False)  # Remove oldest
        self.cache[cache_key] = search_result
        
        # Update average search time
        self.avg_search_time = (self.avg_search_time * (self.total_searches - 1) + search_time) / self.total_searches
        
        return search_result
    
    def _text_search(self, query: str) -> List[Tuple[int, float]]:
        """Perform text search using BM25 and multi-signal ranking"""
        query_terms = tokenize_text(query)
        if not query_terms:
            return []
        
        # Calculate BM25 scores
        bm25_scores = self._calculate_bm25_scores(query_terms)
        
        if not bm25_scores:
            return []
        
        # Get all BM25 scores for normalization
        all_bm25_scores = list(bm25_scores.values())
        
        # Calculate multi-signal scores
        final_scores = {}
        for doc_id, bm25_score in bm25_scores.items():
            final_score = self._calculate_multi_signal_score(
                doc_id=doc_id,
                query=query,
                bm25_score=bm25_score,
                all_bm25_scores=all_bm25_scores
            )
            final_scores[doc_id] = final_score
        
        # Convert to sorted list
        results = [(doc_id, score) for doc_id, score in final_scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
    
    def _apply_filters(self, results: List[Tuple[int, float]], filters: Dict[str, Any]) -> List[Tuple[int, float]]:
        """Apply filters to search results"""
        filtered_results = []
        
        for doc_id, score in results:
            product = self.products.loc[doc_id]
            
            # Price filter
            if 'min_price' in filters and filters['min_price'] is not None:
                if product['price'] < filters['min_price']:
                    continue
            
            if 'max_price' in filters and filters['max_price'] is not None:
                if product['price'] > filters['max_price']:
                    continue
            
            # Brand filter
            if 'brand' in filters and filters['brand']:
                if product['brand'] != filters['brand']:
                    continue
            
            # Availability filter
            if 'availability' in filters and filters['availability'] is not None:
                if product['availability'] != filters['availability']:
                    continue
            
            filtered_results.append((doc_id, score))
        
        return filtered_results
    
    def _sort_results(self, results: List[Tuple[int, float]], sort_by: str) -> List[Tuple[int, float]]:
        """Sort results based on specified criteria"""
        if sort_by == 'price_low':
            return sorted(results, key=lambda x: self.products.loc[x[0], 'price'])
        elif sort_by == 'price_high':
            return sorted(results, key=lambda x: self.products.loc[x[0], 'price'], reverse=True)
        elif sort_by == 'reviews':
            return sorted(results, key=lambda x: self.products.loc[x[0], 'rating_count'], reverse=True)
        else:  # relevance (default)
            return results  # Already sorted by relevance
    
    def get_brands(self) -> List[str]:
        """Get list of all unique brands"""
        return list(self.brand_index.keys())
    
    def get_price_range(self) -> Tuple[float, float]:
        """Get min and max prices in the catalog"""
        if self.price_index:
            return self.price_index[0][1], self.price_index[-1][1]
        return 0.0, 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_searches == 0:
            return 0.0
        return (self.cache_hits / self.total_searches) * 100
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            'total_products': len(self.products),
            'index_size': len(self.inverted_index),
            'unique_terms': len(self.term_doc_freq),
            'unique_brands': len(self.brand_index),
            'cache_hit_rate': self._get_cache_hit_rate(),
            'avg_search_time_ms': self.avg_search_time * 1000,
            'index_build_time_s': self.index_build_time,
            'cache_size': len(self.cache),
            'total_searches': self.total_searches,
            'avg_doc_length': self.avg_doc_length
        }
    
    def clear_cache(self):
        """Clear the search cache"""
        self.cache.clear()
        self.cache_hits = 0
        self.total_searches = 0
        print("Cache cleared")
    
    def similarity_search(self, doc_id: int, limit: int = 5) -> List[Tuple[int, float]]:
        """
        Find similar products based on brand, price range, and shared terms.
        
        Args:
            doc_id: Product ID to find similar items for
            limit: Maximum number of similar products to return
            
        Returns:
            List of (doc_id, similarity_score) tuples
        """
        if doc_id not in self.products.index:
            return []
        
        base_product = self.products.loc[doc_id]
        similarities = []
        
        # Get base product attributes
        base_brand = str(base_product['brand'])
        base_price = float(base_product['price'])
        base_text = f"{base_product['title']} {base_product['product_description']}"
        base_tokens = set(tokenize_text(base_text))
        
        for other_id in self.products.index:
            if other_id == doc_id:
                continue
            
            other_product = self.products.loc[other_id]
            score = 0.0
            
            # Brand match (40% weight)
            if str(other_product['brand']) == base_brand:
                score += 40.0
            
            # Price similarity (30% weight) - closer price = higher score
            price_diff_pct = abs(float(other_product['price']) - base_price) / base_price if base_price > 0 else 1
            price_score = max(0, 30.0 * (1 - price_diff_pct))
            score += price_score
            
            # Text similarity (30% weight) - Jaccard similarity
            other_text = f"{other_product['title']} {other_product['product_description']}"
            other_tokens = set(tokenize_text(other_text))
            
            if base_tokens and other_tokens:
                intersection = len(base_tokens & other_tokens)
                union = len(base_tokens | other_tokens)
                jaccard = intersection / union if union > 0 else 0
                score += 30.0 * jaccard
            
            similarities.append((other_id, score))
        
        # Sort by score and return top results
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]


def product_retriever(search_query: str, min_relevance_threshold: float = 30.0):
    """
    Retrieve products from database using BM25 search with dynamic thresholds.
    
    Args:
        search_query: Search query string
        min_relevance_threshold: Minimum relevance score (0-100) to consider results valid.
                                 Default is 30.0. Lower threshold for broader results.
    
    Returns:
        List of matching products or triggers web crawling if no good matches found
    """
    
    # Fetch data from Supabase
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table('testing').select('*').execute()
    data = pd.DataFrame(response.data)
    
    # Initialize search engine
    engine = EcommerceSearchEngine()
    engine.load_data(df=data)
    
    query = search_query.strip()
    
    # Perform search with improved BM25 + multi-signal ranking
    result = engine.search(query, filters=None, limit=5)
    
    # Check if we have good quality results
    # Scores are now normalized 0-100, so we can use meaningful thresholds
    if result.results:
        high_quality_results = [
            product for product in result.results 
            if product['relevance_score'] >= min_relevance_threshold
        ]
        
        if high_quality_results:
            # We have good matches in database
            return high_quality_results
            # for i, prod in enumerate(high_quality_results, 1):
            #     print(f"  {i}. {prod.get('title', 'N/A')[:60]}... (score: {prod['relevance_score']:.2f})")
        else:
            # All results below threshold - trigger crawling
            # print(f"✗ No products found with relevance >= {min_relevance_threshold}. Triggering web crawl...")
            # best_score = max(p['relevance_score'] for p in result.results)
            # print(f"  (Best match in DB had score: {best_score:.2f})")
            return crawl(search_query)
    else:
        # No results at all
        print("✗ No products found in database. Triggering web crawl...")
        return crawl(search_query)
