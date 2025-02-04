# pylint: disable=missing-module-docstring
import pytest
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


# Import the functions to be tested
from mongo_db_pricing import insert_pricing, get_current_pricing, update_pricing
from uri import URI


@pytest.fixture(scope="module")
def db():
    """
    Connects to a MongoDB database and yields the database object.

    This function establishes a connection to a MongoDB database using the provided URI and server API version.
    It yields the database object for use in database operations. After the operations are complete, it closes the connection.

    Yields:
        pymongo.database.Database: The MongoDB database object.

    Example:
        with db() as database:
            # Perform database operations
            collection = database.get_collection("collection_name")
            collection.find_one({"key": "value"})
    """
    client = MongoClient(URI, server_api=ServerApi("1"))
    db_l = client.get_database("charging_providers")
    yield db_l
    client.close()


def test_insert_and_update_pricing(db_l):
    """
    Test the insertion and updating of pricing in the database.

    This test performs the following steps:
    1. Inserts a new pricing model into the database.
    2. Verifies that the pricing model was correctly inserted.
    3. Updates the pricing model with a new price per kWh.
    4. Verifies that the old pricing model was archived.
    5. Verifies that the new pricing model was correctly inserted.
    6. Cleans up the test data from the database.

    Args:
        db: The database connection object.

    Raises:
        AssertionError: If any of the assertions fail during the test.
    """
    country = "TestCountry"
    provider = "TestProvider"
    price_model_name = "TestModel"
    subscription_price = 10.0
    price_kWh = 0.30
    new_price_kWh = 0.35
    model = {
        "country": country,
        "provider": provider,
        "price_model_name": price_model_name,
        "price_kWh": price_kWh,
        "subscription_price": subscription_price,
    }
    # Insert a new pricing
    insert_pricing(model=model)

    # Verify the pricing was inserted
    current_pricing = get_current_pricing(country, provider, price_model_name)
    assert current_pricing is not None, "Pricing should be inserted"
    assert current_pricing["price_kWh"] == price_kWh, "Inserted price_kWh should match"
    assert (
        current_pricing["subscription_price"] == subscription_price
    ), "Inserted subscription_price should match"

    # Update the pricing
    update_pricing(
        country, provider, price_model_name, subscription_price, new_price_kWh
    )

    # Verify the old pricing was archived
    archived_pricing = db_l.pricing.find_one(
        {
            "country": country,
            "provider": provider,
            "price_model_name": price_model_name,
            "valid_to": {"$ne": None},
        }
    )
    assert archived_pricing is not None, "Old pricing should be archived"
    assert (
        archived_pricing["price_kWh"] == price_kWh
    ), "Archived price_kWh should match the old price"
    assert (
        archived_pricing["valid_to"] is not None
    ), "Archived pricing should have a valid_to date"

    # Verify the new pricing was inserted
    new_pricing = get_current_pricing(country, provider, price_model_name)
    assert new_pricing is not None, "New pricing should be inserted"
    assert (
        new_pricing["price_kWh"] == new_price_kWh
    ), "New price_kWh should match the updated price"
    assert (
        new_pricing["subscription_price"] == subscription_price
    ), "New subscription_price should match"
    assert (
        new_pricing["valid_to"] is None
    ), "New pricing should not have a valid_to date"

    # Clean up the test data
    db_l.pricing.delete_many(
        {"country": country, "provider": provider, "price_model_name": price_model_name}
    )


def test_updating_same_price(db_l):
    """
    Test that updating a pricing entry with the same values does not create a new version.

    This test performs the following steps:
    1. Inserts a new pricing entry into the database.
    2. Updates the pricing entry with the same values.
    3. Verifies that no new pricing entry was inserted and the version number remains the same.
    4. Cleans up the test data from the database.

    Args:
        db: The database connection object.

    Raises:
        AssertionError: If the pricing entry is not found or the version number is incremented.
    """
    country = "TestCountry"
    provider = "TestProvider"
    price_model_name = "TestModel"
    subscription_price = 10.0
    price_kWh = 0.30
    model = {
        "country": country,
        "provider": provider,
        "price_model_name": price_model_name,
        "price_kWh": price_kWh,
        "subscription_price": subscription_price,
    }
    # Insert a new pricing
    insert_pricing(model=model)
    # Update the pricing with the same values
    update_pricing(country, provider, price_model_name, subscription_price, price_kWh)
    # Verify that no new pricing was inserted
    new_pricing = get_current_pricing(country, provider, price_model_name)
    assert new_pricing is not None, "Pricing should still be inserted"
    assert new_pricing["version"] == 1, "Version should not be incremented"

    # Clean up the test data
    db_l.pricing.delete_many(
        {"country": country, "provider": provider, "price_model_name": price_model_name}
    )


if __name__ == "__main__":
    pytest.main()
