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
        monthly_additional_price (Optional[Money]): The monthly subscription price, or None if not offered.
        yearly_additional_price (Optional[Money]): The yearly subscription price, or None if not offered.
    """

    monthly_additional_price: Optional[Money] = None
    yearly_additional_price: Optional[Money] = None


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
    Extracts subscription price and its currency from the given text,
    returning a SubscriptionTerms object with the appropriate period field populated.

    Args:
        amount_text (str): The price amount text (e.g., "€11.99", "47,200 HUF")
        period_text (str): The period text ("per year" or "per month")

    Returns:
        SubscriptionTerms: Object with monthly_additional_price or yearly_additional_price populated

    Raises:
        ValueError: If amount_text cannot be parsed or period_text is invalid

    regex tests https://regex101.com/r/mSS5r0/1
    """

    match = re.search(
        r"([^\d\s]{1,3})?\s*(\d*,?\d+\.?\d+)\s*([^\d\s]{1,3})?", amount_text
    )
    if not match:
        raise ValueError(f"Could not extract subscription price from: {amount_text}")

    prefix_currency = match.group(1)
    postfix_currency = match.group(3)
    currency = prefix_currency if prefix_currency else postfix_currency

    amount = float(match.group(2).replace(",", ""))

    # Determine which field to populate based on period_text
    period_lower = period_text.lower().strip()
    if period_lower == "per year":
        return SubscriptionTerms(
            yearly_additional_price=Money(amount=amount, currency=currency),
            monthly_additional_price=None
        )
    elif period_lower == "per month":
        return SubscriptionTerms(
            monthly_additional_price=Money(amount=amount, currency=currency),
            yearly_additional_price=None
        )
    else:
        raise ValueError(f"Invalid period_text: '{period_text}'. Expected 'per year' or 'per month'")
