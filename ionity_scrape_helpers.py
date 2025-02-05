# pylint: disable=missing-module-docstring
import re
from typing import Optional
from pydantic import BaseModel


class Money(BaseModel):
    """
    A class to represent money with an amount and currency.

    Attributes:
        amount (float): The monetary amount.
        currency (str): The currency of the money.
    """

    amount: float
    currency: str


class SubscriptionTerms(BaseModel):
    """
    A class to represent the terms of a subscription.

    Attributes:
        initial_price (Money): The initial price.
        monthly_price (Money): The monthly price.
    """

    initial_price: Money
    monthly_price: Money


def extract_amount_currency(text) -> Money:
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

        return Money(amount=amount, currency=currency)
    else:
        print(f"No match found. {text}")
    raise ValueError("Could not extract amount and currency")


def extract_subscription_price(text) -> Optional[SubscriptionTerms]:
    """
    Extracts the per month subscription price and its currency from the given text,
    returning a Money object or None if not found.
    """
    if "without any monthly fees." in text:
        return None

    match = re.search(
        r"plus ([^\d\s]{1,3})?\s*(\d+\.\d+)\s*([^\d\s]{1,3})? for the first month; then ([^\d\s]{1,3})?\s*(\d+\.\d+)\s*([^\d\s]{1,3})? per month.\*",
        text,
    )
    if match:
        prefix_currency = match.group(1)
        initial_price = float(match.group(2).replace(",", "."))

        postfix_currency = match.group(3)
        prefix_currency_monthly = match.group(4)
        monthly_price = float(match.group(5).replace(",", "."))

        currency = prefix_currency if prefix_currency else postfix_currency

        return SubscriptionTerms(
            initial_price=Money(amount=initial_price, currency=currency),
            monthly_price=Money(amount=monthly_price, currency=currency),
        )
    else:
        raise ValueError("Could not extract subscription price")
