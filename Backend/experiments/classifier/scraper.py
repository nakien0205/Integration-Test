from amzpy import AmazonScraper

def get_amazon_data():
    # Create scraper for a specific Amazon domain
    scraper = AmazonScraper(
        country_code="in",
        proxies={}
    )

    # Search by query - get up to 2 pages of results
    products = scraper.search_products(query="gaming laptop", max_pages=2)

    # Display the results
    for i, product in enumerate(products[:5], 1):
        print(f"Title: {product['title'] if product['title'] else None}")
        print(f"Price: {product['currency']}{product['price'] if product['price'] else None} ")
        print(f"Rating: {product['rating'] if product['rating'] else None}")
        print('-' * 70)
        product

import requests
from bs4 import BeautifulSoup
import csv
import json
import time
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
import re
from typing import Dict, List, Optional
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ProductScraper:
    """
    A flexible product scraper that can be adapted to different e-commerce websites
    """
    
    def __init__(self, base_url: str, headers: Optional[Dict] = None):
        """
        Initialize the scraper with base URL and optional headers
        
        Args:
            base_url: The base URL of the website to scrape
            headers: Optional HTTP headers for requests
        """
        self.base_url = base_url
        self.session = requests.Session()
        
        # Default headers to avoid being blocked
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        if headers:
            default_headers.update(headers)
        
        self.session.headers.update(default_headers)
        self.products = []
        
    def fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object
        
        Args:
            url: URL to fetch
            retries: Number of retry attempts
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def extract_text(self, element, default: str = "N/A") -> str:
        """
        Safely extract text from an element
        
        Args:
            element: BeautifulSoup element
            default: Default value if extraction fails
            
        Returns:
            Extracted text or default value
        """
        if element:
            text = element.get_text(strip=True)
            return text if text else default
        return default
    
    def extract_price(self, price_text: str) -> tuple:
        """
        Extract price and currency from price text
        
        Args:
            price_text: Raw price text
            
        Returns:
            Tuple of (price, currency)
        """
        if not price_text or price_text == "N/A":
            return ("N/A", "N/A")
        
        # Common currency symbols and codes
        currencies = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
            'USD': 'USD', 'EUR': 'EUR', 'GBP': 'GBP', 'JPY': 'JPY'
        }
        
        # Extract currency
        currency = "N/A"
        for symbol, code in currencies.items():
            if symbol in price_text:
                currency = code
                break
        
        # Extract numeric price
        price_match = re.search(r'[\d,]+\.?\d*', price_text)
        if price_match:
            price = price_match.group().replace(',', '')
        else:
            price = "N/A"
        
        return (price, currency)
    
    def extract_rating(self, rating_text: str) -> float:
        """
        Extract rating from text
        
        Args:
            rating_text: Raw rating text
            
        Returns:
            Rating as float or 0.0
        """
        if not rating_text:
            return 0.0
        
        rating_match = re.search(r'(\d+\.?\d*)', rating_text)
        if rating_match:
            try:
                return float(rating_match.group(1))
            except ValueError:
                return 0.0
        return 0.0
    
    def extract_review_count(self, review_text: str) -> int:
        """
        Extract review count from text
        
        Args:
            review_text: Raw review count text
            
        Returns:
            Review count as integer or 0
        """
        if not review_text:
            return 0
        
        # Look for numbers in the text
        numbers = re.findall(r'\d+', review_text.replace(',', ''))
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                return 0
        return 0
    
    def calculate_discount(self, original_price: str, current_price: str) -> str:
        """
        Calculate discount percentage
        
        Args:
            original_price: Original price
            current_price: Current price
            
        Returns:
            Discount percentage or "N/A"
        """
        try:
            orig = float(original_price)
            curr = float(current_price)
            if orig > curr:
                discount = ((orig - curr) / orig) * 100
                return f"{discount:.1f}%"
        except (ValueError, TypeError, ZeroDivisionError):
            pass
        return "N/A"
    
    def scrape_product(self, product_url: str, selectors: Dict) -> Dict:
        """
        Scrape a single product page
        
        Args:
            product_url: URL of the product
            selectors: Dictionary of CSS/XPath selectors for each field
            
        Returns:
            Dictionary with product data
        """
        soup = self.fetch_page(product_url)
        if not soup:
            return {}
        
        product = {
            'title': 'N/A',
            'brand': 'N/A',
            'description': 'N/A',
            'price': 'N/A',
            'currency': 'N/A',
            'availability': 'N/A',
            'review_count': 0,
            'image_link': 'N/A',
            'average_rating': 0.0,
            'discount': 'N/A',
            'product_url': product_url,
            'scraped_at': datetime.now().isoformat()
        }
        
        # Extract each field using provided selectors
        if 'title' in selectors:
            element = soup.select_one(selectors['title'])
            product['title'] = self.extract_text(element)
        
        if 'brand' in selectors:
            element = soup.select_one(selectors['brand'])
            product['brand'] = self.extract_text(element)
        
        if 'description' in selectors:
            element = soup.select_one(selectors['description'])
            product['description'] = self.extract_text(element)
        
        if 'price' in selectors:
            element = soup.select_one(selectors['price'])
            price_text = self.extract_text(element)
            product['price'], product['currency'] = self.extract_price(price_text)
        
        if 'original_price' in selectors and 'price' in selectors:
            orig_element = soup.select_one(selectors['original_price'])
            if orig_element:
                orig_price_text = self.extract_text(orig_element)
                orig_price, _ = self.extract_price(orig_price_text)
                product['discount'] = self.calculate_discount(orig_price, product['price'])
        
        if 'availability' in selectors:
            element = soup.select_one(selectors['availability'])
            product['availability'] = self.extract_text(element)
        
        if 'review_count' in selectors:
            element = soup.select_one(selectors['review_count'])
            review_text = self.extract_text(element)
            product['review_count'] = self.extract_review_count(review_text)
        
        if 'rating' in selectors:
            element = soup.select_one(selectors['rating'])
            rating_text = self.extract_text(element)
            product['average_rating'] = self.extract_rating(rating_text)
        
        if 'image' in selectors:
            element = soup.select_one(selectors['image'])
            if element:
                # Try different attributes where image URL might be
                image_url = element.get('src') or element.get('data-src') or element.get('href')
                if image_url:
                    product['image_link'] = urljoin(product_url, image_url)
        
        return product
    
    def scrape_product_list(self, list_url: str, product_link_selector: str, 
                           max_products: Optional[int] = None) -> List[str]:
        """
        Scrape product links from a listing page
        
        Args:
            list_url: URL of the listing page
            product_link_selector: CSS selector for product links
            max_products: Maximum number of products to scrape
            
        Returns:
            List of product URLs
        """
        soup = self.fetch_page(list_url)
        if not soup:
            return []
        
        product_links = []
        elements = soup.select(product_link_selector)
        
        for element in elements[:max_products] if max_products else elements:
            href = element.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                product_links.append(full_url)
        
        logger.info(f"Found {len(product_links)} product links")
        return product_links
    
    def scrape_multiple_products(self, product_urls: List[str], selectors: Dict, 
                                delay: float = 1.0) -> None:
        """
        Scrape multiple products with delay between requests
        
        Args:
            product_urls: List of product URLs
            selectors: Dictionary of selectors
            delay: Delay between requests in seconds
        """
        for i, url in enumerate(product_urls, 1):
            logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
            product = self.scrape_product(url, selectors)
            if product:
                self.products.append(product)
            time.sleep(delay)  # Be respectful to the server
    
    def save_to_csv(self, filename: Optional[str] = None) -> str:
        """
        Save scraped products to CSV file
        
        Args:
            filename: Optional filename (default: products_YYYYMMDD_HHMMSS.csv)
            
        Returns:
            Path to the saved file
        """
        if not self.products:
            logger.warning("No products to save")
            return ""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"products_{timestamp}.csv"
        
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)
        
        # Define CSV columns
        columns = [
            'title', 'brand', 'description', 'price', 'currency',
            'availability', 'review_count', 'image_link', 
            'average_rating', 'discount', 'product_url', 'scraped_at'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.products)
        
        logger.info(f"Saved {len(self.products)} products to {filepath}")
        return filepath


# Example usage for Amazon products (you'll need to adapt selectors)
def scrape_amazon_example():
    """
    Example function showing how to use the scraper for Amazon
    Note: You'll need to update selectors based on current Amazon HTML structure
    """
    
    # Initialize scraper
    scraper = ProductScraper("https://www.amazon.com")
    
    # Define selectors for Amazon product pages
    # These are examples and may need updating
    amazon_selectors = {
        'title': 'h1#title',
        'brand': 'a#bylineInfo',
        'description': 'div#feature-bullets',
        'price': 'span.a-price-whole',
        'original_price': 'span.a-price.a-text-price',
        'availability': 'div#availability span',
        'review_count': 'span#acrCustomerReviewText',
        'rating': 'span.a-icon-alt',
        'image': 'div#imgTagWrapperId img'
    }
    
    # Example: Scrape a single product
    # product_url = "https://www.amazon.com/dp/PRODUCT_ID"
    # product = scraper.scrape_product(product_url, amazon_selectors)
    
    # Example: Scrape multiple products from a category page
    # category_url = "https://www.amazon.com/s?k=laptops"
    # product_urls = scraper.scrape_product_list(
    #     category_url, 
    #     'h2.s-title a',  # Selector for product links in search results
    #     max_products=10
    # )
    # scraper.scrape_multiple_products(product_urls, amazon_selectors)
    
    # Save to CSV
    # scraper.save_to_csv()


# Generic example that can be adapted to any website
def main():
    """
    Main function to run the scraper
    """
    
    # Example configuration for a generic e-commerce site
    config = {
        'base_url': 'https://example-store.com',
        'list_page': '/products',
        'product_link_selector': 'a.product-link',
        'selectors': {
            'title': 'h1.product-title',
            'brand': 'span.brand-name',
            'description': 'div.product-description',
            'price': 'span.current-price',
            'original_price': 'span.original-price',
            'availability': 'span.stock-status',
            'review_count': 'span.review-count',
            'rating': 'span.rating-value',
            'image': 'img.product-image'
        }
    }
    
    # Initialize scraper
    scraper = ProductScraper(config['base_url'])
    
    # Get product URLs from listing page
    product_urls = scraper.scrape_product_list(
        urljoin(config['base_url'], config['list_page']),
        config['product_link_selector'],
        max_products=20  # Limit for testing
    )
    
    # Scrape each product
    if product_urls:
        scraper.scrape_multiple_products(
            product_urls, 
            config['selectors'],
            delay=1.5  # Delay between requests
        )
        
        # Save results to CSV
        csv_file = scraper.save_to_csv()
        print(f"Scraping complete! Results saved to: {csv_file}")
    else:
        print("No product URLs found. Please check your selectors.")


# Daily automation script
def run_daily_scraper():
    """
    Function to be called by a scheduler (e.g., cron, Windows Task Scheduler)
    for daily automated scraping
    """
    logger.info("Starting daily scraping job...")
    
    try:
        # Run your scraping configuration here
        main()
        
        # Optional: Send notification of success
        logger.info("Daily scraping completed successfully")
        
    except Exception as e:
        logger.error(f"Daily scraping failed: {e}")
        # Optional: Send error notification
        raise


if __name__ == "__main__":
    # For testing, run the main function
    main()
    
    # For daily automation, you would typically use:
    # - Linux/Mac: cron job
    # - Windows: Task Scheduler
    # - Python: schedule library or APScheduler
    # Example cron entry for daily run at 2 AM:
    # 0 2 * * * /usr/bin/python3 /path/to/scraper.py