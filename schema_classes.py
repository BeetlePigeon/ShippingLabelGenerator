from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field


class ServiceType(StrEnum):
    # Service types listed are from fastest to slowest
    FIRST_OVERNIGHT = "FIRST_OVERNIGHT" # 1 business day    # EXPRESS
    PRIORITY_OVERNIGHT = "PRIORITY_OVERNIGHT"  # 1 business day
    STANDARD_OVERNIGHT = "STANDARD_OVERNIGHT"   # 1 business day
    FEDEX_2_DAY_AM = "FEDEX_2_DAY_AM"   # 2 business days
    FEDEX_2_DAY = "FEDEX_2_DAY"  # 2 business days
    FEDEX_EXPRESS_SAVER = "FEDEX_EXPRESS_SAVER"  # 3 business days
    FEDEX_GROUND = "FEDEX_GROUND"  # Use for commercial delivery address    #
    GROUND_HOME_DELIVERY = "GROUND_HOME_DELIVERY"  # Use for residential delivery address


class RatesOption(BaseModel):
    service_type: ServiceType
    estimated_delivery_time: datetime
    estimated_delivery_cost: float


class RatesOptions(BaseModel):
    options: list[RatesOption]

    @property
    def fastest(self) -> RatesOption:
        return min(self.options, key=lambda option: option.estimated_delivery_time)

    @property
    def cheapest(self) -> RatesOption:
        return min(self.options, key=lambda option: option.estimated_delivery_cost)


class Address(BaseModel):
    street_line_one: str
    street_line_two: str
    city: str
    state_code: str
    postal_code: str
    country_code: str = "US"


class InputData(BaseModel):
    street_line_one: str
    street_line_two: str | None = None
    city: str
    state_code: str
    postal_code: str
    country_code: str = "US"
    name: str
    email_address: str
    phone_number: str
    address_is_commercial: bool
    reference: str
    shipment_weight: float
    other_emails_to_notify: list[str] = Field(default_factory=list)


class RequestPortalData(BaseModel):
    request_for: str
    request_by: str
    comments: str | None
    new_hire_name: str | None
    new_hire_date: str | None
    facility: str | None
    office: str | None
    address: str | None
    phone_number: str | None
    cell_phone: str | None
    needed_by_date: str | None
    instructions: str | None
    others_to_notify: str | None


class Shipment(BaseModel):
    company_name: str
    charge_code: str
    account_number: str

    shipper_address: Address
    shipper_name: str
    shipper_email_address: str
    shipper_phone_number: str
    shipper_address_is_residential: bool

    recipient_address: Address | None
    recipient_name: str
    recipient_email_address: str
    recipient_phone_number: str
    recipient_address_is_residential: bool

    other_emails_to_notify: list[str] = Field(default_factory=list)
    shipment_weight: float
    case_number: str
    asset_number: str
    selected_service_type: ServiceType | None = None

    @property
    def shipper_street_lines(self) -> list[str]:
        lines = [self.shipper_address.street_line_one, self.shipper_address.street_line_two]
        return [line for line in lines if line is not None]

    @property
    def recipient_street_lines(self) -> list[str]:
        lines = [self.recipient_address.street_line_one, self.recipient_address.street_line_two]
        return [line for line in lines if line is not None]

    @property
    def reference_number(self) -> str:
        if self.case_number and self.asset_number:
            return f"{self.case_number}_{self.asset_number}"
        elif self.case_number:
            return f"{self.case_number}"
        elif self.asset_number:
            return f"Asset_{self.asset_number}"
        else:
            return ""