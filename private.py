import os
from dotenv import load_dotenv


load_dotenv()

api_key = os.environ["FEDEX_API_KEY"]
secret_key = os.environ["FEDEX_SECRET_KEY"]
account_number = os.environ["ACCOUNT_NUMBER"]
company_name = os.environ["COMPANY_NAME"]
default_phone_number = os.environ["DEFAULT_PHONE_NUMBER"]
charge_code = os.environ["CHARGE_CODE"]
company_email_domain = os.environ["COMPANY_EMAIL_DOMAIN"]

# For confidentiality, corporate shipper information has been hidden.
shipper_street_line_one = os.environ["SHIPPER_STREET_LINE_ONE"]
shipper_street_line_two = os.environ["SHIPPER_STREET_LINE_TWO"]
shipper_city = os.environ["SHIPPER_CITY"]
shipper_state_code= os.environ["SHIPPER_STATE_CODE"]
shipper_postal_code= os.environ["SHIPPER_POSTAL_CODE"]
shipper_country_code = os.environ["SHIPPER_COUNTRY_CODE"]
shipper_is_residential = os.environ["SHIPPER_IS_RESIDENTIAL"].lower() == "true"
shipper_full_name = os.environ["SHIPPER_FULL_NAME"]
shipper_email_address = os.environ["SHIPPER_EMAIL_ADDRESS"]
shipper_provided_phone_number = os.environ["SHIPPER_PHONE_NUMBER"]