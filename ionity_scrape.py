# pylint: disable=missing-module-docstring
import datetime
from datetime import datetime
from zoneinfo import ZoneInfo
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from ionity_scrape_helpers import extract_amount_currency, extract_subscription_price
from mongo_db_pricing import (
    PricingModel,
    get_current_pricing,
    insert_pricing,
    update_pricing,
)
from uri import URI

# Create a new client and connect to the server
client = MongoClient(URI, server_api=ServerApi("1"))
db = client.get_database("charging_providers")


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

    archive_timestamp = datetime.now(ZoneInfo("UTC"))
    # Floor to the hour
    archive_timestamp = archive_timestamp.replace(minute=0, second=0, microsecond=0)

    for country in country_names:
        print(f"Getting passport prices for {country}...")

        # Wait for dropdown toggle to be interactive
        toggle = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".pricing_dropdown-toggle"))
        )

        # Check current visibility state of dropdown options
        options_locator = (By.CSS_SELECTOR, ".pricing_select-dropdown-link")
        existing_options = driver.find_elements(*options_locator)
        dropdown_visible = (
            any(opt.is_displayed() for opt in existing_options)
            if existing_options
            else False
        )

        # Only activate toggle if dropdown isn't visible
        if not dropdown_visible:
            toggle.click()
            wait.until(EC.visibility_of_element_located(options_locator))

        # Proceed with option selection
        options = driver.find_elements(*options_locator)
        target_option = None
        for option in options:
            if option.text.strip() == country:
                target_option = option
                break

        if not target_option:
            print(f"Could not find an option for {country}")
            continue

        # Click the target option
        target_option.click()

        # Wait for the prices to load and print them
        time.sleep(1)  # Adjust sleep time if necessary
        pricing_cards = driver.find_elements(By.CSS_SELECTOR, ".pricing_card-top")
        models = []
        for pricing_card in pricing_cards:
            l = pricing_card.text.split("\n")
            pricing_model_name = l[0]
            price_per_kwh = extract_amount_currency(l[1])
            subscription_text = l[2]
            print(f"{l[0]} - {l[1]} \n {l[2]}")
            subscription_terms = extract_subscription_price(subscription_text)
            models.append(
                PricingModel(
                    country=country,
                    currency=price_per_kwh.currency,
                    provider="Ionity",
                    pricing_model_name=pricing_model_name,
                    price_kWh=price_per_kwh.amount,
                    subscription_price=(
                        subscription_terms.monthly_price.amount
                        if subscription_terms
                        else 0.0
                    ),
                    initial_subscription_price=(
                        subscription_terms.initial_price.amount
                        if subscription_terms
                        else 0.0
                    ),
                    version=1,
                    _id=None,
                    valid_from=archive_timestamp,
                    valid_to=None,
                )
            )

        for model in models:
            stored_pricing = get_current_pricing(
                model.country, "Ionity", model.pricing_model_name
            )
            if stored_pricing:
                if model.model_dump(
                    exclude={"id", "valid_from", "version"}
                ) != stored_pricing.model_dump(exclude={"id", "valid_from", "version"}):
                    update_pricing(model)
            else:
                insert_pricing(model)


def main():
    # Set up headless Chrome (or remove headless mode for debugging)
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    try:
        url = "https://www.ionity.eu/passport"
        driver.get(url)

        wait = WebDriverWait(driver, 15)

        # --- Handle the cookie consent overlay if present ---
        cookie_banner = wait.until(
            EC.presence_of_element_located((By.ID, "usercentrics-cmp-ui"))
        )
        try:
            shadow_root = driver.execute_script(
                "return arguments[0].shadowRoot", cookie_banner
            )
            accept_button = shadow_root.find_element(By.ID, "save")
            accept_button.click()
            wait.until(
                EC.invisibility_of_element_located((By.ID, "usercentrics-cmp-ui"))
            )
        except (NoSuchElementException, TimeoutException) as e:
            print(f"Could not click the cookie consent button {e}")

        # Get the list of countries from the dropdown
        country_dropdown = wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".pricing_dropdown-toggle")
            )
        )
        country_dropdown.click()
        country_options = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, ".pricing_select-dropdown-link")
            )
        )
        country_names = [option.text for option in country_options if option.text]

        # Query prices for each country
        get_passport_prices_for_country(country_names, driver, wait)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
