# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Testing
- `pytest` - Run all tests (configured with capture settings in pytest.ini)
- `pytest test_file.py` - Run specific test file
- `pytest -v` - Run tests with verbose output

### Environment Setup
- `source env.sh` - Load MongoDB connection URI environment variable
- `pip install -r requirements.txt` - Install dependencies (selenium, pytest, pymongo, pydantic)

### Main Execution
- `python ionity_scrape.py` - Run the main scraper to collect current Ionity pricing data

## Architecture Overview

This is a web scraping application that monitors pricing data from Ionity charging stations across European countries.

### Core Components

**Data Models (`mongo_db_pricing.py`)**
- `PricingModel` - Pydantic model with validation for pricing data including country-currency validation
- Supports versioned pricing history with `valid_from`/`valid_to` timestamps
- MongoDB integration with automatic ObjectId conversion

**Web Scraping (`ionity_scrape.py`)**
- Selenium-based scraper for the Ionity Passport pricing page
- Handles cookie consent and dynamic dropdown interactions
- Processes pricing data for all available countries automatically
- Updates MongoDB with new pricing versions when changes detected

**Text Processing (`ionity_scrape_helpers.py`)**
- `Money` and `SubscriptionTerms` models for structured price data
- Regex-based extraction of prices and currencies from scraped text
- Handles both prefix (€10.50) and postfix (10.50 EUR) currency formats

**Database Operations**
- `insert_pricing()` - Add new pricing records
- `get_current_pricing()` - Retrieve active pricing for country/provider/model
- `update_pricing()` - Version control system that archives old prices and inserts new ones
- `get_pricing_history()` - Retrieve all versions of a pricing model

### Data Flow
1. Scraper visits Ionity website and iterates through country dropdown
2. Extracts pricing cards for each country using helper functions
3. Compares with existing database records using model comparison
4. Updates database with versioned records when changes detected

### Database Schema
MongoDB collection `pricing` with fields:
- Country, currency, provider, pricing_model_name
- price_kWh, subscription_price, initial_subscription_price
- version, valid_from, valid_to for temporal versioning
- Automatic validation ensures currency matches country regulations