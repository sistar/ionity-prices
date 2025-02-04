# pylint: disable=missing-module-docstring
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# pylint: disable=redefined-outer-name


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
    driver.get("https://www.ionity.eu/passport")
    cookie_banner = wait.until(
        EC.presence_of_element_located((By.ID, "usercentrics-cmp-ui"))
    )
    try:
        shadow_root = driver.execute_script(
            "return arguments[0].shadowRoot", cookie_banner
        )
        accept_button = shadow_root.find_element(By.ID, "save")
        accept_button.click()
        wait.until(EC.invisibility_of_element_located((By.ID, "usercentrics-cmp-ui")))
    except (NoSuchElementException, TimeoutException) as e:
        print(f"Could not click the cookie consent button... {e}")

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
    driver.get("https://www.ionity.eu/passport")

    country_dropdown = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pricing_dropdown-toggle"))
    )
    country_dropdown.click()
    country_options = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".pricing_select-dropdown-link")
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
    driver.get("https://www.ionity.eu/passport")

    country_dropdown = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".pricing_dropdown-toggle"))
    )
    country_dropdown.click()
    country_options = wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".pricing_select-dropdown-link")
        )
    )

    # Check if Slovakia is in the country options
    slovakia_present = any(option.text == "Slovakia" for option in country_options)
    assert slovakia_present, "Slovakia should be present in the country options"
