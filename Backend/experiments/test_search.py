from sql_query.sql_function import search_products

def display_results(result, page_number):
    # Display the results in a structured format
    if result['success']:
        print(f"===== SEARCH RESULTS - PAGE {page_number} =====")
        print(f"Showing {result['count']} of {result['total_count']} total products\n")
        
        # Display query parameters used
        print("\nSearch parameters:")
        for param, value in result['query_params'].items():
            if param not in ['result_limit', 'result_offset']:
                print(f"  {param}: {value}")
        
        # Display product information
        print("\nProducts:")
        start_index = result['pagination']['offset'] + 1
        for i, product in enumerate(result['data'], start_index):
            print(f"\n--- Product {i} ---")
            print(f"Title: {product.get('title')}")
            print(f"Brand: {product.get('brand')}")
            print(f"Price: {product.get('final_price')} {product.get('currency')}")
            print(f"Availability: {product.get('availability')}")
            if product.get('rating') is not None:
                print(f"Rating: {product.get('rating')}/5 ({product.get('reviews_count')} reviews)")
            print(f"URL: {product.get('url')}")
    else:
        print("Search failed:")
        print(f"Error: {result['error']}")

def main():
    # Test query
    prompt = 'I want an AC power cord from OMNIHIL'
    items_per_page = 3  # Small number for demonstration purposes
    
    # Get first page of results
    page1 = search_products(prompt, limit=items_per_page, offset=0)
    display_results(page1, 1)
    
    # If there are more pages, get the second page
    if page1['pagination']['has_more']:
        print("\n" + "="*50 + "\n")
        page2 = search_products(prompt, limit=items_per_page, offset=items_per_page)
        display_results(page2, 2)
        
        # If there are still more pages, get the third page
        if page2['pagination']['has_more']:
            print("\n" + "="*50 + "\n")
            page3 = search_products(prompt, limit=items_per_page, offset=items_per_page*2)
            display_results(page3, 3)

if __name__ == "__main__":
    main()
