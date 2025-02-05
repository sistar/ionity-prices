# pylint: disable=missing-module-docstring
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pydantic import BaseModel, Field, field_validator, model_validator
from uri import URI


# Pydantic model definition
class PricingModel(BaseModel):
    """
    PricingModel represents the pricing details for a specific country and provider.

    Attributes:
        country (str): The country where the pricing model is applicable. Must be at least 2 characters long.
        currency (str): The currency used for pricing. Must be exactly 3 characters long.
        provider (str): The name of the provider offering the pricing model.
        pricing_model_name (str): The name of the pricing model.
        price_kWh (float): The price per kilowatt-hour. Must be greater than 0.
        subscription_price (float): The subscription price. Must be greater than or equal to 0.
        version (int): The version of the pricing model. Must be greater than or equal to 1.
        id (Optional[str]): The unique identifier for the pricing model, aliased as "_id".

    Methods:
        check_currency_country_relationship(): Validates that the currency is appropriate for the specified country.
    """

    country: str = Field(..., min_length=2)
    currency: str = Field(..., min_length=1, max_length=3)
    provider: str
    pricing_model_name: str
    price_kWh: float = Field(..., gt=0)
    subscription_price: float = Field(..., ge=0)
    initial_subscription_price: float = Field(..., ge=0)
    version: int = Field(..., ge=1)
    id: Optional[str] = Field(None, alias="_id")
    valid_to: Optional[datetime]
    valid_from: Optional[datetime]

    @field_validator("id", mode="before")
    def convert_objectid_to_str(cls, value):  # pylint: disable=no-self-argument
        """
        Convert a MongoDB ObjectId to a string.

        Args:
            value: The value to be checked and potentially converted.

        Returns:
            str: The string representation of the ObjectId if the value is an ObjectId.
            Otherwise, returns the value unchanged.
        """
        # If the "_id" is a MongoDB ObjectId, convert it to a string
        if isinstance(value, ObjectId):
            return str(value)
        return value

    @model_validator(mode="after")
    def check_currency_country_relationship(self):
        """
        Checks if the currency is valid for the given country.

        This method verifies if the currency specified in the instance is appropriate
        for the country specified in the instance. It uses a predefined mapping of
        currencies to countries to perform this validation.

        Raises:
            ValueError: If the currency is not valid for the specified country.

        Returns:
            self: The instance itself if the currency-country relationship is valid.
        """
        currency_country_map = {
            "€": [
                "Germany",
                "France",
                "Italy",
                "Austria",
                "Spain",
                "Portugal",
                "Netherlands",
                "Belgium",
                "Luxembourg",
                "Ireland",
                "Finland",
                "Slovakia",
                "Hungary",
                "Greece",
                "Croatia",
                "Slovenia",
                "Estonia",
                "Latvia",
                "Lithuania",
                "Malta",
                "Cyprus",
                "TestCountry",
            ],
            "CHF": ["Switzerland"],
            "DKR": ["Denmark"],
            "NOK": ["Norway"],
            "SEK": ["Sweden"],
            "PLN": ["Poland"],
            "USD": ["United States", "Canada"],
            "£": ["United Kingdom"],
            "CZK": ["Czech Republic"],
            "HUF": ["Hungary"],
            "RON": ["Romania"],
            "BGN": ["Bulgaria"],
            "HRK": ["Croatia"],
            "ISK": ["Iceland"],
        }
        if self.country not in currency_country_map.get(self.currency, [self.country]):
            raise ValueError(f"Currency {self.currency} not valid for {self.country}")
        return self


# Database connection
client = MongoClient(URI, server_api=ServerApi("1"))
db = client.get_database("charging_providers")


def insert_pricing(model: PricingModel):
    """
    Inserts a validated pricing model into MongoDB with automatic versioning
    """
    coll = db.pricing
    document = model.model_dump() | {
        "valid_from": datetime.now(ZoneInfo("UTC")),
        "valid_to": None,
        "version": 1,
    }
    coll.insert_one(document)


def get_current_pricing(
    country: str, provider: str, pricing_model: str
) -> PricingModel | None:
    """
    Returns validated PricingModel or None if not found
    """
    coll = db.pricing
    result = coll.find_one(
        {
            "country": country,
            "provider": provider,
            "pricing_model_name": pricing_model,
            "valid_to": None,
        }
    )
    return PricingModel(**result) if result else None


def get_pricing_history(
    country: str, provider: str, pricing_model: str
) -> list[PricingModel]:
    """
    Returns a list of all versions of the pricing model
    """
    coll = db.pricing
    result = coll.find(
        {
            "country": country,
            "provider": provider,
            "pricing_model_name": pricing_model,
        }
    )
    return [PricingModel(**doc) for doc in result]


def update_pricing(new_data: PricingModel):
    """
    Updates pricing with automatic version control and validation
    """
    coll = db.pricing
    current = get_current_pricing(
        new_data.country, new_data.provider, new_data.pricing_model_name
    )

    if not current:
        print("No active price found")
        return

    if current.model_dump(
        exclude={"id", "valid_from", "version"}
    ) == new_data.model_dump(exclude={"id", "valid_from", "version"}):
        print("No changes detected")
        return

    # Archive current version
    archive_timestamp = datetime.now(ZoneInfo("UTC"))
    # Floor to the hour
    archive_timestamp = archive_timestamp.replace(minute=0, second=0, microsecond=0)

    update_result = coll.update_one(
        {"_id": ObjectId(current.id)}, {"$set": {"valid_to": archive_timestamp}}
    )
    if not update_result.modified_count:
        raise ValueError("Failed to archive current version")

    # Insert new version
    new_doc = new_data.model_dump() | {
        "valid_from": archive_timestamp,
        "valid_to": None,
        "version": current.version + 1,
    }
    coll.insert_one(new_doc)
