# Saya.pk Discount Finder

A web scraper that monitors products on Saya.pk for price changes and discounts.

## Setup

1. Clone this repository:
```bash
git clone <your-repository-url>
cd saya-discount-finder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create data directory:
```bash
mkdir -p data
```

4. Run the scraper:
```bash
python fix_data.py
```

## Files
- `fix_data.py`: Main scraper script that collects product data
- `view_data.py`: Script to view collected data and price history
- `requirements.txt`: Python package dependencies

## Features

- Full product catalog scraping
- Hourly price monitoring
- Discount detection and tracking
- Efficient data storage using SQLite
- Price history tracking
- Minimal resource usage

## Usage

### Initial Scrape
```bash
python src/initial_scrape.py
```

### Price Monitor
```bash
python src/price_monitor.py
```

## Project Structure

```
saya_discount_finder/
├── src/
│   ├── __init__.py
│   ├── initial_scrape.py
│   ├── price_monitor.py
│   ├── database.py
│   └── utils.py
├── data/
│   └── products.db
├── logs/
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

Create a `.env` file with the following variables:
```
DATABASE_PATH=data/products.db
SCAN_INTERVAL=3600  # in seconds
USER_AGENT=Mozilla/5.0 ...
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License 