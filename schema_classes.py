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


class RequestPortalData(BaseModel):
    request_for: str = ""
    request_by: str = ""
    comments: str = ""
    new_hire_name: str = ""
    new_hire_date: str = ""
    facility: str = ""
    office: str = ""
    address: str = ""
    phone_number: str = ""
    cell_phone: str = ""
    needed_by_date: str = ""
    instructions: str = ""
    others_to_notify: str = ""


class Address(BaseModel):
    street_line_one: str
    street_line_two: str
    city: str
    state_code: str
    postal_code: str
    country_code: str = "US"


    @property
    def street_lines(self) -> list[str]:
        lines = [self.street_line_one, self.street_line_two]
        return [line for line in lines if line is not None]


class Shipment(BaseModel):
    company_name: str
    charge_code: str
    account_number: str
    shipper_name: str
    shipper_email_address: str
    shipper_phone_number: str
    shipper_address: Address
    shipper_address_is_commercial: bool

    recipient_name: str
    recipient_email_address: str
    recipient_phone_number: str

    recipient_address: Address
    recipient_address_is_commercial: bool

    reference: str
    weight: str = "8"
    other_email_1: str
    other_email_2: str
    other_email_3: str

    selected_service_type: ServiceType | None = None


    @property
    def other_emails_to_notify(self) -> list[str]:
        emails = [
            self.other_email_1,
            self.other_email_2,
            self.other_email_3,
        ]
        return emails


    @property
    def shipper_address_is_residential(self) -> bool:
        return not self.shipper_address_is_commercial


    @property
    def recipient_address_is_residential(self) -> bool:
        return not self.recipient_address_is_commercial