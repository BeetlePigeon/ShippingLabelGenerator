import base64
from pathlib import Path
import requests
from api_settings import APIEnvironment
from payload_builders import build_address_validation_payload, build_fedex_ship_payload, build_fedex_rates_payload
from schema_classes import Address, Shipment, RatesOption, RatesOptions
from private import (
    company_name,
    charge_code,
    test_key_account_number,
    shipper_account_number,
    shipper_street_line_one,
    shipper_street_line_two,
    shipper_city,
    shipper_state_code,
    shipper_postal_code,
    shipper_country_code,
    shipper_address_is_residential,
    shipper_name,
    shipper_email_address,
    shipper_phone_number,
)


def get_access_token(api_key, secret_key, environment):
    if environment == APIEnvironment.SANDBOX:
        url = "https://apis-sandbox.fedex.com/oauth/token"
    else:
        url = "https://apis.fedex.com/oauth/token"
    headers = {
        'Content-Type': "application/x-www-form-urlencoded"
    }
    payload = {
        'grant_type': "client_credentials",
        'client_id': api_key,
        'client_secret': secret_key,
    }
    response = requests.post(url, data=payload, headers=headers, timeout=30)
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("FedEx reponse did not contain access token")
    return token


def build_shipment_data(input_data):
    shipper_address = Address(
        street_line_one=shipper_street_line_one,
        street_line_two=shipper_street_line_two,
        city=shipper_city,
        state_code=shipper_state_code,
        postal_code=shipper_postal_code,
        country_code=shipper_country_code,
    )

    return Shipment(
        company_name=company_name,
        charge_code=charge_code,
        account_number=shipper_account_number,

        shipper_address=shipper_address,
        shipper_name=shipper_name,
        shipper_email_address=shipper_email_address,
        shipper_phone_number=shipper_phone_number,
        shipper_address_is_residential=shipper_address_is_residential,

        recipient_address=input_data.address,
        recipient_name=input_data.name,
        recipient_email_address=input_data.email_address,
        recipient_phone_number=input_data.phone_number,
        recipient_address_is_residential=input_data.address_is_residential,

        other_emails_to_notify=input_data.other_emails_to_notify,
        case_number=input_data.case_number,
        asset_number=input_data.asset_number,
        shipment_weight=input_data.shipment_weight,

        selected_service_type=None,
    )


def attempt_address_completion(sandbox_auth_token, production_auth_token, address, environment):
    if environment == APIEnvironment.SANDBOX:
        url = "https://apis-sandbox.fedex.com/address/v1/addresses/resolve"
        token = sandbox_auth_token
        account_number = test_key_account_number
    else:
        url = "https://apis.fedex.com/address/v1/addresses/resolve"
        token = production_auth_token
        account_number = shipper_account_number

    payload = build_address_validation_payload(address, account_number)
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
    }

    response = requests.post(url, json=payload, headers=headers)

    return response


def populate_rates_options(sandbox_auth_token, production_auth_token, shipment_data, environment):
    if environment == APIEnvironment.SANDBOX:
        url = "https://apis-sandbox.fedex.com/rate/v1/rates/quotes"
        token = sandbox_auth_token
        account_number = test_key_account_number
    else:
        url = "https://apis.fedex.com/rate/v1/rates/quotes"
        token = production_auth_token
        account_number = shipper_account_number

    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
    }

    payload = build_fedex_rates_payload(shipment_data, account_number)
    response = requests.post(url, json=payload, headers=headers, timeout=30)

    print(f"Rates retrieval status code: {response.status_code}")
    response.raise_for_status()
    rates_data = response.json()

    rates_options = []
    for rates_option in rates_data["output"]["rateReplyDetails"]:
        rates_options.append(
            RatesOption(
                service_type=rates_option["serviceType"],
                estimated_delivery_time=rates_option["commit"]["dateDetail"]["dayFormat"],
                estimated_delivery_cost=rates_option["ratedShipmentDetails"][0]["totalNetFedExCharge"],
            )
        )

    rates_options = RatesOptions(options=rates_options)
    return rates_options


def select_from_rates_options(shipment, available_rates, rates_environment, ship_environment):
    if rates_environment == APIEnvironment.SANDBOX or ship_environment == APIEnvironment.SANDBOX:
        shipment.selected_service_type = shipment.default_service_type
    else:
        shipment.selected_service_type = shipment.default_service_type
    return shipment


def create_label(sandbox_auth_token, production_auth_token, shipment_data, environment):
    if environment == APIEnvironment.SANDBOX:
        url = "https://apis-sandbox.fedex.com/ship/v1/shipments"
        token = sandbox_auth_token
        account_number = test_key_account_number
    else:
        url = "https://apis.fedex.com/ship/v1/shipments"
        token = production_auth_token
        account_number = shipper_account_number

    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
    }

    label_payload = build_fedex_ship_payload(shipment_data, account_number)
    response = requests.post(url, json=label_payload, headers=headers, timeout=30)
    #    print(response.text)
    print(f"Label creation status code: {response.status_code}")

    response.raise_for_status()
    response_data = response.json()

    return response_data


def save_label(response_data, label_recipient_name):
    tracking_number = response_data["output"]["transactionShipments"][0]["masterTrackingNumber"]
    encoded_label = response_data["output"]["transactionShipments"][0]["pieceResponses"][0]["packageDocuments"][0][
        "encodedLabel"]
    label_bytes = base64.b64decode(encoded_label)
    output_directory = Path(__file__).parent / "output_labels"
    output_directory.mkdir(exist_ok=True)
    label_path = output_directory / f"{label_recipient_name}_{tracking_number}.pdf"
    label_path.write_bytes(label_bytes)