import os
from dotenv import load_dotenv


load_dotenv()

sandbox_api_key = os.environ["FEDEX_SANDBOX_API_KEY"]
sandbox_secret_key = os.environ["FEDEX_SANDBOX_SECRET_KEY"]
production_rates_api_key = os.environ["FEDEX_PRODUCTION_RATES_API_KEY"]
production_rates_secret_key = os.environ["FEDEX_PRODUCTION_RATES_SECRET_KEY"]
production_ship_api_key = os.environ["FEDEX_PRODUCTION_SHIP_API_KEY"]
production_ship_secret_key = os.environ["FEDEX_PRODUCTION_SHIP_SECRET_KEY"]
test_key_account_number = os.environ["TEST_KEY_ACCOUNT_NUMBER"]
shipper_account_number = os.environ["SHIPPER_ACCOUNT_NUMBER"]
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