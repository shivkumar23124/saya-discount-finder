# -*- coding: utf-8 -*-
import os
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any, Optional
import sqlite3
import pandas as pd
from tabulate import tabulate
import schedule
from scraper import make_request, parse_price, Product, PriceHistory, SessionLocal, engine, Base, get_headers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('data', 'price_monitor.log'))
    ]
)
logger = logging.getLogger(__name__)

def check_price_changes():
    """Check for price changes in all products"""
    logger.info("Starting price check")
    db = SessionLocal()
    
    try:
        # Get all products
        products = db.query(Product).all()
        logger.info(f"Checking prices for {len(products)} products")
        
        discounts_found = 0
        
        for product in products:
            # Construct product URL
            url = f"https://saya.pk/products/{product.slug}"
            response = make_request(url)
            
            if not response:
                continue
                
            soup = BeautifulSoup(response.text, 'lxml')
            price_elem = soup.select_one('.price')
            
            if not price_elem:
                continue
                
            current_price = parse_price(price_elem.text)
            
            # Check if price has changed
            if current_price != product.current_price and current_price > 0:
                # Log price history
                price_history = PriceHistory(
                    product_id=product.id,
                    price=current_price,
                    timestamp=datetime.utcnow()
                )
                db.add(price_history)
                
                # Update product price
                old_price = product.current_price
                product.current_price = current_price
                product.last_checked = datetime.utcnow()
                
                # If price dropped, log it
                if current_price < old_price:
                    discount_percentage = ((old_price - current_price) / old_price) * 100
                    logger.info(f"Price drop detected for {product.name}:")
                    logger.info(f"Old price: Rs. {old_price:.2f}")
                    logger.info(f"New price: Rs. {current_price:.2f}")
                    logger.info(f"Discount: {discount_percentage:.1f}%")
                    discounts_found += 1
            
            time.sleep(1)  # Be nice to the server
            
        db.commit()
        logger.info(f"Price check completed. Found {discounts_found} new discounts.")
        
    except Exception as e:
        logger.error(f"Error during price check: {str(e)}")
        db.rollback()
    finally:
        db.close()

def get_top_discounts(limit: int = 10) -> pd.DataFrame:
    """Get top discounted products"""
    db = SessionLocal()
    try:
        # Query products with discounts
        products = (
            db.query(Product)
            .filter(Product.current_price < Product.original_price)
            .all()
        )
        
        # Calculate discounts and create DataFrame
        discounts = []
        for p in products:
            discount = ((p.original_price - p.current_price) / p.original_price) * 100
            discounts.append({
                'name': p.name,
                'original_price': p.original_price,
                'current_price': p.current_price,
                'discount_percentage': discount,
                'url': f"https://saya.pk/products/{p.slug}"
            })
        
        df = pd.DataFrame(discounts)
        if not df.empty:
            df = df.sort_values('discount_percentage', ascending=False).head(limit)
            df['discount_percentage'] = df['discount_percentage'].round(1)
            
        return df
    finally:
        db.close()

def generate_price_history_report(days: int = 7) -> pd.DataFrame:
    """Generate price history report for the last N days"""
    db = SessionLocal()
    try:
        # Calculate date threshold
        threshold = datetime.utcnow() - timedelta(days=days)
        
        # Get price changes
        history = (
            db.query(PriceHistory, Product)
            .join(Product, PriceHistory.product_id == Product.id)
            .filter(PriceHistory.timestamp >= threshold)
            .all()
        )
        
        # Create DataFrame
        changes = []
        for h, p in history:
            changes.append({
                'name': p.name,
                'price': h.price,
                'timestamp': h.timestamp,
                'url': f"https://saya.pk/products/{p.slug}"
            })
        
        return pd.DataFrame(changes)
    finally:
        db.close()

def print_report():
    """Print current discount report"""
    # Get top discounts
    discounts_df = get_top_discounts(limit=20)
    
    if discounts_df.empty:
        logger.info("No discounts found.")
        return
    
    # Format and print report
    logger.info("\n=== Top Discounts Right Now ===")
    logger.info(tabulate(
        discounts_df,
        headers=['Name', 'Original', 'Current', 'Discount %', 'URL'],
        tablefmt='grid',
        floatfmt='.1f'
    ))
    
    # Save report to CSV
    report_path = os.path.join('data', f'discounts_{datetime.now().strftime("%Y%m%d_%H%M")}.csv')
    discounts_df.to_csv(report_path, index=False)
    logger.info(f"\nReport saved to: {report_path}")

def main():
    """Main function to run the price monitor"""
    logger.info("Starting price monitor")
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Schedule tasks
    schedule.every(1).hours.do(check_price_changes)
    schedule.every(1).hours.do(print_report)
    schedule.every().day.at("00:00").do(generate_price_history_report)
    
    # Run initial check
    check_price_changes()
    print_report()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 