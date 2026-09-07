from pydantic import BaseModel


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
    phone_number: str
