import re
import math

def parse_price(price_str):
    """
    Parse price string to extract numeric value.
    Examples:
        "$189,00 with 18 percent savings" -> (189.00, 18)
        "$189,00" -> (189.00, None)
        "€1,234.56 with 10 percent savings" -> (1234.56, 10)
    """
    if not price_str:
        return None, None

    discount = None

    # Check if 'with X percent savings' is present
    discount_match = re.search(r'with\s+(\d+)\s+percent\s+savings', price_str, flags=re.IGNORECASE)
    if discount_match:
        discount = int(discount_match.group(1))

    # Remove 'with X percent savings' part if present
    price_str = re.sub(r'\s+with\s+\d+\s+percent\s+savings.*', '', price_str, flags=re.IGNORECASE)

    # Extract numeric part (handles currency symbols, commas, dots)
    # Match patterns like $189,00 or €1,234.56 or 189.00
    match = re.search(r'[\d,]+\.?\d*', price_str)
    if match:
        price_num = match.group()
        # Remove commas and return as string
        price_num = price_num.replace(',', '')
        return float(price_num), discount

    return None, None


def parse_rating_count(rating_count_str):
    """
    Parse rating count string to extract numeric value.
    Examples:
        "1,234 ratings" -> "1234"
        "234 ratings" -> "234"
        "1 rating" -> "1"
    """
    if not rating_count_str:
        return None

    # Extract numeric part (handles commas)
    match = re.search(r'[\d,]+', rating_count_str)
    if match:
        count_num = match.group()
        # Remove commas and return as string
        count_num = count_num.replace(',', '')
        return int(count_num)

    return None


def increase_resolution(images: list):
    try:
        for image in images:
            if image.get('src'):
                url = image['src']

                # Remove standard Amazon image size suffix pattern (_AC_US40_)
                if '_AC_' in url:
                    parts = url.split('._')
                    if len(parts) >= 2:
                        base_url = parts[0]
                        extension = parts[-1].split('_')[-1]
                        image['src'] = f"{base_url}{extension}"

    except TypeError:
        pass
    return images


# ============================================================================
# Search Engine Utility Functions
# ============================================================================

def tokenize_text(text: str) -> list[str]:
    """
    Tokenize and normalize text for search indexing.
    
    Args:
        text: Input text to tokenize
        
    Returns:
        List of normalized tokens
    """
    if not text:
        return []
    
    # Convert to lowercase and remove special characters
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split and filter short tokens
    tokens = [token for token in text.split() if len(token) > 1]
    
    return tokens


def normalize_score(score: float, min_score: float, max_score: float) -> float:
    """
    Normalize score to 0-100 range.
    
    Args:
        score: Raw score
        min_score: Minimum possible score
        max_score: Maximum possible score
        
    Returns:
        Normalized score (0-100)
    """
    if max_score == min_score:
        return 50.0  # Return middle value if no variance
    
    normalized = ((score - min_score) / (max_score - min_score)) * 100
    return max(0.0, min(100.0, normalized))


def calculate_bm25_score(
    query_terms: list[str],
    doc_terms: list[str],
    doc_length: int,
    avg_doc_length: float,
    term_doc_freq: dict[str, int],
    total_docs: int,
    k1: float = 1.5,
    b: float = 0.75
) -> float:
    """
    Calculate BM25 score for a document given a query.
    
    BM25 is superior to TF-IDF for search ranking:
    - Handles document length normalization
    - Saturates term frequency (prevents keyword stuffing)
    - Industry standard algorithm
    
    Args:
        query_terms: List of query tokens
        doc_terms: List of document tokens
        doc_length: Length of the document
        avg_doc_length: Average document length in corpus
        term_doc_freq: Document frequency for each term
        total_docs: Total number of documents
        k1: Term frequency saturation parameter (default: 1.5)
        b: Document length normalization parameter (default: 0.75)
        
    Returns:
        BM25 score
    """
    score = 0.0
    
    # Count term frequencies in document
    doc_term_freq = {}
    for term in doc_terms:
        doc_term_freq[term] = doc_term_freq.get(term, 0) + 1
    
    # Calculate BM25 for each query term
    for term in query_terms:
        if term not in doc_term_freq:
            continue
        
        # Term frequency in document
        tf = doc_term_freq[term]
        
        # Document frequency (how many documents contain this term)
        df = term_doc_freq.get(term, 0)
        
        # IDF calculation (with smoothing)
        idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
        
        # BM25 formula
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * (doc_length / avg_doc_length))
        
        score += idf * (numerator / denominator)
    
    return score


def detect_exact_matches(query: str, text: str) -> dict[str, bool]:
    """
    Detect various types of exact matches between query and text.
    
    Args:
        query: Search query
        text: Text to search in
        
    Returns:
        Dictionary with match types and boolean values
    """
    query_lower = query.lower().strip()
    text_lower = text.lower() if text else ""
    
    return {
        'exact_match': query_lower == text_lower,
        'starts_with': text_lower.startswith(query_lower),
        'contains': query_lower in text_lower,
        'word_boundary_match': bool(re.search(rf'\b{re.escape(query_lower)}\b', text_lower))
    }


def calculate_price_competitiveness(price: float, min_price: float, max_price: float) -> float:
    """
    Calculate price competitiveness score (0-100).
    Lower prices get higher scores.
    
    Args:
        price: Product price
        min_price: Minimum price in catalog
        max_price: Maximum price in catalog
        
    Returns:
        Competitiveness score (0-100)
    """
    if max_price == min_price:
        return 50.0
    
    # Invert: lower price = higher score
    score = 100 - ((price - min_price) / (max_price - min_price)) * 100
    return max(0.0, min(100.0, score))


def calculate_popularity_score(rating_count: int, max_rating_count: int) -> float:
    """
    Calculate popularity score based on rating count (0-100).
    
    Args:
        rating_count: Number of ratings
        max_rating_count: Maximum rating count in catalog
        
    Returns:
        Popularity score (0-100)
    """
    if max_rating_count == 0:
        return 0.0
    
    # Use logarithmic scale for better distribution
    score = (math.log(rating_count + 1) / math.log(max_rating_count + 1)) * 100
    return max(0.0, min(100.0, score))