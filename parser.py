from private import company_email_domain, recipient_default_phone_number
from schema_classes import Address
import usaddress
import re


class Parser:
    def __init__(self, gui):
        self.gui = gui


    @staticmethod
    def get_email_address_from(name_string: str) -> str:
        def d(string):
            a = re.sub("'", "", string)
            b = re.sub(" ", "", a)
            return b

        parts = re.split(",", name_string)
        second_part, first_part = parts[0], parts[1]

        # Remove employee ID
        first_part = re.sub(r"\s*\(\d+\)", "", first_part).strip()

        # Check for nickname and remove it if it exists
        match = re.search(r"\(([^)]+)\)", first_part)
        if match:
            nickname = match.group(1)
            first_part = first_part.replace(f"({nickname})", "").strip()

        return f"{d(first_part)}.{d(second_part)}@{company_email_domain}"


    @staticmethod
    def get_label_name_from(name_string: str, new_hire: bool=False) -> str:
        if new_hire:
            if "," in name_string:
                parts = re.split(", ", name_string)
                second_part, first_part = parts[0], parts[1]
                label_name = f"{first_part} {second_part}"
            else:
                label_name = name_string

        else:
            parts = re.split(",", name_string)
            second_part, first_part = parts[0], parts[1]

            # Remove employee ID
            first_part = re.sub(r"\s*\(\d+\)", "", first_part).strip()

            # Check for nickname and use it instead of first part of name if it exists
            match = re.search(r"\(([^)]+)\)", first_part)
            if match:
                nickname = match.group(1)
                first_part = nickname

            label_name = f"{first_part} {second_part}"

        return label_name


    def parse_names(self, data):
        requester = data["request_by"]
        requestee = data["request_for"]
        new_hire = data["new_hire_name"]

        if new_hire:
            label_name = self.get_label_name_from(new_hire, new_hire=True)
            email_address = self.get_email_address_from(requester)
        elif requester != requestee:
            label_name = self.get_label_name_from(requestee)
            email_address = self.get_email_address_from(requestee)
        else:
            label_name = self.get_label_name_from(requester)
            email_address = self.get_email_address_from(requester)

        return label_name, email_address


    @staticmethod
    def parse_contact_numbers(data) -> str:
        raw_phone = data["phone_number"]
        raw_cell = data["cell_phone"]

        if raw_phone:
            parsed_num = re.sub(r'\D', '', raw_phone)
        elif raw_cell:
            parsed_num = re.sub(r'\D', '', raw_cell)
        else:
            parsed_num = recipient_default_phone_number

        return parsed_num


    @staticmethod
    def parse_others_to_notify(data) -> list[str]:
        parts = re.split("; ", data["others_to_notify"])
        others_to_notify = [part for part in parts]
        return others_to_notify


    def parse_address(self, data):
        raw_address = data["address"]

        address_parts = usaddress.tag(raw_address, tag_mapping={
            'Recipient': 'recipient',
            'AddressNumber': 'address1',
            'AddressNumberPrefix': 'address1',
            'AddressNumberSuffix': 'address1',
            'StreetName': 'address1',
            'StreetNamePreDirectional': 'address1',
            'StreetNamePreModifier': 'address1',
            'StreetNamePreType': 'address1',
            'StreetNamePostDirectional': 'address1',
            'StreetNamePostModifier': 'address1',
            'StreetNamePostType': 'address1',
            'CornerOf': 'address1',
            'IntersectionSeparator': 'address1',
            'LandmarkName': 'address1',
            'USPSBoxGroupID': 'address1',
            'USPSBoxGroupType': 'address1',
            'USPSBoxID': 'address1',
            'USPSBoxType': 'address1',
            'BuildingName': 'address2',
            'OccupancyType': 'address2',
            'OccupancyIdentifier': 'address2',
            'SubaddressIdentifier': 'address2',
            'SubaddressType': 'address2',
            'PlaceName': 'city',
            'StateName': 'state',
            'ZipCode': 'zip_code',
        })

        address = {
            "street_line_one": address_parts[0].get('address1') or "",
            "street_line_two": address_parts[0].get('address2') or "",
            "city": address_parts[0].get('city') or "",
            "state_code": address_parts[0].get('state') or "",
            "postal_code": address_parts[0].get('zip_code') or "",
            "country_code": "US"
        }

        return Address(**address)