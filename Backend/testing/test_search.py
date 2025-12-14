"""
Test script for the improved BM25 + Multi-Signal search engine
"""
import pandas as pd
from main.finder import EcommerceSearchEngine

# Create sample test data
sample_data = {
    'title': [
        'AMD Ryzen 5 9600X 6-Core 12-Thread Desktop Processor',
        'AMD Ryzen 7 5800X 8-Core 16-Thread Desktop Processor',
        'Intel Core i5-13600K Desktop Processor',
        'AMD Ryzen 9 5950X 16-Core Desktop Processor',
        'Logitech G502 HERO Gaming Mouse',
        'Corsair K70 RGB Mechanical Gaming Keyboard',
        'Samsung 970 EVO Plus 1TB NVMe SSD',
        'AMD Radeon RX 6800 XT Graphics Card',
    ],
    'brand': ['AMD', 'AMD', 'Intel', 'AMD', 'Logitech', 'Corsair', 'Samsung', 'AMD'],
    'price': [299.99, 399.99, 319.99, 799.99, 79.99, 169.99, 149.99, 649.99],
    'product_description': [
        'High performance gaming processor with 6 cores',
        'Powerful 8-core processor for gaming and productivity',
        'Latest Intel processor with excellent performance',
        'Top-tier 16-core processor for demanding workloads',
        'High precision gaming mouse with HERO sensor',
        'Premium mechanical keyboard with RGB lighting',
        'Fast NVMe solid state drive with 1TB capacity',
        'High-end graphics card for 4K gaming',
    ],
    'rating_count': [500, 1200, 800, 350, 3500, 2100, 4500, 920],
    'availability': [True, True, True, True, True, True, True, True]
}

df = pd.DataFrame(sample_data)

print("="*70)
print("Testing BM25 + Multi-Signal Search Engine")
print("="*70)

# Initialize engine
engine = EcommerceSearchEngine(cache_size=50)
engine.load_data(df=df)

# Display stats
print("\n📊 Engine Statistics:")
stats = engine.get_stats()
for key, value in stats.items():
    print(f"  {key}: {value}")

# Test cases
test_queries = [
    ('Ryzen 5', "Should find AMD Ryzen 5 9600X with high score"),
    ('AMD processor', "Should find AMD processors"),
    ('gaming mouse', "Should find Logitech G502"),
    ('Intel', "Should find Intel processor"),
    ('graphics card', "Should find AMD Radeon"),
]

print("\n" + "="*70)
print("Running Test Searches")
print("="*70)

for query, description in test_queries:
    print(f"\n🔍 Query: '{query}'")
    print(f"   Expected: {description}")
    
    result = engine.search(query, limit=3)
    
    print(f"   Found: {len(result.results)} results in {result.search_time:.2f}ms")
    
    for i, product in enumerate(result.results, 1):
        score = product['relevance_score']
        title = product['title'][:50]
        print(f"   {i}. [{score:5.2f}/100] {title}...")

# Test similarity search
print("\n" + "="*70)
print("Testing Similarity Search")
print("="*70)

base_product = df.iloc[0]
print(f"\n🔗 Finding products similar to: '{base_product['title'][:50]}...'")

similar = engine.similarity_search(doc_id=0, limit=3)
for i, (doc_id, sim_score) in enumerate(similar, 1):
    product = df.loc[doc_id]
    print(f"   {i}. [{sim_score:5.2f}/100] {product['title'][:50]}...")

# Test with filters
print("\n" + "="*70)
print("Testing Search with Filters")
print("="*70)

print("\n🔍 Query: 'AMD' with price filter ($200-$400)")
result = engine.search(
    query='AMD',
    filters={'min_price': 200, 'max_price': 400},
    limit=5
)

print(f"   Found: {len(result.results)} results")
for i, product in enumerate(result.results, 1):
    print(f"   {i}. [{product['relevance_score']:5.2f}] {product['title'][:40]}... ${product['price']}")

# Test caching
print("\n" + "="*70)
print("Testing Cache Performance")
print("="*70)

print("\n🔄 Running same query twice to test caching...")
result1 = engine.search('AMD Ryzen', limit=3)
print(f"   First search: {result1.search_time:.2f}ms (from_cache: {result1.from_cache})")

result2 = engine.search('AMD Ryzen', limit=3)
print(f"   Second search: {result2.search_time:.2f}ms (from_cache: {result2.from_cache})")
print(f"   Cache hit rate: {result2.cache_hit_rate:.2f}%")

print("\n" + "="*70)
print("✅ All tests completed successfully!")
print("="*70)
