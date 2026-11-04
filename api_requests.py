import requests
from config import APIEnvironment
from payload_builders import build_address_validation_payload, build_fedex_ship_payload, build_fedex_rates_payload
from private import (
    test_key_account_number,
    shipper_account_number,
)


def request_access_token(api_key, secret_key, environment):
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
        raise RuntimeError("FedEx reponse did not contain a valid access token")

    return token


def request_suggested_address(sandbox_auth_token, production_auth_token, address, environment):
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

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    suggestion_response_json = response.json()

    return suggestion_response_json


def request_rates_options(sandbox_auth_token, production_auth_token, shipment_data, environment):
    if environment == APIEnvironment.SANDBOX:
        url = "https://apis-sandbox.fedex.com/rate/v1/rates/quotes"
        token = sandbox_auth_token
        account_number = test_key_account_number
    else:
        url = "https://apis.fedex.com/rate/v1/rates/quotes"
        token = production_auth_token
        account_number = shipper_account_number

    payload = build_fedex_rates_payload(shipment_data, account_number)
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    rates_response_json = response.json()

    return rates_response_json


def request_shipping_label(sandbox_auth_token, production_auth_token, shipment_data, environment):
    if environment == APIEnvironment.SANDBOX:
        url = "https://apis-sandbox.fedex.com/ship/v1/shipments"
        token = sandbox_auth_token
        account_number = test_key_account_number
    else:
        url = "https://apis.fedex.com/ship/v1/shipments"
        token = production_auth_token
        account_number = shipper_account_number

    payload = build_fedex_ship_payload(shipment_data, account_number)
    headers = {
        'Content-Type': "application/json",
        'X-locale': "en_US",
        'Authorization': f"Bearer {token}"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    ship_response_json = response.json()

    return ship_response_json