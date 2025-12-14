# Search Engine Tuning Guide 🎛️

This guide helps you optimize the search engine for your specific use case.

---

## 1. Adjusting Signal Weights

Location: `main/finder.py` → `_calculate_multi_signal_score()` method

### Current Default Weights
```python
final_score = (
    0.40 * normalized_bm25 +        # Text relevance
    0.20 * exact_match_score +      # Exact matches
    0.15 * brand_match_score +      # Brand importance
    0.15 * popularity_score +       # Social proof
    0.10 * price_score              # Price competitiveness
)
```

### Use Case: E-commerce with Strong Brand Preference
If users frequently search by brand (e.g., "Nike shoes", "Apple iPhone"):
```python
final_score = (
    0.35 * normalized_bm25 +        # ↓ Reduced text weight
    0.20 * exact_match_score +      # Keep exact match high
    0.25 * brand_match_score +      # ↑ Increase brand importance
    0.10 * popularity_score +       # ↓ Less popularity weight
    0.10 * price_score              # Keep price low
)
```

### Use Case: Discount/Budget Shopping
If price is the primary driver:
```python
final_score = (
    0.30 * normalized_bm25 +        # ↓ Reduced text weight
    0.20 * exact_match_score +      # Keep exact match
    0.10 * brand_match_score +      # ↓ Brand less important
    0.15 * popularity_score +       # Keep popularity
    0.25 * price_score              # ↑ Price is king!
)
```

### Use Case: Trending/Popular Products
If you want to surface bestsellers:
```python
final_score = (
    0.30 * normalized_bm25 +        # ↓ Text matters less
    0.15 * exact_match_score +      # ↓ Exact match less critical
    0.15 * brand_match_score +      # Keep brand moderate
    0.30 * popularity_score +       # ↑ Maximize social proof
    0.10 * price_score              # Keep price low
)
```

### Use Case: Technical/Specific Product Search
When users know exactly what they want (model numbers, SKUs):
```python
final_score = (
    0.35 * normalized_bm25 +        # Keep text relevance
    0.40 * exact_match_score +      # ↑ Exact match crucial!
    0.10 * brand_match_score +      # ↓ Brand less important
    0.10 * popularity_score +       # ↓ Popularity less important
    0.05 * price_score              # ↓ Price least important
)
```

---

## 2. Adjusting Relevance Thresholds

Location: `main/finder.py` → `product_retriever()` function

### Current Default
```python
def product_retriever(search_query: str, min_relevance_threshold: float = 30.0):
```

### Recommended Thresholds by Scenario

#### High-Quality Catalog (Well-structured, complete data)
```python
min_relevance_threshold = 25.0  # Lower threshold, trust your data
```

#### Poor-Quality Catalog (Incomplete descriptions, sparse data)
```python
min_relevance_threshold = 40.0  # Higher threshold, more crawling
```

#### Mixed Catalog Quality
```python
min_relevance_threshold = 30.0  # Balanced approach (default)
```

#### Development/Testing
```python
min_relevance_threshold = 10.0  # See all results, debug scoring
```

### Dynamic Threshold Based on Query Type
```python
def product_retriever(search_query: str):
    # Detect specific queries (model numbers, SKUs)
    if re.search(r'\b[A-Z0-9]{4,}\b', search_query):
        threshold = 40.0  # High threshold for specific queries
    else:
        threshold = 25.0  # Lower threshold for general queries
    
    # ... rest of function
```

---

## 3. Tuning BM25 Parameters

Location: `utils.py` → `calculate_bm25_score()` function

### Current Defaults
```python
def calculate_bm25_score(..., k1: float = 1.5, b: float = 0.75):
```

### Parameter: k1 (Term Frequency Saturation)
Controls how quickly term frequency impact saturates.

**Default: k1 = 1.5**

- **Higher k1 (2.0-3.0)**: Term frequency matters more
  - Good for: Technical documents, specific queries
  - Example: "gaming laptop gaming performance gaming"
  
- **Lower k1 (1.0-1.2)**: Term frequency saturates faster
  - Good for: Product titles, short descriptions
  - Prevents keyword stuffing exploitation

**Recommendation for E-commerce**: k1 = 1.2 to 1.5

### Parameter: b (Document Length Normalization)
Controls how much document length affects scoring.

**Default: b = 0.75**

- **Higher b (0.9-1.0)**: Strong length normalization
  - Good for: Mixed content (short titles + long descriptions)
  - Prevents long documents from dominating
  
- **Lower b (0.3-0.5)**: Weak length normalization
  - Good for: Similar-length documents
  - Longer docs get slight boost

**Recommendation for E-commerce**: b = 0.75 (standard)

### Example Adjustments

#### For Technical Products with Detailed Specs
```python
k1 = 1.8  # Higher saturation for detailed specs
b = 0.6   # Less length penalty (specs can be long)
```

#### For Simple Product Catalogs
```python
k1 = 1.2  # Lower saturation (titles are short)
b = 0.8   # More length normalization
```

---

## 4. Adjusting Exact Match Bonuses

Location: `main/finder.py` → `_calculate_multi_signal_score()` method

### Current Bonuses
```python
if title_matches['exact_match']:
    exact_match_score = 100.0      # "iPhone 14" == "iPhone 14"
elif title_matches['word_boundary_match']:
    exact_match_score = 80.0       # "iPhone" in "iPhone 14 Pro"
elif title_matches['starts_with']:
    exact_match_score = 60.0       # "Samsung Galaxy S21"
elif title_matches['contains']:
    exact_match_score = 40.0       # "gaming" in "Ultra Gaming Laptop"
elif desc_matches['contains']:
    exact_match_score = 20.0       # Found in description
```

### More Aggressive Exact Matching
For technical products where exact model matters:
```python
if title_matches['exact_match']:
    exact_match_score = 100.0      # Perfect match
elif title_matches['word_boundary_match']:
    exact_match_score = 90.0       # ↑ Increase from 80
elif title_matches['starts_with']:
    exact_match_score = 70.0       # ↑ Increase from 60
elif title_matches['contains']:
    exact_match_score = 30.0       # ↓ Decrease partial matches
elif desc_matches['contains']:
    exact_match_score = 10.0       # ↓ Description less important
```

### More Lenient Matching
For general shopping where partial matches are OK:
```python
if title_matches['exact_match']:
    exact_match_score = 100.0
elif title_matches['word_boundary_match']:
    exact_match_score = 75.0       # ↓ Slightly lower
elif title_matches['starts_with']:
    exact_match_score = 60.0       # Keep same
elif title_matches['contains']:
    exact_match_score = 50.0       # ↑ Increase partial match value
elif desc_matches['contains']:
    exact_match_score = 30.0       # ↑ Description more valuable
```

---

## 5. Popularity Scoring Adjustments

Location: `utils.py` → `calculate_popularity_score()` function

### Current Implementation (Logarithmic Scale)
```python
score = (math.log(rating_count + 1) / math.log(max_rating_count + 1)) * 100
```

This uses logarithmic scaling, which:
- Gives diminishing returns to very popular items
- Prevents a few ultra-popular items from dominating
- Better distribution across popularity spectrum

### Alternative: Linear Scale
For strong popularity emphasis:
```python
def calculate_popularity_score(rating_count: int, max_rating_count: int) -> float:
    if max_rating_count == 0:
        return 0.0
    
    # Linear scaling
    score = (rating_count / max_rating_count) * 100
    return max(0.0, min(100.0, score))
```

### Alternative: Square Root Scale (Middle Ground)
```python
import math

def calculate_popularity_score(rating_count: int, max_rating_count: int) -> float:
    if max_rating_count == 0:
        return 0.0
    
    # Square root scaling
    score = (math.sqrt(rating_count) / math.sqrt(max_rating_count)) * 100
    return max(0.0, min(100.0, score))
```

### Comparison
| Rating Count | Linear | Square Root | Logarithmic (Current) |
|--------------|--------|-------------|----------------------|
| 10           | 1.0    | 3.2         | 10.0                 |
| 100          | 10.0   | 32.0        | 50.0                 |
| 1,000        | 100.0  | 100.0       | 75.0                 |

**Recommendation**: Keep logarithmic for balanced results

---

## 6. Cache Tuning

Location: `main/finder.py` → `EcommerceSearchEngine.__init__()`

### Current Default
```python
def __init__(self, cache_size: int = 100):
```

### Adjust Based on Memory & Usage

#### High Traffic, Memory Available
```python
engine = EcommerceSearchEngine(cache_size=500)
```

#### Low Memory Environment
```python
engine = EcommerceSearchEngine(cache_size=50)
```

#### Very High Traffic (Dedicated Server)
```python
engine = EcommerceSearchEngine(cache_size=1000)
```

### Cache Size Guidelines
- **50-100**: Personal/development use
- **200-500**: Small to medium e-commerce site
- **500-1000**: Large e-commerce site
- **1000+**: Enterprise level

**Memory estimate**: ~1-2 KB per cached query result

---

## 7. Performance Tuning

### Index Build Performance

For large catalogs, optimize indexing:

```python
def load_data(self, csv_path: str = None, df: pd.DataFrame = None):
    """Load product data with progress tracking"""
    start_time = time.time()
    
    if csv_path:
        # Use chunked reading for very large files
        chunk_size = 10000
        chunks = pd.read_csv(csv_path, chunksize=chunk_size)
        self.products = pd.concat(chunks, ignore_index=True)
    elif df is not None:
        self.products = df
    
    # ... rest of method
```

### Search Performance Tips

1. **Limit candidate documents** for very large catalogs:
```python
def _calculate_bm25_scores(self, query_terms: List[str]) -> Dict[int, float]:
    # Limit to top 100 candidates if too many
    candidate_docs = set()
    for term in query_terms:
        if term in self.inverted_index:
            candidate_docs.update(self.inverted_index[term])
    
    # If too many candidates, sample or use heuristics
    if len(candidate_docs) > 500:
        # Score only the first N that match multiple terms
        # (implementation detail)
        pass
```

2. **Use appropriate result limits**:
```python
# Good: Limit to what you need
result = engine.search(query, limit=10)

# Bad: Retrieving too many results
result = engine.search(query, limit=100)  # Slower!
```

---

## 8. Monitoring & Analytics

### Add Logging for Score Distribution

```python
def search(self, query: str = "", ...) -> SearchResult:
    # ... existing code ...
    
    # Log score distribution
    if result_data:
        scores = [p['relevance_score'] for p in result_data]
        print(f"Query: {query}")
        print(f"  Scores: min={min(scores):.1f}, max={max(scores):.1f}, avg={sum(scores)/len(scores):.1f}")
    
    return search_result
```

### Track Query Performance

```python
import logging

logging.basicConfig(filename='search_analytics.log', level=logging.INFO)

def product_retriever(search_query: str, min_relevance_threshold: float = 30.0):
    # ... existing code ...
    
    if high_quality_results:
        logging.info(f"DB_HIT|{search_query}|{len(high_quality_results)}|{result.search_time:.2f}ms")
    else:
        logging.info(f"CRAWL|{search_query}|{best_score:.2f}|threshold={min_relevance_threshold}")
    
    # ... rest of function
```

---

## 9. A/B Testing Different Configurations

Create variant configurations:

```python
# config_a.py (Current)
WEIGHTS = {
    'bm25': 0.40,
    'exact_match': 0.20,
    'brand': 0.15,
    'popularity': 0.15,
    'price': 0.10
}
THRESHOLD = 30.0

# config_b.py (Variant)
WEIGHTS = {
    'bm25': 0.35,
    'exact_match': 0.25,
    'brand': 0.20,
    'popularity': 0.15,
    'price': 0.05
}
THRESHOLD = 25.0
```

Then randomly assign users and track metrics:
- Click-through rate
- Conversion rate
- Search time
- Crawl rate

---

## 10. Quick Reference: Common Scenarios

### Scenario: Too Many Crawls
**Problem**: Database has good data but still crawling too often  
**Solution**: Lower threshold to 25.0 or 20.0

### Scenario: Poor Result Quality
**Problem**: Returning irrelevant results  
**Solution**: Increase threshold to 40.0, increase exact_match weight to 0.30

### Scenario: Missing Specific Products
**Problem**: Exact product searches not finding items  
**Solution**: Increase exact_match bonus from 80→90, increase exact_match weight to 0.25

### Scenario: Brand Matters Most
**Problem**: Users care about brand more than features  
**Solution**: Increase brand weight to 0.25, reduce other weights proportionally

### Scenario: Price-Sensitive Users
**Problem**: Users want cheapest options first  
**Solution**: Increase price weight to 0.25, use sort_by='price_low' filter

---

## Summary Checklist

- [ ] Adjust signal weights for your business priorities
- [ ] Set appropriate relevance threshold for your catalog quality
- [ ] Tune BM25 parameters (k1, b) if needed
- [ ] Configure cache size based on traffic
- [ ] Add monitoring/logging for insights
- [ ] Test different configurations
- [ ] Monitor crawl rate vs. DB hit rate
- [ ] Gather user feedback on result quality

**Remember**: Start with defaults, measure, then tune! 📊
