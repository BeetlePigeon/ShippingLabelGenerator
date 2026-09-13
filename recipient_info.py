import re
from tables import STATE_CODES
from private import company_email_domain
from schema_classes import Address, ShippingContact


def normalize_state_code(state_string: str) -> str:
    if len(state_string) == 2:
        return state_string
    return STATE_CODES[state_string.lower()]


def normalize_phone_number(phone_number) -> str:
    return re.sub(r'\D', '', phone_number)


def normalize_email_address(name, email_address):
    if email_address == "":
        # Only construct email address from name if name is exactly two words and doesn't contain special characters
        if not re.fullmatch(r"^[A-Za-z]+ [A-Za-z]+$", name):
            raise ValueError("Name cannot be converted to email address. Manually enter email address.")
        first_name, last_name = name.split(" ")
        constructed_email_address = f"{first_name}.{last_name}@{company_email_domain}"
        return constructed_email_address
    return email_address


def build_normalized_address(input_data) -> Address:
    return Address(
        street_line_one=input_data.address_line_one,
        street_line_two=input_data.address_line_two,
        city=input_data.city,
        state_code=normalize_state_code(input_data.state),
        postal_code=input_data.zip_code,
        is_residential=input_data.is_residential_address,
    )


def get_recipient_info_from_input(input_data):
    recipient = ShippingContact(
        address=build_normalized_address(input_data),
        full_name=input_data.name,
        email_address=normalize_email_address(input_data.name, input_data.email_address),
        provided_phone_number=normalize_phone_number(input_data.phone_number),
    )

    return recipient