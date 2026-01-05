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
        yearly_additional_price (Money): The yearly subscription price.
    """

    yearly_additional_price: Money


def extract_amount_currency(text) -> Money:
    """Extracts the amount and currency from a string."""
    # if string ends in /kWh, remove it
    is_kwh_suffix = text.endswith("/kWh")
    if is_kwh_suffix:
        text = text[:-4]
    match = re.search(r"([^\d\s]{1,3})?\s*(\d+\.?\d+)\s*([^\d\s]{1,3})?", text)
    if match:
        prefix_currency = match.group(1)
        postfix_currency = match.group(3)
        currency = prefix_currency if prefix_currency else postfix_currency

        amount = float(match.group(2).replace(",", ""))
        return Money(amount=amount, currency=currency)
    else:
        print(f"No match found. {text}")
    raise ValueError("Could not extract amount and currency")


def extract_subscription_price(amount_text, period_text) -> Optional[SubscriptionTerms]:
    """
    Extracts the per month subscription price and its currency from the given text,
    returning a Money object or None if not found.
    regex tests https://regex101.com/r/mSS5r0/1
    """

    match = re.search(
        r"([^\d\s]{1,3})?\s*(\d*,?\d+\.?\d+)\s*([^\d\s]{1,3})?", amount_text
    )
    if match:
        prefix_currency = match.group(1)
        postfix_currency = match.group(3)
        currency = prefix_currency if prefix_currency else postfix_currency

        amount = float(match.group(2).replace(",", ""))

        return SubscriptionTerms(
            yearly_additional_price=Money(amount=amount, currency=currency)
        )
    else:
        raise ValueError("Could not extract subscription price")
