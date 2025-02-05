# pylint: disable=missing-module-docstring
import pytest
from ionity_scrape_helpers import (
    extract_subscription_price,
    extract_amount_currency,
    Money,
    SubscriptionTerms,
)


def test_extract_eur_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price(
        "plus €7.99 for the first month; then €11.99 per month.*"
    )
    assert terms is not None, "Terms should not be None"
    assert (
        terms.initial_price.amount == 7.99
    ), "Subscription price should be 11.99 - ignore the first month price"
    assert terms.initial_price.currency == "€", "Currency should be €"
    assert terms is not None, "Terms should not be None"
    assert (
        terms.monthly_price.amount == 11.99
    ), "Subscription price should be 11.99 - ignore the first month price"
    assert terms.monthly_price.currency == "€", "Currency should be €"


def test_extract_gbp_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price(
        "plus £7.99 for the first month; then £11.99 per month.*"
    )
    assert terms is not None, "Terms should not be None"
    assert (
        terms.monthly_price.amount == 11.99
    ), "Subscription price should be 11.99 - ignore the first month price"
    assert terms.monthly_price.currency == "£", "Currency should be £"


def test_extract_chf_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price(
        "plus 3.99 CHF for the first month; then 5.99 CHF per month.*"
    )
    assert terms is not None, "Terms should not be None"
    assert (
        terms.monthly_price.amount == 5.99
    ), "Subscription price should be 5.99 - ignore the first month price"
    assert terms.monthly_price.currency == "CHF", "Currency should be CHF"


def test_extract_no_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price(
        "Charge on-site and pay contactless without any monthly fees."
    )
    assert terms is None, "Subscription Terms should be None"


def test_extract_subscription_price_no_match():  # pylint: disable=missing-function-docstring
    with pytest.raises(ValueError):
        extract_subscription_price("No match here.")


def test_extract_amount_currency_postfix():  # pylint: disable=missing-function-docstring
    money = extract_amount_currency("7.99 SFR")
    assert money is not None, "Money should not be None"
    assert money.amount == 7.99, "Amount should be 7.99"
    assert money.currency == "SFR", "Currency should be SFR"


def test_extract_amount_currency():  # pylint: disable=missing-function-docstring
    money = extract_amount_currency("€7.99")
    assert money is not None, "Money should not be None"
    assert money.amount == 7.99, "Amount should be 7.99"
    assert money.currency == "€", "Currency should be €"


def test_extract_amount_currency_price_per_kwh():  # pylint: disable=missing-function-docstring
    money = extract_amount_currency("0.39 €/kWh")
    assert money is not None, "Money should not be None"
    assert money.amount == 0.39, "Amount should be 0.39"
    assert money.currency == "€", "Currency should be €"


if __name__ == "__main__":

    pytest.main()
