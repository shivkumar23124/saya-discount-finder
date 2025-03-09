import os
import sqlite3
from bs4 import BeautifulSoup
import requests
import time
from tqdm import tqdm

def get_headers():
    """Get default headers for requests"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def make_request(url, retries=3, delay=5):
    """Make an HTTP request with retry logic"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=get_headers(), timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Request failed for {url}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
            continue
    return None

def parse_price(price_text):
    """Parse price text to float"""
    try:
        # Remove currency symbol and any whitespace/special characters
        clean_price = ''.join(filter(lambda x: x.isdigit() or x == '.', price_text))
        return float(clean_price)
    except (ValueError, TypeError):
        print(f"Failed to parse price: {price_text}")
        return 0.0

def extract_product_data(soup, url):
    """Extract product data from BeautifulSoup object"""
    try:
        # Try different selectors for product name
        name = None
        name_selectors = ['.product-title', 'h1.product-title', '.product-single__title']
        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem:
                name = name_elem.text.strip()
                break

        # Try different selectors for price
        price = 0.0
        price_selectors = ['.price', '.product-price', '.product-single__price']
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = parse_price(price_elem.text)
                break

        # Try different selectors for image
        image_url = ''
        image_selectors = ['.product-featured-image', '.product-single__image', '.product__image']
        for selector in image_selectors:
            image = soup.select_one(selector)
            if image:
                image_url = image.get('src', '')
                if image_url and not image_url.startswith('http'):
                    image_url = 'https:' + image_url
                break

        # Try different selectors for SKU
        sku = ''
        sku_selectors = ['.sku', '.product-sku', '.product-single__sku']
        for selector in sku_selectors:
            sku_elem = soup.select_one(selector)
            if sku_elem:
                sku = sku_elem.text.strip()
                break

        # Try different selectors for description
        description = ''
        desc_selectors = ['.product-description', '.product-single__description', '.product__description']
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.text.strip()
                break

        # Try different selectors for stock status
        is_in_stock = True
        stock_selectors = ['.stock-status', '.product-stock', '.product-inventory']
        for selector in stock_selectors:
            stock_elem = soup.select_one(selector)
            if stock_elem:
                is_in_stock = 'in stock' in stock_elem.text.lower()
                break

        return {
            'name': name or '',
            'current_price': price,
            'original_price': price,
            'image_url': image_url,
            'sku': sku,
            'description': description,
            'is_in_stock': is_in_stock
        }
    except Exception as e:
        print(f"Failed to extract product data from {url}: {str(e)}")
        return {}

def fix_data():
    """Fix scraped data by re-scraping product details"""
    # Connect to the database
    db_path = os.path.join('data', 'products.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all products
    cursor.execute("SELECT id, slug FROM products")
    products = cursor.fetchall()
    print(f"\nFound {len(products)} products to fix")
    
    # Re-scrape each product
    fixed = 0
    for product_id, slug in tqdm(products, desc="Fixing products"):
        url = f"https://saya.pk/products/{slug}"
        response = make_request(url)
        
        if not response:
            continue
            
        soup = BeautifulSoup(response.text, 'lxml')
        product_data = extract_product_data(soup, url)
        
        if product_data:
            # Update product data
            cursor.execute("""
                UPDATE products 
                SET name = ?, current_price = ?, original_price = ?, 
                    image_url = ?, sku = ?, description = ?, is_in_stock = ?
                WHERE id = ?
            """, (
                product_data['name'],
                product_data['current_price'],
                product_data['original_price'],
                product_data['image_url'],
                product_data['sku'],
                product_data['description'],
                product_data['is_in_stock'],
                product_id
            ))
            fixed += 1
        
        time.sleep(1)  # Be nice to the server
        
        # Commit every 10 products
        if fixed % 10 == 0:
            conn.commit()
    
    # Final commit
    conn.commit()
    conn.close()
    
    print(f"\nFixed {fixed} products")

if __name__ == "__main__":
    fix_data() 