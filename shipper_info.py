from schema_classes import ShippingContact
from private import (
    shipper_street_line_one,
    shipper_street_line_two,
    shipper_city,
    shipper_state_code,
    shipper_postal_code,
    shipper_country_code,
    shipper_is_residential,
    shipper_full_name,
    shipper_email_address,
    shipper_provided_phone_number,
)


default_shipper = ShippingContact(
    street_line_one = shipper_street_line_one,
    street_line_two = shipper_street_line_two,
    city = shipper_city,
    state_code= shipper_state_code,
    postal_code= shipper_postal_code,
    country_code = shipper_country_code,
    is_residential = shipper_is_residential,
    full_name = shipper_full_name,
    email_address = shipper_email_address,
    provided_phone_number = shipper_provided_phone_number,
)

def get_default_shipper_info():
    return default_shipper