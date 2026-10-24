import json
import re
from scraper import Scraper
from parser import Parser
from tables import state_codes
from api_settings import APIEnvironment, rates_API_config, validation_API_config
from api_requests import request_access_token, request_suggested_address, request_rates_options
from schema_classes import Address, Shipment
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
)


class Processor:
    def __init__(self):
        self.sandbox_token = request_access_token(sandbox_api_key, sandbox_secret_key, APIEnvironment.SANDBOX)
        self.production_token = request_access_token(production_api_key, production_secret_key, APIEnvironment.PRODUCTION)

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

        if not self.scraper.request_is_valid(url):
            return False

        rp_dict = self.scraper.scrape_request(url).model_dump()

        name, recipient_email = self.parser.parse_names(rp_dict)
        phone = self.parser.parse_contact_numbers(rp_dict)

        raw_address = self.parser.parse_address(rp_dict)
        address_classification = -1

        reference = "no_reference"
        weight = "8"
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
            "state_code": self.state_is_valid(self.preshipment_details["state_code"]),
            "postal_code": self.required_text_is_valid(self.preshipment_details["postal_code"]),
            "address_type": self.preshipment_details["address_is_commercial"] in (0, 1)
        }

        if results["street_line_one"]:
            address_check_response = self.request_address_validation(
                    self.preshipment_details["street_line_one"],
                    self.preshipment_details["street_line_two"],
                    self.preshipment_details["city"],
                    self.preshipment_details["state_code"],
                    self.preshipment_details["postal_code"],
                )

            results["address_valid"] = self.address_is_confirmed(address_check_response)

        return results


    def build_preshipment_data(self):
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
            weight=self.preshipment_details["weight"],
            other_email_1=self.preshipment_details["other_email_1"],
            other_email_2=self.preshipment_details["other_email_2"],
            other_email_3=self.preshipment_details["other_email_3"],

            selected_service_type=None,
        )


    def retrieve_rates(self):
        preshipment_data = self.build_preshipment_data()
        rates = request_rates_options(self.sandbox_token, self.production_token, preshipment_data, rates_API_config)
        return rates


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

        response = request_suggested_address(self.sandbox_token, self.production_token, address, validation_API_config).json()["output"]["resolvedAddresses"][0]

        confirmed_address = self.address_is_confirmed(response)
        suggested_address = self.address_from_response(response)
        address_classification = self.classification_from_response(response)

        return confirmed_address, suggested_address, address_classification


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
        if response["customerMessages"]:
            msg = response["customerMessages"][0]["code"]
        else:
            msg = None

        address_type = response["attributes"]["AddressType"]
        resolved = response["attributes"]["Resolved"]
        dpv = response["attributes"]["DPV"]

        if address_type == "STANDARDIZED" and resolved == "true" and dpv == "true":
            return True
        elif address_type == "NORMALIZED" and resolved == "false" and dpv == "false" and msg == "STANDARDIZED.ADDRESS.NOTFOUND":
            return False
        else:
            print(f"unknown case.\nType:{address_type}\nResolved:{resolved}\nDPV:{dpv}\nMessage:{msg}")
            return None


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
    def state_is_valid(selection) -> bool:
        return selection in state_codes