# pylint: disable=missing-module-docstring
import pytest
from ionity_scrape_helpers import (
    extract_subscription_price,
    extract_amount_currency,
    Money,
    SubscriptionTerms,
)


def test_extract_eur_subscription_price_yearly():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("€11.99", "per year")
    assert terms is not None, "Terms should not be None"
    assert terms.yearly_additional_price is not None, "Yearly price should not be None"
    assert (
        terms.yearly_additional_price.amount == 11.99
    ), "Subscription price should be 11.99"
    assert terms.yearly_additional_price.currency == "€", "Currency should be €"
    assert terms.monthly_additional_price is None, "Monthly should be None for yearly subscription"


def test_extract_gbp_subscription_price_yearly():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("£11.99", "per year")
    assert terms is not None, "Terms should not be None"
    assert terms.yearly_additional_price is not None, "Yearly price should not be None"
    assert (
        terms.yearly_additional_price.amount == 11.99
    ), "Subscription price should be 11.99"
    assert terms.yearly_additional_price.currency == "£", "Currency should be £"
    assert terms.monthly_additional_price is None, "Monthly should be None for yearly subscription"


def test_extract_chf_subscription_price_yearly():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("5.99 CHF", "per year")
    assert terms is not None, "Terms should not be None"
    assert terms.yearly_additional_price is not None, "Yearly price should not be None"
    assert (
        terms.yearly_additional_price.amount == 5.99
    ), "Subscription price should be 5.99"
    assert terms.yearly_additional_price.currency == "CHF", "Currency should be CHF"
    assert terms.monthly_additional_price is None, "Monthly should be None for yearly subscription"


def test_extract_huf_subscription_price_yearly_with_comma():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("47,200 HUF", "per year")
    assert terms is not None, "Terms should not be None"
    assert terms.yearly_additional_price is not None, "Yearly price should not be None"
    assert (
        terms.yearly_additional_price.amount == 47200.0
    ), "Subscription price should be 47200.0"
    assert terms.yearly_additional_price.currency == "HUF", "Currency should be HUF"
    assert terms.monthly_additional_price is None, "Monthly should be None for yearly subscription"


def test_extract_no_subscription_price():  # pylint: disable=missing-function-docstring
    # Test with text that has no price pattern
    with pytest.raises(ValueError):
        extract_subscription_price("without any fees", "per year")


def test_extract_subscription_price_no_match():  # pylint: disable=missing-function-docstring
    with pytest.raises(ValueError):
        extract_subscription_price("No match here", "period text")


def test_extract_eur_subscription_price_monthly():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("€0.99", "per month")
    assert terms is not None, "Terms should not be None"
    assert terms.monthly_additional_price is not None, "Monthly price should not be None"
    assert (
        terms.monthly_additional_price.amount == 0.99
    ), "Subscription price should be 0.99"
    assert terms.monthly_additional_price.currency == "€", "Currency should be €"
    assert terms.yearly_additional_price is None, "Yearly should be None for monthly subscription"


def test_extract_gbp_subscription_price_monthly():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("£0.99", "per month")
    assert terms is not None, "Terms should not be None"
    assert terms.monthly_additional_price is not None, "Monthly price should not be None"
    assert (
        terms.monthly_additional_price.amount == 0.99
    ), "Subscription price should be 0.99"
    assert terms.monthly_additional_price.currency == "£", "Currency should be £"
    assert terms.yearly_additional_price is None, "Yearly should be None for monthly subscription"


def test_extract_chf_subscription_price_monthly():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("1.99 CHF", "per month")
    assert terms is not None, "Terms should not be None"
    assert terms.monthly_additional_price is not None, "Monthly price should not be None"
    assert (
        terms.monthly_additional_price.amount == 1.99
    ), "Subscription price should be 1.99"
    assert terms.monthly_additional_price.currency == "CHF", "Currency should be CHF"
    assert terms.yearly_additional_price is None, "Yearly should be None for monthly subscription"


def test_extract_huf_subscription_price_monthly_with_comma():  # pylint: disable=missing-function-docstring
    terms = extract_subscription_price("3,933 HUF", "per month")
    assert terms is not None, "Terms should not be None"
    assert terms.monthly_additional_price is not None, "Monthly price should not be None"
    assert (
        terms.monthly_additional_price.amount == 3933.0
    ), "Subscription price should be 3933.0"
    assert terms.monthly_additional_price.currency == "HUF", "Currency should be HUF"
    assert terms.yearly_additional_price is None, "Yearly should be None for monthly subscription"


def test_extract_subscription_price_invalid_period():  # pylint: disable=missing-function-docstring
    with pytest.raises(ValueError, match="Invalid period_text"):
        extract_subscription_price("€11.99", "per week")


def test_extract_subscription_price_case_insensitive():  # pylint: disable=missing-function-docstring
    # Test uppercase
    terms1 = extract_subscription_price("€11.99", "PER YEAR")
    assert terms1.yearly_additional_price is not None
    assert terms1.yearly_additional_price.amount == 11.99

    # Test mixed case
    terms2 = extract_subscription_price("€0.99", "Per Month")
    assert terms2.monthly_additional_price is not None
    assert terms2.monthly_additional_price.amount == 0.99


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


def test_extract_amount_currency_pence():  # pylint: disable=missing-function-docstring
    """Test that pence (p) is converted to pounds (£)."""
    money = extract_amount_currency("43p")
    assert money is not None, "Money should not be None"
    assert money.amount == 0.43, "Amount should be 0.43 (43 pence = £0.43)"
    assert money.currency == "£", "Currency should be £ (converted from p)"


def test_extract_amount_currency_pence_with_kwh():  # pylint: disable=missing-function-docstring
    """Test that pence with /kWh suffix is converted to pounds."""
    money = extract_amount_currency("43p/kWh")
    assert money is not None, "Money should not be None"
    assert money.amount == 0.43, "Amount should be 0.43 (43 pence = £0.43)"
    assert money.currency == "£", "Currency should be £ (converted from p)"


def test_extract_amount_currency_decimal_pence():  # pylint: disable=missing-function-docstring
    """Test that decimal pence values are converted correctly."""
    money = extract_amount_currency("42.5p")
    assert money is not None, "Money should not be None"
    assert money.amount == 0.425, "Amount should be 0.425 (42.5 pence = £0.425)"
    assert money.currency == "£", "Currency should be £ (converted from p)"


if __name__ == "__main__":

    pytest.main()
