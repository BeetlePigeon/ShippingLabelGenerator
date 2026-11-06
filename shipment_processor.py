import json
import re
import base64
from datetime import date
from pathlib import Path
from scraper import Scraper
from parser import Parser
from tables import state_codes
from schema_classes import Address, Shipment, RatesOption, RatesOptions
from config import APIEnvironment, ship_API_config, rates_API_config, validation_API_config, LABEL_SUBDIR
from api_requests import request_access_token, request_suggested_address, request_rates_options, request_shipping_label
from private import (
    sandbox_api_key,
    sandbox_secret_key,
    production_api_key,
    production_secret_key,
    company_name,
    charge_code,
    shipper_account_number,
    shipper_street_line_one,
    shipper_street_line_two,
    shipper_city,
    shipper_state_code,
    shipper_postal_code,
    shipper_country_code,
    shipper_address_is_commercial,
    shipper_name,
    shipper_email_address,
    shipper_phone_number,
    default_shipment_weight,
)


class Processor:
    def __init__(self):
        self.sandbox_token = None
        self.production_token = None

        self.scraper = Scraper()
        self.parser = Parser()

        self.address_valid = False
        self.address_changed_since_validated = True
        self.address_snapshot = None

        self.preshipment_details = {
            "recipient_name": "",
            "recipient_email": "",
            "recipient_phone": "",
            "street_line_one": "",
            "street_line_two": "",
            "city": "",
            "state_code": "",
            "postal_code": "",
            "address_is_commercial": -1,
            "reference": "",
            "weight": "",
            "other_email_1": "",
            "other_email_2": "",
            "other_email_3": "",
        }

        self.suggested_address = {
            "street_line_one": "",
            "street_line_two": "",
            "city": "",
            "state_code": "",
            "postal_code": "",
            "address_is_commercial": -1,
        }

        self.rates = None


    def request_tokens(self):
        sandbox_response_json = request_access_token(sandbox_api_key, sandbox_secret_key, APIEnvironment.SANDBOX)
        s_token = sandbox_response_json.get("access_token")

        production_response_json = request_access_token(production_api_key, production_secret_key, APIEnvironment.PRODUCTION)
        p_token = production_response_json.get("access_token")

        if not s_token or not p_token:
            return False

        self.sandbox_token = s_token
        self.production_token = p_token
        return True


    @staticmethod
    def pretty_print(response):
        pretty_json = json.dumps(response, indent=4)
        print(pretty_json)


    @staticmethod
    def required_text_is_valid(text: str) -> bool:
        return bool(text)


    @staticmethod
    def name_is_valid(text: str) -> bool:
        return bool(text)


    @staticmethod
    def email_is_valid(text: str) -> bool:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not text or re.fullmatch(email_regex, text):
            return True
        return False


    @staticmethod
    def phone_is_valid(text: str) -> bool:
        cleaned = re.sub(r'\D', '', text)
        return not text or len(cleaned) == 10 or (len(cleaned) == 11 and cleaned.startswith("1"))


    @staticmethod
    def reference_is_valid(text: str) -> bool:
        return not text or len(text) <= 24


    @staticmethod
    def weight_is_valid(weight: str) -> bool:
        return (not weight or
                any(char.isdigit() for char in weight)
                and 0 < float(weight) <= 20
        )


    @staticmethod
    def state_code_is_valid(selection: str) -> bool:
        return selection in state_codes


    @staticmethod
    def postal_code_is_valid(text: str) -> bool:
        if not text:
            return True

        if len(text) in (5, 9) and all(char in "0123456789" for char in text):
            return True

        if len(text) == 10 and all(char in "0123456789-" for char in text) and text.count("-") == 1 and text[5] == "-":
            return True

        return False


    def clear_preshipment_details(self):
        self.preshipment_details["recipient_name"] = ""
        self.preshipment_details["recipient_email"] = ""
        self.preshipment_details["recipient_phone"] = ""

        self.preshipment_details["street_line_one"] = ""
        self.preshipment_details["street_line_two"] = ""
        self.preshipment_details["city"] = ""
        self.preshipment_details["state_code"] = ""
        self.preshipment_details["postal_code"] = ""
        self.preshipment_details["address_is_commercial"] = -1

        self.preshipment_details["reference"] = ""
        self.preshipment_details["weight"] = ""
        self.preshipment_details["other_email_1"] = ""
        self.preshipment_details["other_email_2"] = ""
        self.preshipment_details["other_email_3"] = ""


    def load_preshipment_details_from_scraper(self, request_num) -> bool:
        url = f"https://requestportal.americansystems.com/Request/Request?id={request_num}"

        if not self.scraper.request_number_is_feasible(request_num):
            return False

        if not self.scraper.session_is_authenticated(url):
            self.scraper.authenticate_session(url)

        if not self.scraper.request_number_is_valid(url):
            return False

        rp_dict = self.scraper.scrape_request(url).model_dump()

        name, recipient_email = self.parser.parse_names(rp_dict)
        phone = self.parser.parse_contact_numbers(rp_dict)

        raw_address = self.parser.parse_address(rp_dict)
        address_classification = -1

        reference = "no_reference"
        weight = default_shipment_weight
        other_emails = self.parser.parse_others_to_notify(rp_dict)

        self.preshipment_details["recipient_name"] = name
        self.preshipment_details["recipient_email"] = recipient_email
        self.preshipment_details["recipient_phone"] = phone

        self.preshipment_details["street_line_one"] = raw_address.street_line_one
        self.preshipment_details["street_line_two"] = raw_address.street_line_two
        self.preshipment_details["city"] = raw_address.city
        self.preshipment_details["state_code"] = raw_address.state_code
        self.preshipment_details["postal_code"] = raw_address.postal_code
        self.preshipment_details["address_is_commercial"] = address_classification

        self.preshipment_details["reference"] = reference
        self.preshipment_details["weight"] = weight
        self.preshipment_details["other_email_1"] = other_emails[0]
        self.preshipment_details["other_email_2"] = other_emails[1]
        self.preshipment_details["other_email_3"] = other_emails[2]

        return True


    def is_preshipment_valid(self):
        results = {
            "recipient_name": self.name_is_valid(self.preshipment_details["recipient_name"]),
            "recipient_email": self.email_is_valid(self.preshipment_details["recipient_email"]),
            "recipient_phone": self.phone_is_valid(self.preshipment_details["recipient_phone"]),

            "reference": self.reference_is_valid(self.preshipment_details["reference"]),
            "weight": self.weight_is_valid(self.preshipment_details["weight"]),
            "other_email_1": self.email_is_valid(self.preshipment_details["other_email_1"]),
            "other_email_2": self.email_is_valid(self.preshipment_details["other_email_2"]),
            "other_email_3": self.email_is_valid(self.preshipment_details["other_email_3"]),

            "street_line_one": self.required_text_is_valid(self.preshipment_details["street_line_one"]),
            "street_line_two": True,
            "city": self.required_text_is_valid(self.preshipment_details["city"]),
            "state_code": self.state_code_is_valid(self.preshipment_details["state_code"]),
            "postal_code": self.postal_code_is_valid(self.preshipment_details["postal_code"]),
            "address_type": self.preshipment_details["address_is_commercial"] in (0, 1),
        }

        return results


    def address_from_response(self, response):
        street_lines = response.get("streetLinesToken")
        if street_lines:
            street_line_one = street_lines[0]
            if len(street_lines) == 1:
                street_line_two = ""
            else:
                street_line_two = street_lines[1]
        else:
            street_line_one, street_line_two = "", ""

        city = response.get("city")
        state_code = response.get("stateOrProvinceCode")
        postal_code = response.get("postalCode")

        corrected_address = self.build_address_obj(
            street_line_one,
            street_line_two,
            city,
            state_code,
            postal_code,
        )

        return corrected_address


    @staticmethod
    def classification_from_response(response):
        classification = response.get("classification") or ""

        if classification:
            if classification == "RESIDENTIAL":
                address_is_commercial = 0
            elif classification == "BUSINESS":
                address_is_commercial = 1
            else:
                address_is_commercial = -1
        else:
            address_is_commercial = -1

        return address_is_commercial


    @staticmethod
    def build_address_obj(street_line_one, street_line_two, city, state_code, postal_code):
        return Address(
            street_line_one=street_line_one or "",
            street_line_two=street_line_two or "",
            city=city or "",
            state_code=state_code or "",
            postal_code=postal_code or "",
        )


    @staticmethod
    def address_is_confirmed(response):
        messages = response.get("customerMessages") or []
        msg = messages[0].get("code") if messages else None

        attributes = response.get("attributes") or {}

        address_type = attributes.get("AddressType")
        resolved = attributes.get("Resolved")
        dpv = attributes.get("DPV")

        if address_type == "STANDARDIZED" and resolved == "true" and dpv == "true":
            return True
        elif address_type == "NORMALIZED" and resolved == "false" and dpv == "false" and msg == "STANDARDIZED.ADDRESS.NOTFOUND":
            return False
        else:
            return None


    def build_preshipment_data(self, selected_service_type=None):
        shipper_address = Address(
            street_line_one=shipper_street_line_one,
            street_line_two=shipper_street_line_two,
            city=shipper_city,
            state_code=shipper_state_code,
            postal_code=shipper_postal_code,
            country_code=shipper_country_code,
        )

        recipient_address = Address(
            street_line_one=self.preshipment_details["street_line_one"],
            street_line_two=self.preshipment_details["street_line_two"],
            city=self.preshipment_details["city"],
            state_code=self.preshipment_details["state_code"],
            postal_code=self.preshipment_details["postal_code"],
            country_code="US",
        )

        return Shipment(
            company_name=company_name,
            charge_code=charge_code,
            account_number=shipper_account_number,

            shipper_address=shipper_address,
            shipper_name=shipper_name,
            shipper_email_address=shipper_email_address,
            shipper_phone_number=shipper_phone_number,
            shipper_address_is_commercial=shipper_address_is_commercial,

            recipient_address=recipient_address,
            recipient_name=self.preshipment_details["recipient_name"],
            recipient_email_address=self.preshipment_details["recipient_email"],
            recipient_phone_number=self.preshipment_details["recipient_phone"],
            recipient_address_is_commercial=bool(self.preshipment_details["address_is_commercial"]),

            reference=self.preshipment_details["reference"],
            weight=self.preshipment_details["weight"] or default_shipment_weight,
            other_email_1=self.preshipment_details["other_email_1"],
            other_email_2=self.preshipment_details["other_email_2"],
            other_email_3=self.preshipment_details["other_email_3"],

            selected_service_type=selected_service_type,
        )


    def build_final_shipment_data(self, service_type):
        return self.build_preshipment_data(selected_service_type=service_type)


    def suggested_address_to_preshipment_address(self):
        self.preshipment_details["street_line_one"] = self.suggested_address["street_line_one"]
        self.preshipment_details["street_line_two"] = self.suggested_address["street_line_two"]
        self.preshipment_details["city"] = self.suggested_address["city"]
        self.preshipment_details["state_code"] = self.suggested_address["state_code"]
        self.preshipment_details["postal_code"] = self.suggested_address["postal_code"]
        self.preshipment_details["address_is_commercial"] = self.suggested_address["address_is_commercial"]


    def set_suggested_address(self, address, is_commercial):
        self.suggested_address["street_line_one"] = address.street_line_one
        self.suggested_address["street_line_two"] = address.street_line_two
        self.suggested_address["city"] = address.city
        self.suggested_address["state_code"] = address.state_code
        self.suggested_address["postal_code"] = address.postal_code
        self.suggested_address["address_is_commercial"] = is_commercial


    def get_suggested_address(self):
        address = self.build_address_obj(
                self.preshipment_details["street_line_one"],
                self.preshipment_details["street_line_two"],
                self.preshipment_details["city"],
                self.preshipment_details["state_code"],
                self.preshipment_details["postal_code"],
            )

        response_json = request_suggested_address(self.sandbox_token, self.production_token, address, validation_API_config)

        resolved_addresses = response_json.get("output", {}).get("resolvedAddresses") or []

        if not resolved_addresses:
            raise ValueError("FedEx returned no resolved addresses.")

        resolved_address = resolved_addresses[0]

        confirmed_address = self.address_is_confirmed(resolved_address)
        suggested_address = self.address_from_response(resolved_address)
        address_classification = self.classification_from_response(resolved_address)

        return confirmed_address, suggested_address, address_classification


    def clear_suggested_address(self):
        self.suggested_address["street_line_one"] = ""
        self.suggested_address["street_line_two"] = ""
        self.suggested_address["city"] = ""
        self.suggested_address["state_code"] = ""
        self.suggested_address["postal_code"] = ""
        self.suggested_address["address_is_commercial"] = -1


    def retrieve_rates(self):
        preshipment_data = self.build_preshipment_data()
        rates_options = []

        response_json = request_rates_options(self.sandbox_token, self.production_token, preshipment_data, rates_API_config)

        errors = response_json.get("errors")
        if errors:
            return False

        rate_reply_details = response_json.get("output", {}).get("rateReplyDetails", [])

        if not rate_reply_details:
            return False

        for rates_option in rate_reply_details:
            rates_options.append(
                RatesOption(
                    service_type=rates_option["serviceType"],
                    estimated_delivery_time=rates_option["commit"]["dateDetail"]["dayFormat"],
                    estimated_delivery_cost=rates_option["ratedShipmentDetails"][0]["totalNetFedExCharge"],
                )
            )

        self.rates = RatesOptions(options=rates_options)
        return True


    def clear_rates(self):
        self.rates = None


    def create_and_save_label(self, shipment_data):
        response_json = request_shipping_label(self.sandbox_token, self.production_token, shipment_data, ship_API_config)

        errors = response_json.get("errors")
        if errors:
            return False

        shipments = response_json.get("output", {}).get("transactionShipments", [])
        if not shipments:
            return False

        tracking_number = shipments[0].get("masterTrackingNumber")
        piece_responses = shipments[0].get("pieceResponses", [])
        if not piece_responses:
            return False

        package_documents = piece_responses[0].get("packageDocuments", [])
        if not package_documents:
            return False

        encoded_label = package_documents[0].get("encodedLabel")

        if not encoded_label or not tracking_number:
            return False

        self.label_data_to_pdf(encoded_label, tracking_number)
        return True


    def label_data_to_pdf(self, label_data, tracking_number):
        label_bytes = base64.b64decode(label_data)
        output_directory = Path.home() / LABEL_SUBDIR
        output_directory.mkdir(exist_ok=True)
        today = date.today()
        today = today.strftime("%m-%d")
        cleaned_name = re.sub(r"[^a-zA-Z]", "", self.preshipment_details["recipient_name"])
        label_path = output_directory / f"{today}_{cleaned_name}_{tracking_number}.pdf"
        label_path.write_bytes(label_bytes)