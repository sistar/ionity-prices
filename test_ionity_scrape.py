# pylint: disable=missing-module-docstring
import time
import logging
import os
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# pylint: disable=redefined-outer-name

from dotenv import load_dotenv


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """
    Load environment variables from .env file.
    """
    load_dotenv()

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        logger.error("MONGODB_URI environment variable is not set")
        raise ValueError("MONGODB_URI environment variable is required")


@pytest.fixture(scope="module")
def driver_and_wait():
    """
    Initializes a headless Chrome WebDriver and WebDriverWait instance, navigates to the Ionity passport page,
    and handles the cookie consent overlay if present.

    Yields:
        tuple: A tuple containing the WebDriver instance and WebDriverWait instance.

    Raises:
        NoSuchElementException: If the cookie consent button is not found.
        TimeoutException: If the cookie consent overlay does not disappear within the wait time.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 15)

    # Handle the cookie consent overlay if present
    driver.get("https://www.ionity.eu/subscriptions")

    # More robust cookie handling with multiple attempts
    for attempt in range(3):
        try:
            cookie_banner = wait.until(
                EC.presence_of_element_located((By.ID, "usercentrics-cmp-ui"))
            )

            # Use JavaScript to click the accept button
            driver.execute_script("""
                const banner = document.getElementById('usercentrics-cmp-ui');
                if (banner && banner.shadowRoot) {
                    const saveBtn = banner.shadowRoot.getElementById('save');
                    if (saveBtn) {
                        saveBtn.click();
                        return true;
                    }
                }
                return false;
            """)

            # Wait for cookie banner to disappear with longer timeout
            wait = WebDriverWait(driver, 10)
            wait.until(
                EC.invisibility_of_element_located((By.ID, "usercentrics-cmp-ui"))
            )
            break

        except (NoSuchElementException, TimeoutException):
            if attempt == 2:
                # Final attempt - just wait and hope for the best
                time.sleep(3)
            else:
                time.sleep(1)

    # Final safety wait
    time.sleep(2)

    yield driver, wait
    driver.quit()


def test_country_options_not_empty(driver_and_wait):
    """
    Test that the country options dropdown on the Ionity Passport page is not empty.

    Args:
        driver_and_wait (tuple): A tuple containing the WebDriver instance and WebDriverWait instance.

    Raises:
        AssertionError: If the country options dropdown is empty or any country option is empty.

    Steps:
        1. Navigate to the Ionity Passport page.
        2. Locate and click the country dropdown.
        3. Wait for all country options to be present.
        4. Assert that the country options list is not empty.
        5. Assert that each country option has non-empty text.
        6. Print the text of each country option.
    """
    driver, wait = driver_and_wait

    # Aggressive approach to handle cookie banner
    driver.execute_script("""
        // Hide any remaining cookie banners
        const banner = document.getElementById('usercentrics-cmp-ui');
        if (banner) {
            banner.style.display = 'none';
            banner.remove();
        }
    """)

    country_dropdown = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".combi-pricing_dropdown-toggle"))
    )
    country_dropdown.click()
    country_options = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".combi-pricing_select-dropdown-link")
        )
    )
    assert len(country_options) > 0, "Country options should not be empty"
    for option in country_options:
        assert option.text.strip(), "Country option should not be empty"
        print(option.text)


def test_country_option_slovakia(driver_and_wait):
    """
    Test to verify that Slovakia is present in the country options on the Ionity Passport page.

    Args:
        driver_and_wait (tuple): A tuple containing the WebDriver instance and WebDriverWait instance.

    Raises:
        AssertionError: If Slovakia is not found in the country options.
    """
    driver, wait = driver_and_wait

    # Aggressive approach to handle cookie banner
    driver.execute_script("""
        // Hide any remaining cookie banners
        const banner = document.getElementById('usercentrics-cmp-ui');
        if (banner) {
            banner.style.display = 'none';
            banner.remove();
        }
    """)

    country_dropdown = wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".combi-pricing_dropdown-toggle")
        )
    )

    # Check if dropdown is already open
    is_open = country_dropdown.get_attribute("aria-expanded") == "true"
    if not is_open:
        # Use JavaScript click to avoid interception
        driver.execute_script("arguments[0].click();", country_dropdown)

    country_options = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".combi-pricing_select-dropdown-link")
        )
    )

    # Check if Slovakia is in the country options
    slovakia_present = any(option.text == "Slovakia" for option in country_options)
    assert slovakia_present, "Slovakia should be present in the country options"
