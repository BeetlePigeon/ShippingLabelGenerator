from enum import StrEnum
from pydantic import BaseModel, Field
from private import default_phone_number


class ServiceType(StrEnum):
    PRIORITY_OVERNIGHT = "PRIORITY_OVERNIGHT"  # 1 business day
    FEDEX_2_DAY = "FEDEX_2_DAY"  # 2 business days
    FEDEX_EXPRESS_SAVER = "FEDEX_EXPRESS_SAVER"  # 3 business days

    # Regular
    FEDEX_GROUND_COMMERCIAL = "FEDEX_GROUND"  # Use for commercial address deliveries
    FEDEX_GROUND_HOME = "GROUND_HOME_DELIVERY"  # Use for residential address deliveries


class Address(BaseModel):
    street_line_one: str
    street_line_two: str | None = None
    city: str
    state_code: str
    postal_code: str
    country_code: str = "US"
    is_residential: bool

    @property
    def street_lines(self) -> list[str]:
        lines = [self.street_line_one, self.street_line_two]
        return [line for line in lines if line is not None]


class ShippingContact(BaseModel):
    address: Address
    full_name: str
    email_address: str
    provided_phone_number: str | None = None

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
    default_service_type: ServiceType = ServiceType.FEDEX_EXPRESS_SAVER
    selected_service_type: ServiceType | None = None
    charge_code: str
    shipment_weight: float = 10
    other_emails_to_notify: list[str] = Field(default_factory=list)

    @property
    def service_type(self) -> ServiceType:
        return self.selected_service_type or self.default_service_type


class InputData(BaseModel):
    address_line_one: str
    address_line_two: str | None = None
    city: str
    state: str
    zip_code: str
    name: str
    email_address: str | None = ""
    phone_number: str
    is_residential_address: bool
    shipment_weight: float = 10
    case_number: str | None = ""
    asset_number: str | None = ""
    other_emails_to_notify: list[str] = Field(default_factory=list)
    service_type: ServiceType | None = None