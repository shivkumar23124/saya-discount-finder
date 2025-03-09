import sqlite3
import os
from tabulate import tabulate

def view_data():
    # Connect to the database
    db_path = os.path.join('data', 'products.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total number of products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    print(f"\nTotal products in database: {total_products}")
    
    # Get latest 10 products
    print("\nLatest 10 products:")
    cursor.execute("""
        SELECT name, current_price, original_price, sku, is_in_stock 
        FROM products 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    products = cursor.fetchall()
    print(tabulate(
        products,
        headers=['Name', 'Current Price', 'Original Price', 'SKU', 'In Stock'],
        tablefmt='grid'
    ))
    
    # Get products with discounts
    print("\nProducts with discounts:")
    cursor.execute("""
        SELECT name, current_price, original_price,
               ((original_price - current_price) / original_price * 100) as discount
        FROM products 
        WHERE current_price < original_price
        ORDER BY discount DESC
        LIMIT 10
    """)
    discounts = cursor.fetchall()
    print(tabulate(
        discounts,
        headers=['Name', 'Current Price', 'Original Price', 'Discount %'],
        tablefmt='grid',
        floatfmt='.1f'
    ))
    
    # Get price history
    print("\nRecent price changes:")
    cursor.execute("""
        SELECT p.name, ph.price, ph.timestamp
        FROM price_history ph
        JOIN products p ON p.id = ph.product_id
        ORDER BY ph.timestamp DESC
        LIMIT 10
    """)
    history = cursor.fetchall()
    print(tabulate(
        history,
        headers=['Product', 'Price', 'Timestamp'],
        tablefmt='grid'
    ))
    
    conn.close()

if __name__ == "__main__":
    view_data() 