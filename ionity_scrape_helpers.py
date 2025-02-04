# pylint: disable=missing-module-docstring
import re


def extract_amount_currency(text):
    """Extracts the amount and currency from a string."""
    # if string ends in /kWh, remove it
    is_kwh_suffix = text.endswith("/kWh")
    if is_kwh_suffix:
        text = text[:-4]
    match = re.search(r"([^\d\s]{1,3})?\s*(\d+\.\d+)\s*([^\d\s]{1,3})?", text)
    if match:
        prefix_currency = match.group(1)
        amount = float(match.group(2))
        postfix_currency = match.group(3)
        currency = prefix_currency if prefix_currency else postfix_currency
        if prefix_currency:
            print(f"Amount: {currency}{amount}")
        else:
            print(f"Amount: {amount} {currency}")
        return amount, currency, is_kwh_suffix
    else:
        print(f"No match found. {text}")
    raise ValueError("Could not extract amount and currency")


def extract_subscription_price(text):
    """Extracts the subscription price from a string."""

    if "without any monthly fees." in text:
        return None, None

    match = re.search(
        r"plus ([^\d\s]{1,3})?\s*(\d+\.\d+)\s*([^\d\s]{1,3})? for the first month; then ([^\d\s]{1,3})?\s*(\d+\.\d+)\s*([^\d\s]{1,3})? per month.\*",
        text,
    )
    if match:
        prefix_currency = match.group(1)
        initial_price = float(match.group(2))

        postfix_currency = match.group(3)
        prefix_currency_monthly = match.group(4)
        monthly_price = float(match.group(5))

        currency = prefix_currency if prefix_currency else postfix_currency
        if prefix_currency:
            print(f"Initial price: {currency}{initial_price}")
        else:
            print(f"Initial price: {initial_price} {currency}")
        if prefix_currency_monthly:
            print(f"Monthly price: {currency}{monthly_price}")
        else:
            print(f"Monthly price: {monthly_price} {currency}")
        return float(monthly_price), currency
    else:
        print(f"No match found. {text}")
    raise ValueError("Could not extract subscription price")
