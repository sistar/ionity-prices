# pylint: disable=missing-module-docstring
from datetime import datetime, UTC
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from uri import URI

client = MongoClient(URI, server_api=ServerApi("1"))
db = client.get_database("charging_providers")


def insert_pricing(model):
    """
    Inserts a pricing model into the MongoDB pricing collection.

    Args:
        model (dict): A dictionary containing the pricing model details with the following keys:
            - country (str): The country for which the pricing model is applicable.
            - currency (str): The currency used in the pricing model.
            - provider (str): The provider of the pricing model.
            - pricing_model_name (str): The name of the pricing model.
            - price_kWh (float): The price per kWh.
            - subscription_price (float): The subscription price.

    Returns:
        None
    """
    coll = db.pricing
    coll.insert_one(
        {
            "country": model["country"],
            "currency": model["currency"],
            "provider": model["provider"],
            "pricing_model_name": model["pricing_model_name"],
            "valid_from": datetime.now(UTC),
            "valid_to": None,
            "price_kWh": model["price_kWh"],
            "subscription_price": model["subscription_price"],
            "version": 1,
        }
    )


def get_current_pricing(country, provider, pricing_model):
    """
    Retrieve the current pricing information for a given country, provider, and price model.

    Args:
        country (str): The name of the country for which to retrieve pricing information.
        provider (str): The name of the provider for which to retrieve pricing information.
        pricing_model (str): The name of the price model for which to retrieve pricing information.

    Returns:
        dict or None: A dictionary containing the pricing information if found, otherwise None.
    """
    coll = db.pricing
    return coll.find_one(
        {
            "country": country,
            "provider": provider,
            "pricing_model_name": pricing_model,
            "valid_to": None,
        }
    )


def update_pricing(country, provider, pricing_model, subscription_price, new_price):
    """
    Updates the pricing information for a given country, provider, and price model.

    This function archives the current active pricing version and inserts a new version
    with the updated pricing information. If the new price is the same as the current price,
    the function will print a message and return without making any changes.

    Args:
        country (str): The country for which the pricing is being updated.
        provider (str): The provider for which the pricing is being updated.
        pricing_model (str): The price model name.
        subscription_price (float): The subscription price to be updated.
        new_price (float): The new price per kWh to be updated.

    Returns:
        None
    """
    coll = db.pricing
    # Archive current active version

    if not (current_price := get_current_pricing(country, provider, pricing_model)):
        print("No active price found for this provider and price model.")
        return
    if (
        current_price["price_kWh"] == new_price
        and current_price["subscription_price"] == subscription_price
    ):
        print("New price is the same as the current price.")
        return
    coll.update_one(
        {
            "country": country,
            "provider": provider,
            "pricing_model_name": pricing_model,
            "valid_to": None,
        },
        {"$set": {"valid_to": datetime.now(UTC)}},
    )
    # Insert new version
    coll.insert_one(
        {
            "country": country,
            "provider": provider,
            "pricing_model_name": pricing_model,
            "valid_from": datetime.now(UTC),
            "valid_to": None,
            "price_kWh": new_price,
            "subscription_price": subscription_price,
            "version": current_price["version"] + 1,
        }
    )
