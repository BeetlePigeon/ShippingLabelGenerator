import os
from dotenv import load_dotenv
from schema_classes import ShippingContact


load_dotenv()

api_key = os.environ["FEDEX_API_KEY"]
secret_key = os.environ["FEDEX_SECRET_KEY"]
account_number = os.environ["ACCOUNT_NUMBER"]
company_name = os.environ["COMPANY_NAME"]

# For confidentiality, corporate shipper information has been hidden.
shipper = ShippingContact(
    street_line_one = os.environ["SHIPPER_STREET_LINE_ONE"],
    street_line_two = os.environ["SHIPPER_STREET_LINE_TWO"],
    city = os.environ["SHIPPER_CITY"],
    state_code= os.environ["SHIPPER_STATE_CODE"],
    postal_code= os.environ["SHIPPER_POSTAL_CODE"],
    country_code = os.environ["SHIPPER_COUNTRY_CODE"],
    is_residential = os.environ["SHIPPER_IS_RESIDENTIAL"].lower() == "true",
    full_name = os.environ["SHIPPER_FULL_NAME"],
    email_address = os.environ["SHIPPER_EMAIL_ADDRESS"],
    phone_number = os.environ["SHIPPER_PHONE_NUMBER"],
)