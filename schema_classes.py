from enum import StrEnum
from pydantic import BaseModel, Field
from private import default_phone_number


class ServiceType(StrEnum):
        FEDEX_OVERNIGHT = "PRIORITY_OVERNIGHT",  # 1 business day
        FEDEX_2_DAY = "FEDEX_2_DAY",  # 2 business days
        FEDEX_EXPRESS_SAVER = "FEDEX_EXPRESS_SAVER",  # 3 business days

        # Regular
        FEDEX_GROUND_COMMERCIAL = "FEDEX_GROUND",  # Use for commercial address deliveries
        FEDEX_GROUND_HOME = "GROUND_HOME_DELIVERY",  # Use for residential address deliveries


class ShippingContact(BaseModel):
    street_line_one: str
    street_line_two: str | None = None
    city: str
    state_code: str
    postal_code: str
    country_code: str
    is_residential: bool
    full_name: str
    email_address: str
    provided_phone_number: str | None = None

    @property
    def street_lines(self) -> list[str]:
        lines = [self.street_line_one, self.street_line_two]
        return [line for line in lines if line is not None]

    @property
    def phone_number(self) -> str:
        if not self.provided_phone_number:
            return default_phone_number
        return self.provided_phone_number


class Shipment(BaseModel):
    shipper: ShippingContact
    recipient: ShippingContact
    case_number: str | None = ""
    asset_number: str | None = ""
    service_type: ServiceType
    charge_code: str
    shipment_weight: float = 10
    other_emails_to_notify: list[str] = Field(default_factory=list)