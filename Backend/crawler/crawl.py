import json
import asyncio
import pandas as pd
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonXPathExtractionStrategy
from crawler.schema import link_schema, data_schema
import random
from database.store_data import store_data
from utils import *

page_num = 1
agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 OPR/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def create_search_url(search_terms, page=1):
    """Create Amazon search URL with pagination"""
    base_url = "https://www.amazon.com/s"
    query = '+'.join(search_terms.split())

    if page == 1:
        return f"{base_url}?k={query}"
    else:
        return f"{base_url}?k={query}&page={page}"


async def extract_links(prompt):
    schema = link_schema
    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)

    # Create all crawler tasks at once
    tasks = []
    for i in range(1, page_num + 1):
        url = create_search_url(prompt, i)

        config = CrawlerRunConfig(
            user_agent=random.choice(agents),
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=extraction_strategy,
            verbose=True
        )

        async def fetch_page(page_url, page_config):
            async with AsyncWebCrawler(verbose=True) as crawler:
                return await crawler.arun(url=page_url, config=page_config)

        tasks.append(fetch_page(url, config))

    # Run all pages concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_links = []
    for i, result in enumerate(results, 1):
        if isinstance(result, Exception):
            print(f"Page {i} failed: {result}")
            continue
        if result.success:
            data = json.loads(result.extracted_content)
            all_links.extend(data)
            print(f"Page {i}: {len(data)} links")

    return all_links


async def fetch_product(link):
    schema = data_schema
    extraction_strategy = JsonXPathExtractionStrategy(schema, verbose=True)

    config = CrawlerRunConfig(
        user_agent=random.choice(agents),
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=f'https://amazon.com{link.get("hyperlink")}',
            config=config
        )
        if result.success:
            data = json.loads(result.extracted_content)
            for item in data:
                if item.get('images'):
                    # Remove the suffix in hyperlink to make image bigger
                    item['images'] = increase_resolution(item.get('images'))

            return data
        return []


async def extract_amazon(links):
    # Run all products concurrently with a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent requests

    async def bounded_fetch(link):
        async with semaphore:
            return await fetch_product(link)

    tasks = [bounded_fetch(link) for link in links]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_products = []
    for result in results:
        if isinstance(result, list):
            all_products.extend(result)

    return all_products  # The result is a lists of dictionaries


def store_database(data):
    try:
        for item in data:
            asin = item.get('asin')
            title = item.get('title')
            brand = item.get('brand')
            price_raw = item.get('price')
            rating = float(item.get('rating')) if item.get('rating') else None
            rating_count = item.get('rating_count')
            availability = item.get('availability')
            info = item.get('info')
            product_description = item.get('product_description')
            images = list(item.get('images')) if item.get('images') else []
            return_policy = item.get('return_policy')

            # Parse and clean the price and rating_count fields
            price, discount = parse_price(price_raw)
            rating_count = parse_rating_count(rating_count)

            store_data(asin, title, brand, price, discount, rating, rating_count, availability, info, product_description, images, return_policy)
    
    except Exception as e:
        print(f'Error storing data!\nError type: {e}')


def crawl(query, store=True):
    links = asyncio.run(extract_links(query))
    products_data = asyncio.run(extract_amazon(links))

    # processed_data = processing_data(products_data)

    if store:
        store_database(products_data)
    
    return products_data


def create_data_frame(data, search):
    if data:
        df = pd.DataFrame(data)

        # Save to CSV
        filename = f"amazon_{'_'.join(search)}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n✓ Data saved to {filename}")
        print(f"✓ Total products scraped: {len(df)}")

        # Display summary
        print("\nDataFrame Info:")
        print(df.info())
        print("\nFirst few rows:")
        print(df.head())
    else:
        print("No data was scraped.")