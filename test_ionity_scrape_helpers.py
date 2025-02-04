# pylint: disable=missing-module-docstring
import pytest
from ionity_scrape_helpers import extract_subscription_price, extract_amount_currency


def test_extract_eur_subscription_price():  # pylint: disable=missing-function-docstring
    price, currency = extract_subscription_price(
        "plus €7.99 for the first month; then €11.99 per month.*"
    )
    assert (
        price == 11.99
    ), "Subscription price should be 11.99 - ignore the first month price"
    assert currency == "€", "Currency should be €"


def test_extract_gbp_subscription_price():  # pylint: disable=missing-function-docstring
    price, currency = extract_subscription_price(
        "plus £7.99 for the first month; then £11.99 per month.*"
    )
    assert (
        price == 11.99
    ), "Subscription price should be 11.99 - ignore the first month price"
    assert currency == "£", "Currency should be £"


def test_extract_chf_subscription_price():  # pylint: disable=missing-function-docstring
    price, currency = extract_subscription_price(
        "plus 3.99 CHF for the first month; then 5.99 CHF per month.*"
    )
    assert (
        price == 5.99
    ), "Subscription price should be 5.99 - ignore the first month price"
    assert currency == "CHF", "Currency should be CHF"


def test_extract_no_subscription_price():  # pylint: disable=missing-function-docstring
    price, currency = extract_subscription_price(
        "Charge on-site and pay contactless without any monthly fees."
    )
    assert price is None, "Price should be None"
    assert currency is None, "Currency should be None"


def test_extract_subscription_price_no_match():  # pylint: disable=missing-function-docstring
    with pytest.raises(ValueError):
        extract_subscription_price("No match here.")


def test_extract_amount_currency_postfix():  # pylint: disable=missing-function-docstring
    amount, currency, _ = extract_amount_currency("7.99 SFR")
    assert amount == 7.99, "Amount should be 7.99"
    assert currency == "SFR", "Currency should be SFR"


def test_extract_amount_currency():  # pylint: disable=missing-function-docstring
    amount, currency, _ = extract_amount_currency("€7.99")
    assert amount == 7.99, "Amount should be 7.99"
    assert currency == "€", "Currency should be €"


def test_extract_amount_currency_price_per_kwh():  # pylint: disable=missing-function-docstring
    amount, currency, _ = extract_amount_currency("0.39 €/kWh")
    assert amount == 0.39, "Amount should be 0.39"
    assert currency == "€", "Currency should be €"


if __name__ == "__main__":

    pytest.main()
