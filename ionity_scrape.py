# pylint: disable=missing-module-docstring
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError
from dotenv import load_dotenv
from ionity_scrape_helpers import extract_amount_currency, extract_subscription_price
from mongo_db_pricing import (
    PricingModel,
    get_current_pricing,
    insert_pricing,
    update_pricing,
)


load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Create a new client and connect to the server
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    logger.error("MONGODB_URI environment variable is not set")
    raise ValueError("MONGODB_URI environment variable is required")

logger.info("Connecting to MongoDB...")
client = MongoClient(mongo_uri, server_api=ServerApi("1"))
db = client.get_database("charging_providers")
logger.info("Successfully connected to MongoDB database: charging_providers")


def get_passport_prices_for_country(country_names, driver, wait):
    """
    Uses Selenium to scrape the Ionity Passport page for a given country by interacting
    with the custom dropdown and handling a cookie consent overlay.

    Args:
        country_names (list): The list of country names as shown on the website's dropdown (e.g., ["Germany", "Belgium"]).
        driver (webdriver): The Selenium WebDriver instance.
        wait (WebDriverWait): The WebDriverWait instance.

    Returns:
        None: Prints the price information.
    """
    logger.info("Starting to scrape prices for %d countries", len(country_names))

    archive_timestamp = datetime.now(ZoneInfo("UTC"))
    # Floor to the hour
    archive_timestamp = archive_timestamp.replace(minute=0, second=0, microsecond=0)
    logger.debug("Archive timestamp set to: %s (UTC)", archive_timestamp)

    for country in country_names:
        logger.info("Processing country: %s", country)

        # Wait for dropdown toggle to be interactive
        logger.debug("Waiting for dropdown toggle to be clickable for %s", country)
        try:
            toggle = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, ".combi-pricing_dropdown-toggle")
                )
            )
            logger.debug("Dropdown toggle is clickable")
        except TimeoutException:
            logger.error("Timeout waiting for dropdown toggle for country: %s", country)
            continue

        # Check current visibility state of dropdown options
        options_locator = (By.CSS_SELECTOR, ".combi-pricing_select-dropdown-link")
        existing_options = driver.find_elements(*options_locator)
        dropdown_visible = (
            any(opt.is_displayed() for opt in existing_options)
            if existing_options
            else False
        )
        logger.debug("Dropdown visible state: %s", dropdown_visible)

        # Only activate toggle if dropdown isn't visible
        if not dropdown_visible:
            logger.debug("Clicking dropdown toggle for %s", country)
            toggle.click()
            wait.until(EC.visibility_of_element_located(options_locator))
            logger.debug("Dropdown options are now visible")

        # Proceed with option selection
        options = driver.find_elements(*options_locator)
        logger.debug("Found %d country options in dropdown", len(options))
        target_option = None
        for option in options:
            if option.text.strip() == country:
                target_option = option
                break

        if not target_option:
            logger.warning("Could not find dropdown option for country: %s", country)
            continue

        # Click the target option
        logger.debug("Clicking country option: %s", country)
        target_option.click()

        # Wait for the prices to load and print them
        logger.debug("Waiting for pricing cards to load for %s", country)
        time.sleep(1)  # Adjust sleep time if necessary
        pricing_cards = driver.find_elements(
            By.CSS_SELECTOR, ".combi_pricing-card-middle"
        )
        logger.info("Found %d pricing card(s) for %s", len(pricing_cards), country)

        if not pricing_cards:
            logger.warning("No pricing cards found for country: %s", country)
            continue

        models = []
        for idx, pricing_card in enumerate(pricing_cards, 1):
            try:
                text_lines = pricing_card.text.split("\n")
                pricing_model_name = text_lines[0]
                logger.debug(
                    "Processing pricing model %d/%d: %s",
                    idx,
                    len(pricing_cards),
                    pricing_model_name,
                )

                # Extract price per kWh
                try:
                    price_per_kwh = extract_amount_currency(text_lines[1])
                    logger.debug(
                        "Extracted price per kWh: %s %s",
                        price_per_kwh.amount,
                        price_per_kwh.currency,
                    )
                except (ValueError, IndexError) as e:
                    logger.error(
                        "Failed to extract price per kWh for %s in %s: %s",
                        pricing_model_name,
                        country,
                        e,
                    )
                    continue
                # Initialize subscription tracking
                monthly_terms = None
                yearly_terms = None

                # Check if there's a subscription section
                if len(text_lines) >= 5 and text_lines[2] == "plus":
                    # Extract first subscription period
                    try:
                        first_period_terms = extract_subscription_price(text_lines[3], text_lines[4])

                        # Determine which period this is
                        if first_period_terms.monthly_additional_price:
                            monthly_terms = first_period_terms
                        elif first_period_terms.yearly_additional_price:
                            yearly_terms = first_period_terms

                        logger.debug(
                            "Extracted first subscription: %s %s for %s",
                            text_lines[3],
                            text_lines[4],
                            pricing_model_name
                        )
                    except ValueError as e:
                        logger.error(
                            "Failed to extract first subscription price for %s in %s: %s",
                            pricing_model_name,
                            country,
                            e,
                        )
                        continue

                    # Check for second subscription period
                    if len(text_lines) >= 8 and text_lines[5].lower() == "or":
                        try:
                            second_period_terms = extract_subscription_price(text_lines[6], text_lines[7])

                            # Determine which period this is
                            if second_period_terms.monthly_additional_price:
                                monthly_terms = second_period_terms
                            elif second_period_terms.yearly_additional_price:
                                yearly_terms = second_period_terms

                            logger.debug(
                                "Extracted second subscription: %s %s for %s",
                                text_lines[6],
                                text_lines[7],
                                pricing_model_name
                            )
                        except ValueError as e:
                            logger.warning(
                                "Failed to extract second subscription price for %s in %s: %s",
                                pricing_model_name,
                                country,
                                e,
                            )
                            # Continue with only the first period
                else:
                    logger.debug("No subscription fees for %s (free model)", pricing_model_name)

                # Create pricing model
                model = PricingModel(
                    country=country,
                    currency=price_per_kwh.currency,
                    provider="Ionity",
                    pricing_model_name=pricing_model_name,
                    price_kWh=price_per_kwh.amount,
                    monthly_subscription_price=(
                        monthly_terms.monthly_additional_price.amount
                        if monthly_terms and monthly_terms.monthly_additional_price
                        else None
                    ),
                    yearly_subscription_price=(
                        yearly_terms.yearly_additional_price.amount
                        if yearly_terms and yearly_terms.yearly_additional_price
                        else None
                    ),
                    initial_subscription_price=None,  # Deprecated for new records
                    version=1,
                    _id=None,
                    valid_from=archive_timestamp,
                    valid_to=None,
                )
                models.append(model)

                # Build subscription description dynamically
                subscription_parts = []
                if model.monthly_subscription_price is not None:
                    subscription_parts.append(
                        f"Monthly: {model.monthly_subscription_price} {price_per_kwh.currency}"
                    )
                if model.yearly_subscription_price is not None:
                    subscription_parts.append(
                        f"Yearly: {model.yearly_subscription_price} {price_per_kwh.currency}"
                    )
                subscription_desc = ", ".join(subscription_parts) if subscription_parts else "Free"

                logger.info(
                    "Created pricing model for %s - %s: %s %s/kWh, Subscription: %s",
                    country,
                    pricing_model_name,
                    price_per_kwh.amount,
                    price_per_kwh.currency,
                    subscription_desc,
                )
            except (IndexError, ValueError) as e:
                logger.error(
                    "Error processing pricing card %d for %s: %s", idx, country, e
                )
                continue

        logger.info(
            "Processing %d pricing model(s) for database operations", len(models)
        )
        for model in models:
            logger.debug(
                "Checking existing pricing for %s - %s",
                model.country,
                model.pricing_model_name,
            )
            stored_pricing = get_current_pricing(
                db, model.country, "Ionity", model.pricing_model_name
            )
            if stored_pricing:
                logger.debug(
                    "Found existing pricing record for %s in %s",
                    model.pricing_model_name,
                    model.country,
                )
                # Compare models excluding id, valid_from, and version
                model_data = model.model_dump(exclude={"id", "valid_from", "version"})
                stored_data = stored_pricing.model_dump(
                    exclude={"id", "valid_from", "version"}
                )
                if model_data != stored_data:
                    logger.info(
                        "Price change detected for %s in %s. Updating pricing...",
                        model.pricing_model_name,
                        model.country,
                    )
                    logger.debug("Old pricing: %s", stored_data)
                    logger.debug("New pricing: %s", model_data)
                    try:
                        update_pricing(db, new_data=model)
                        logger.info(
                            "Successfully updated pricing for %s in %s",
                            model.pricing_model_name,
                            model.country,
                        )
                    except (PyMongoError, ValueError) as e:
                        logger.error(
                            "Failed to update pricing for %s in %s: %s",
                            model.pricing_model_name,
                            model.country,
                            e,
                        )
                else:
                    logger.debug(
                        "No changes detected for %s in %s",
                        model.pricing_model_name,
                        model.country,
                    )
            else:
                logger.info(
                    "No existing pricing found for %s in %s. Inserting new record...",
                    model.pricing_model_name,
                    model.country,
                )
                try:
                    insert_pricing(db, model=model)
                    logger.info(
                        "Successfully inserted new pricing for %s in %s",
                        model.pricing_model_name,
                        model.country,
                    )
                except (PyMongoError, ValueError) as e:
                    logger.error(
                        "Failed to insert pricing for %s in %s: %s",
                        model.pricing_model_name,
                        model.country,
                        e,
                    )

        logger.info("Completed processing prices for %s", country)


def main():
    """
    Main entry point for the Ionity price scraper.

    Initializes the Chrome WebDriver, navigates to the Ionity subscriptions page,
    handles cookie consent, extracts available countries, and scrapes pricing
    information for all countries. Prices are stored in MongoDB with automatic
    version control.

    Raises:
        Exception: If WebDriver initialization fails or scraping process encounters
            an error. The exception is logged and re-raised.
    """
    logger.info("=" * 60)
    logger.info("Starting Ionity price scraper")
    logger.info("=" * 60)

    # Set up headless Chrome (or remove headless mode for debugging)
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    logger.info("Initializing Chrome WebDriver")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome WebDriver initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Chrome WebDriver: %s", e)
        raise

    try:
        url = "https://www.ionity.eu/subscriptions"
        logger.info("Navigating to: %s", url)
        driver.get(url)
        logger.info("Page loaded successfully")

        wait = WebDriverWait(driver, 15)
        logger.debug("WebDriverWait instance created with 15 second timeout")

        # --- Handle the cookie consent overlay if present ---
        logger.info("Waiting for cookie consent banner...")
        try:
            cookie_banner = wait.until(
                EC.presence_of_element_located((By.ID, "usercentrics-cmp-ui"))
            )
            logger.debug("Cookie consent banner found")
            try:
                shadow_root = driver.execute_script(
                    "return arguments[0].shadowRoot", cookie_banner
                )
                accept_button = shadow_root.find_element(By.ID, "save")
                logger.debug("Found accept button in shadow root")
                accept_button.click()
                logger.info("Clicked cookie consent accept button")
                wait.until(
                    EC.invisibility_of_element_located((By.ID, "usercentrics-cmp-ui"))
                )
                logger.info("Cookie consent banner dismissed")
            except (NoSuchElementException, TimeoutException) as e:
                logger.warning("Could not click the cookie consent button: %s", e)
        except TimeoutException:
            logger.debug("Cookie consent banner not found or already dismissed")

        # Get the list of countries from the dropdown
        logger.info("Extracting list of available countries from dropdown...")
        try:
            country_dropdown = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".combi-pricing_dropdown-toggle")
                )
            )
            logger.debug("Country dropdown found")
            country_dropdown.click()
            logger.debug("Clicked country dropdown")

            country_options = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".combi-pricing_select-dropdown-link")
                )
            )
            country_names = [option.text for option in country_options if option.text]
            logger.info(
                "Found %d countries: %s", len(country_names), ", ".join(country_names)
            )
        except TimeoutException as e:
            logger.error("Timeout while extracting country list: %s", e)
            raise
        except Exception as e:
            logger.error("Error extracting country list: %s", e)
            raise

        # Query prices for each country
        logger.info("Starting to scrape prices for all countries...")
        get_passport_prices_for_country(country_names, driver, wait)
        logger.info("=" * 60)
        logger.info("Scraping completed successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error("Error during scraping process: %s", e, exc_info=True)
        raise
    finally:
        logger.info("Closing WebDriver...")
        driver.quit()
        logger.info("WebDriver closed")


if __name__ == "__main__":
    main()
