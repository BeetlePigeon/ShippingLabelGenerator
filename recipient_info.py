import re
from schema_classes import Address, ShippingContact


def parse_state(state_string: str) -> str:
    return state_string


def build_address(input_data) -> Address:
    return Address(
        street_line_one=input_data.address_line_one,
        street_line_two=input_data.address_line_two,
        city=input_data.city,
        state_code=parse_state(input_data.state),
        postal_code=input_data.zip_code,
        is_residential=input_data.is_residential_address,
    )


def parse_phone_number(input_data) -> str:
    return re.sub(r'\D', '', input_data.phone_number)


def get_recipient_info_from_input(input_data):
    recipient = ShippingContact(
        address=build_address(input_data),
        full_name=input_data.name,
        email_address=input_data.email_address,
        provided_phone_number=parse_phone_number(input_data),
    )

    return recipient