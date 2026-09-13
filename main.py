import base64
from pathlib import Path
import requests
from private import api_key, secret_key, charge_code
from ship_payload import build_fedex_ship_payload, build_fedex_rates_payload
from shipper_info import get_default_shipper_info
from input import example_input
from recipient_info import get_recipient_info_from_input
from schema_classes import Shipment


def get_access_token():
    url = "https://apis-sandbox.fedex.com/oauth/token"
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


def get_rates(token, shipment_data):
    url = "https://apis-sandbox.fedex.com/rate/v1/rates/quotes"
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
    }

    payload = build_fedex_rates_payload(shipment_data)
    response = requests.post(url, json=payload, headers=headers, timeout=30)

    print(response.status_code)
    print(response.text)
    response.raise_for_status()
    rates_data = response.json()

    return rates_data


def select_from_available_rates(shipment, rates=None):
    if not rates:
        shipment.selected_service_type = None
    return shipment


def create_label(token, shipment_data):
    url = "https://apis-sandbox.fedex.com/ship/v1/shipments"
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
        }

    label_payload = build_fedex_ship_payload(shipment_data)
    response = requests.post(url, json=label_payload, headers=headers, timeout=30)
    print(f"Label creation status code: {response.status_code}\n")
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
    access_token = get_access_token()
    shipment_without_rate = create_pre_shipment(example_input)
#    available_rates = get_rates(access_token, shipment_without_rate)
    shipment_with_rate_selected = select_from_available_rates(shipment_without_rate)
    label = create_label(access_token, shipment_with_rate_selected)
    save_label(label, shipment_with_rate_selected.recipient.full_name)