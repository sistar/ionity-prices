# pylint: disable=missing-module-docstring
import pytest
from ionity_scrape_helpers import (
    extract_subscription_price,
    extract_amount_currency,
    Money,
    SubscriptionTerms,
)


def test_extract_eur_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("€11.99", "per year")
    assert terms is not None, "Terms should not be None"
    assert (
        terms.yearly_additional_price.amount == 11.99
    ), "Subscription price should be 11.99"
    assert terms.yearly_additional_price.currency == "€", "Currency should be €"


def test_extract_gbp_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("£11.99", "per year")
    assert terms is not None, "Terms should not be None"
    assert (
        terms.yearly_additional_price.amount == 11.99
    ), "Subscription price should be 11.99"
    assert terms.yearly_additional_price.currency == "£", "Currency should be £"


def test_extract_chf_subscription_price():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("5.99 CHF", "per year")
    assert terms is not None, "Terms should not be None"
    assert (
        terms.yearly_additional_price.amount == 5.99
    ), "Subscription price should be 5.99"
    assert terms.yearly_additional_price.currency == "CHF", "Currency should be CHF"


def test_extract_huf_subscription_price_with_comma():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("47,200 HUF", "per year")
    assert terms is not None, "Terms should not be None"
    assert (
        terms.yearly_additional_price.amount == 47200.0
    ), "Subscription price should be 47200.0"
    assert terms.yearly_additional_price.currency == "HUF", "Currency should be HUF"


def test_extract_no_subscription_price():  # pylint: disable=missing-function-docstring
    # Test with text that has no price pattern
    with pytest.raises(ValueError):
        extract_subscription_price("without any fees", "per year")


def test_extract_subscription_price_no_match():  # pylint: disable=missing-function-docstring
    with pytest.raises(ValueError):
        extract_subscription_price("No match here", "period text")


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
