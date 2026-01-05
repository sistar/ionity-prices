# Ionity Prices

A web scraping tool that monitors and tracks Ionity EV charging station pricing data across European countries. The application scrapes pricing information from the Ionity website and stores it in MongoDB with automatic versioning to track price changes over time.

## Features

- 🔍 **Automated Web Scraping**: Uses Selenium to scrape Ionity Passport pricing page for all available countries
- 📊 **MongoDB Integration**: Stores pricing data with version control and timestamp tracking
- ✅ **Data Validation**: Uses Pydantic models to validate pricing data, including country-currency relationships
- 📈 **Price History Tracking**: Automatically versions pricing changes with `valid_from` and `valid_to` timestamps
- 🌍 **Multi-Country Support**: Scrapes pricing for all available countries from the Ionity website
- 🧪 **Test Coverage**: Comprehensive test suite for scraping, database operations, and data extraction

## Installation

### Prerequisites

- Python 3.13 or higher
- MongoDB database (local or cloud instance like MongoDB Atlas)
- Chrome/Chromium browser (required for Selenium)
- ChromeDriver (usually installed automatically with Selenium)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ionity-prices
   ```

2. **Install dependencies**

   This project uses Poetry for dependency management. Install dependencies with:

   ```bash
   poetry install
   ```

   Or if using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root with your MongoDB connection URI:

   ```env
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
   ```

   Alternatively, set the `MONGODB_URI` environment variable.

## Usage

### Run the Scraper

Execute the main scraper to collect current Ionity pricing data:

```bash
python ionity_scrape.py
```

The scraper will:

1. Navigate to the Ionity Passport pricing page
2. Handle cookie consent overlay
3. Extract pricing information for all available countries
4. Store or update pricing data in MongoDB
5. Track price changes with automatic versioning

### Database Operations

The project includes several database operations in `mongo_db_pricing.py`:

- `insert_pricing(model)`: Insert new pricing records
- `get_current_pricing(country, provider, pricing_model)`: Retrieve active pricing
- `update_pricing(model)`: Update pricing with automatic version control
- `get_pricing_history(country, provider, pricing_model)`: Retrieve all versions of a pricing model

### Running Tests

Run the test suite:

```bash
pytest
```

Run specific test files:

```bash
pytest test_ionity_scrape.py
pytest test_mongo_db_pricing.py
pytest test_ionity_scrape_helpers.py
```

Run tests with verbose output:

```bash
pytest -v
```

## Project Structure

```
ionity-prices/
├── ionity_scrape.py              # Main scraper script
├── ionity_scrape_helpers.py      # Helper functions for text extraction
├── mongo_db_pricing.py           # MongoDB operations and PricingModel
├── uri.py                        # MongoDB URI configuration
├── test_ionity_scrape.py         # Tests for scraping functionality
├── test_mongo_db_pricing.py      # Tests for database operations
├── test_ionity_scrape_helpers.py # Tests for helper functions
├── pyproject.toml                # Project dependencies and metadata
├── pytest.ini                    # Pytest configuration
└── README.md                     # This file
```

## Core Components

### Data Models (`mongo_db_pricing.py`)

- **PricingModel**: Pydantic model with validation for pricing data
  - Validates country-currency relationships
  - Supports versioned pricing history with `valid_from`/`valid_to` timestamps
  - MongoDB integration with automatic ObjectId conversion

### Web Scraping (`ionity_scrape.py`)

- Selenium-based scraper for the Ionity Passport pricing page
- Handles cookie consent and dynamic dropdown interactions
- Processes pricing data for all available countries automatically
- Updates MongoDB with new pricing versions when changes are detected

### Text Processing (`ionity_scrape_helpers.py`)

- `Money` and `SubscriptionTerms` models for structured price data
- Regex-based extraction of prices and currencies from scraped text
- Handles both prefix (€10.50) and postfix (10.50 EUR) currency formats

## Data Flow

1. Scraper visits Ionity website and iterates through country dropdown
2. For each country, extracts pricing model names, kWh prices, and subscription terms
3. Parses text to extract structured pricing data using regex
4. Creates `PricingModel` instances with validation
5. Checks MongoDB for existing pricing records
6. If changes detected, archives old version and inserts new one
7. If new record, inserts directly into database

## Dependencies

- **selenium** (>=4.39.0): Web scraping and browser automation
- **pymongo[srv]** (>=4.15.5): MongoDB database driver
- **pydantic** (>=2.12.5): Data validation and modeling
- **pytest** (>=9.0.2): Testing framework
- **python-dotenv** (>=1.2.1): Environment variable management

## License

This project is maintained by Ralf Sigmund (ralf.sigmund@gmail.com).

## Notes

- The scraper handles cookie consent overlays automatically
- Pricing versions are tracked hourly (timestamps are floored to the hour)
- Currency validation ensures data integrity between countries and currencies
- The application is designed to run as a scheduled task for continuous price monitoring
