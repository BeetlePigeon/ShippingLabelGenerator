import json
import base64
from pathlib import Path
import requests
from jsonschema import validate, ValidationError
from private import api_key, secret_key, charge_code
from ship_payload import build_fedex_ship_payload
from shipper_info import get_default_shipper_info
from recipient_info import get_sample_recipient_info
from schema_classes import Shipment, ServiceType


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


def validate_payload(payload):
    ## Legacy function, remove it or upgrade it later
    ship_schema_filename = "fedex_ship_schema.json"
    schema_path = Path(__file__).parent / ship_schema_filename
    try:
        with schema_path.open("r", encoding="utf-8") as file:
            ship_schema = json.load(file)
        validate(instance=payload, schema=ship_schema)
        print("Valid payload, sending to FedEx...")
        return True
    except FileNotFoundError:
        print(f"File {ship_schema_filename} not found")
        return False
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {ship_schema_filename}: {e}")
        return False
    except ValidationError as e:
        print(f"Ship payload validation failed: {e.message}")
        return False


def create_label(token):
    url = "https://apis-sandbox.fedex.com/ship/v1/shipments"
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
        }

    shipper = get_default_shipper_info()
    recipient = get_sample_recipient_info()

    shipment = Shipment(
        shipper=shipper,
        recipient=recipient,
        asset_number="SAMPLE_ASSET_73",
        case_number="SAMPLE_CASE_37",
        service_type=ServiceType.FEDEX_2_DAY,
        charge_code=charge_code
    )

    label_payload = build_fedex_ship_payload(shipment)
    response = requests.post(url, json=label_payload, headers=headers, timeout=30)

    print(response.status_code)
    print(response.text)

    response.raise_for_status()

    response_data = response.json()
    save_label(response_data, recipient)


def save_label(response_data, label_recipient):
    encoded_label = response_data["output"]["transactionShipments"][0]["pieceResponses"][0]["packageDocuments"][0]["encodedLabel"]
    label_bytes = base64.b64decode(encoded_label)
    output_directory = Path("output_labels")
    output_directory.mkdir(exist_ok=True)
    label_path = output_directory / f"{label_recipient.full_name}.pdf"
    label_path.write_bytes(label_bytes)


if __name__ == '__main__':
    access_token = get_access_token()
    create_label(access_token)