import base64
from pathlib import Path
import requests
from api_settings import APIEnvironment, rates_API_config, ship_API_config
from private import sandbox_api_key, sandbox_secret_key, production_api_key, production_secret_key, charge_code, test_key_account_number, shipper_account_number
from payload_builders import build_fedex_ship_payload, build_fedex_rates_payload
from shipper_info import get_default_shipper_info
from input import example_input
from recipient_info import get_recipient_info_from_input
from schema_classes import Shipment, RatesOption, RatesOptions


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


def create_pre_shipment(input_data):
    shipper = get_default_shipper_info()
    recipient = get_recipient_info_from_input(input_data)

    shipment_data = Shipment(
        shipper=shipper,
        recipient=recipient,
        asset_number=input_data.asset_number,
        case_number=input_data.case_number,
        charge_code=charge_code,
        shipment_weight=input_data.shipment_weight,
        other_emails_to_notify=input_data.other_emails_to_notify,
        selected_service_type=None,
    )

    return shipment_data


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


def select_from_rates_options(shipment, rates,  rates_environment, ship_environment):
    if rates_environment == APIEnvironment.SANDBOX or ship_environment == APIEnvironment.SANDBOX:
        shipment.selected_service_type = shipment.default_service_type
    else:
        shipment.selected_service_type = rates.cheapest.service_type

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
    print(f"Label creation status code: {response.status_code}")

    response.raise_for_status()
    response_data = response.json()

    return response_data


def save_label(response_data, label_recipient_name):
    tracking_number = response_data["output"]["transactionShipments"][0]["masterTrackingNumber"]
    encoded_label = response_data["output"]["transactionShipments"][0]["pieceResponses"][0]["packageDocuments"][0]["encodedLabel"]
    label_bytes = base64.b64decode(encoded_label)
    output_directory = Path(__file__).parent / "output_labels"
    output_directory.mkdir(exist_ok=True)
    label_path = output_directory / f"{label_recipient_name}_{tracking_number}.pdf"
    label_path.write_bytes(label_bytes)



if __name__ == '__main__':
    # Fetch OAuth tokens
    sandbox_token = get_access_token(sandbox_api_key, sandbox_secret_key, APIEnvironment.SANDBOX)
    production_token = get_access_token(production_api_key, production_secret_key, APIEnvironment.PRODUCTION)


    # Process shipment input data into shipping label PDF
    shipment_without_rate_option_selected = create_pre_shipment(example_input)
    available_rates_options = populate_rates_options(sandbox_token, production_token, shipment_without_rate_option_selected, rates_API_config)
    shipment_with_rate_option_selected = select_from_rates_options(shipment_without_rate_option_selected, available_rates_options, rates_API_config, ship_API_config)
    label = create_label(sandbox_token, production_token, shipment_with_rate_option_selected, ship_API_config)
    save_label(label, shipment_with_rate_option_selected.recipient.full_name)