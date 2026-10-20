import tkinter
import re
from tkinter import ttk
from scraper import Scraper
from parser import Parser
from tables import state_codes
from private import sandbox_api_key, sandbox_secret_key, production_api_key, production_secret_key, rp_url_prefix
from api_settings import APIEnvironment, rates_API_config, ship_API_config, validation_API_config
from api_requests import get_access_token, build_shipment_data, attempt_address_completion, populate_rates_options, select_from_rates_options, create_label, save_label
from schema_classes import InputData, Address
from input import example_input
from PIL import Image, ImageTk
from pathlib import Path
from sample_inputs import test_requests
import json


class GUI:
    def __init__(self):
        self.sandbox_token = get_access_token(sandbox_api_key, sandbox_secret_key, APIEnvironment.SANDBOX)
        self.production_token = get_access_token(production_api_key, production_secret_key, APIEnvironment.PRODUCTION)

        self.scraper = Scraper()
        self.parser = Parser(self)

        self.root = tkinter.Tk()
        self.root.title("FedEx Shipping Label Generator")


        assets_dir = Path(__file__).parent

        company_icon = Image.open(assets_dir / "company_icon.png")
        company_icon = company_icon.convert("RGBA")
        company_icon.thumbnail((64, 64), Image.Resampling.LANCZOS)

        self.company_icon = ImageTk.PhotoImage(company_icon)
        self.root.iconphoto(True, self.company_icon)

        self.configure_styles()

        self.main_frame = ttk.Frame(self.root, padding=(22, 18, 22, 12))
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        title_frame.columnconfigure(0, weight=1)

        header_inner = ttk.Frame(title_frame)
        header_inner.grid(row=0, column=0)

        fedex_image = Image.open(assets_dir / "fedex_logo.png")
        fedex_image = fedex_image.resize((90, 50))
        self.fedex_logo_image = ImageTk.PhotoImage(fedex_image)

        tkinter.Label(header_inner, image=self.fedex_logo_image, bg=self.colors["bg"], borderwidth=0).pack(side="left", padx=(0, 12))
        ttk.Label(header_inner, text="Shipping Label Generator", font=("Segoe UI", 18, "bold")).pack(side="left")

        self.rp_outer_frame = ttk.Frame(self.main_frame, padding=(12, 10), style="Card.TFrame")
        self.rp_outer_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.rp_outer_frame.columnconfigure(0, weight=1)

        self.rp_frame = ttk.Frame(self.rp_outer_frame, style="CardInterior.TFrame")
        self.rp_frame.grid(row=0, column=0)

        ttk.Label(self.rp_frame, text="RequestPortal Number", style="Card.TLabel", font=("Segoe UI", 15, "bold")).pack(pady=(0, 5))

        rp_controls_frame = ttk.Frame(self.rp_frame, style="CardInterior.TFrame")
        rp_controls_frame.pack()

        validate_command = (self.root.register(self.validate_rp_number_entry), "%P")

        self.rp_number_entry = ttk.Entry(rp_controls_frame, width=26, validate="key", validatecommand=validate_command)
        self.rp_number_entry.pack(side="left")
        self.rp_number_entry.bind("<<Paste>>", self.handle_rp_paste)

        self.rp_paste_button = ttk.Button(rp_controls_frame, text="⧉", width=2, style="Icon.TButton", command=self.handle_rp_paste)
        self.rp_paste_button.pack(side="left", padx=(3, 10))

        self.load_shipment_details_button = ttk.Button(rp_controls_frame, text="Lookup", style="Primary.TButton", command=self.load_shipment_details)
        self.load_shipment_details_button.pack(side="left")

        self.rp_number_entry.bind("<Return>", lambda event: self.load_shipment_details_button.invoke())

        self.rp_error_label = ttk.Label(self.rp_outer_frame, text="", style="Error.TLabel")
        self.rp_error_label.grid(row=1, column=0, pady=(5, 0))

        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.grid(row=2, column=0, sticky="nsew")
        self.results_frame.columnconfigure(0, weight=1, uniform="form")
        self.results_frame.columnconfigure(1, weight=1, uniform="form")
        self.create_preshipment_sections()

        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=3, column=0, pady=(8, 0))

        self.retrieve_rates_button = ttk.Button(action_frame, text="Retrieve Rates", style="Primary.TButton", command=self.attempt_retrieve_rates)
        self.retrieve_rates_button.pack(side="left", padx=7)

        self.clear_shipment_details_button = ttk.Button(action_frame, text="Clear All", command=self.clear_preshipment_sections)
        self.clear_shipment_details_button.pack(side="left", padx=7)


    def configure_styles(self):
        self.colors = {
            "bg": "#eff3f9",
            "surface": "#ffffff",
            "muted": "#e9eff7",
            "border": "#ccd8e6",
            "ink": "#263449",
            "subtitle": "#67798f",

            "primary": "#4878b7",
            "primary_hover": "#3968a5",

            "button": "#e9f0f8",
            "button_hover": "#d7e6f5",

            "combobox": "#eaf0f8",
            "input_focus": "#80a7d6",
            "hover": "#b42318",

            "asterisk": "#d92d20"
        }

        c = self.colors
        self.root.configure(bg=c["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("Required.TLabel", background=c["surface"], foreground=c["asterisk"], font=("Segoe UI", 10, "bold"))

        style.configure("TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["surface"], relief="solid", borderwidth=1, bordercolor=c["border"])
        style.configure("CardInterior.TFrame", background=c["surface"], borderwidth=0, relief="flat")
        style.configure("TLabel", background=c["bg"], foreground=c["ink"], font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=c["surface"], foreground=c["ink"], font=("Segoe UI", 10))
        style.configure("Hint.TLabel", background=c["surface"], foreground=c["subtitle"], font=("Segoe UI", 9))
        style.configure("Error.TLabel", background=c["surface"], foreground=c["hover"], font=("Segoe UI", 10))

        style.configure("TEntry", fieldbackground="white", bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], relief="flat", borderwidth=1, padding=4, font=("Segoe UI", 10))
        style.map("TEntry", bordercolor=[("focus", c["input_focus"])])

        style.configure("TCombobox", fieldbackground="white", background=c["combobox"], bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], padding=4, font=("Segoe UI", 10))
        style.map("TCombobox", fieldbackground=[("readonly", "white")])

        style.configure("TButton", background=c["button"], foreground=c["ink"], borderwidth=1, relief="flat", bordercolor=c["border"], padding=(10, 5), font=("Segoe UI", 10))
        style.map("TButton", background=[("active", c["button_hover"])])

        style.configure("Icon.TButton", background=c["button"], foreground=c["ink"], bordercolor=c["border"], borderwidth=1, relief="flat", padding=(4, 3), font=("Segoe UI Symbol", 11))
        style.map("Icon.TButton", background=[("active", c["button_hover"])])

        style.configure("Primary.TButton", background=c["primary"], foreground="white", bordercolor=c["primary"], padding=(14, 5), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", c["primary_hover"])], foreground=[("active", "white")])

        style.configure("Card.TRadiobutton", background="white", foreground=c["ink"], font=("Segoe UI", 10))


    def create_field_label(self, parent, text, row, column=0, required=False, padx=5, pady=3):
        label_frame = ttk.Frame(parent, style="CardInterior.TFrame")
        label_frame.grid(row=row, column=column, sticky="w", padx=padx, pady=pady)

        ttk.Label(label_frame, text=text, style="Card.TLabel").pack(side="left")
        if required:
            ttk.Label(label_frame, text=" *", style="Required.TLabel").pack(side="left")


    def create_preshipment_sections(self):
        left_column = ttk.Frame(self.results_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        left_column.columnconfigure(0, weight=1)

        recipient_frame = ttk.Frame(left_column, padding=4, style="Card.TFrame")
        recipient_frame.grid(row=0, column=0, sticky="ew")
        recipient_frame.columnconfigure(1, weight=1)

        self.recipient_header = tkinter.Label(recipient_frame, text="Recipient", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=("Segoe UI", 12, "bold"))
        self.recipient_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.recipient_name = tkinter.StringVar(value="")
        self.recipient_email = tkinter.StringVar(value="")
        self.recipient_phone = tkinter.StringVar(value="")

        self.create_field_label(recipient_frame, "Name", 1, required=True)
        ttk.Entry(recipient_frame, textvariable=self.recipient_name, width=36).grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        self.create_field_label(recipient_frame, "Email", 2, required=False)
        ttk.Entry(recipient_frame, textvariable=self.recipient_email, width=36).grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        self.create_field_label(recipient_frame, "Phone", 3, required=False)
        phone_validation = (self.root.register(self.validate_phone_entry), "%P")
        ttk.Entry(recipient_frame, textvariable=self.recipient_phone, width=36, validate="key", validatecommand=phone_validation).grid(row=3, column=1, sticky="ew", padx=5, pady=3)

        other_frame = ttk.Frame(left_column, padding=4, style="Card.TFrame")
        other_frame.grid(row=1, column=0, sticky="ew")
        other_frame.columnconfigure(1, weight=1)

        self.other_header = tkinter.Label(other_frame, text="Other", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=("Segoe UI", 12, "bold"))
        self.other_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.reference = tkinter.StringVar(value="")
        self.weight = tkinter.StringVar(value="")
        self.other_emails = [tkinter.StringVar(value=""), tkinter.StringVar(value=""), tkinter.StringVar(value="")]

        fields = [
            ("Reference #", self.reference),
            ("Weight (lbs)", self.weight),
            ("Other Emails to Notify", self.other_emails[0]),
            ("", self.other_emails[1]),
            ("", self.other_emails[2]),
        ]

        weight_validation = (self.root.register(self.validate_weight_entry), "%P")
        for row, (field_name, field_value) in enumerate(fields):
            ttk.Label(other_frame, style="Card.TLabel", text=field_name).grid(row=row + 1, column=0, sticky="w", padx=5, pady=3)
            entry = ttk.Entry(other_frame, textvariable=field_value, width=36)
            if field_name == "Weight (lbs)":
                entry.configure(validate="key", validatecommand=weight_validation)
            entry.grid(row=row+1, column=1, sticky="ew", padx=5, pady=3)

        address_frame = ttk.Frame(self.results_frame, padding=4, style="Card.TFrame")
        address_frame.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        address_frame.columnconfigure(1, weight=1)

        self.address_header = tkinter.Label(address_frame, text="Address", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=("Segoe UI", 12, "bold"))
        self.address_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.street_line_one = tkinter.StringVar(value="")
        self.street_line_two = tkinter.StringVar(value="")
        self.city = tkinter.StringVar(value="")
        self.state_code = tkinter.StringVar(value="")
        self.postal_code = tkinter.StringVar(value="")
        self.address_is_commercial = tkinter.IntVar(value=-1)

        self.create_field_label(address_frame, "Street line 1", row=1, required=True, pady=4)
        ttk.Entry(address_frame, textvariable=self.street_line_one, width=36).grid(row=1, column=1, sticky="ew", padx=5, pady=4)

        self.create_field_label(address_frame, "Street line 2", row=2, required=False, pady=4)
        ttk.Entry(address_frame, textvariable=self.street_line_two, width=36).grid(row=2, column=1, sticky="ew", padx=5, pady=4)

        bottom_frame = ttk.Frame(address_frame, style="CardInterior.TFrame")
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=8)
        bottom_frame.columnconfigure(0, weight=1, uniform="bottom")
        bottom_frame.columnconfigure(1, weight=1, uniform="bottom")

        type_frame = ttk.Frame(bottom_frame, style="CardInterior.TFrame")
        type_frame.grid(row=0, column=0)

        ttk.Label(type_frame, style="Card.TLabel", text="Residential").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Radiobutton(type_frame, style="Card.TRadiobutton", variable=self.address_is_commercial, value=0).grid(row=0, column=1, sticky="w", padx=8)

        ttk.Label(type_frame, style="Card.TLabel", text="Commercial").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Radiobutton(type_frame, style="Card.TRadiobutton", variable=self.address_is_commercial, value=1).grid(row=1, column=1, sticky="w", padx=8)

        location_frame = ttk.Frame(bottom_frame, style="CardInterior.TFrame")
        location_frame.grid(row=0, column=1, sticky="ew")
        location_frame.columnconfigure(0, weight=1, uniform="location")
        location_frame.columnconfigure(1, weight=1, uniform="location")

        self.create_field_label(location_frame, "City", row=0, required=True, padx=0, pady=0)
        ttk.Entry(location_frame, textvariable=self.city).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2,10))

        self.create_field_label(location_frame, "State", row=2, column=0, required=True, padx=0, pady=0)
        ttk.Combobox(location_frame, textvariable=self.state_code, values=state_codes, state="readonly", width=6).grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=2)

        self.create_field_label(location_frame, "ZIP", row=2, column=1, required=True, padx=(5, 0), pady=0)
        zip_validation = (self.root.register(self.validate_zip_entry), "%P")
        ttk.Entry(location_frame, textvariable=self.postal_code, width=10, validate="key", validatecommand=zip_validation).grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=2)


    @staticmethod
    def validate_rp_number_entry(text: str) -> bool:
        return len(text) <= 6 and (text.isascii() and text.isdigit() or text == "")


    @staticmethod
    def validate_phone_entry(text: str) -> bool:
        return all(char in "0123456789.-_()+" for char in text)


    @staticmethod
    def validate_weight_entry(text: str) -> bool:
        return text.count(".") <= 1 and all(char in "0123456789." for char in text)


    @staticmethod
    def validate_zip_entry(text: str) -> bool:
        numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        if not text:
            return True
        if all(char in "0123456789-" for char in text) and text.startswith(tuple(numbers)) and text.count("-") <= 1:
            return True
        return False


    def extract_rp_number(self, text: str) -> str | None:
        text = text.strip()

        if text.startswith(rp_url_prefix):
            text = text.removeprefix(rp_url_prefix)

        if len(text) == 6 and text.isascii() and text.isdigit():
            return text

        return None


    def handle_rp_paste(self, event=None):
        pasted_text = self.root.clipboard_get().strip()

        request_number = self.extract_rp_number(pasted_text)

        if request_number is not None:
            self.rp_number_entry.delete(0, tkinter.END)
            self.rp_number_entry.insert(0, request_number)

            return "break"

        if pasted_text.startswith(rp_url_prefix):
            return "break"


    def clear_preshipment_sections(self):
        self.recipient_name.set("")
        self.recipient_email.set("")
        self.recipient_phone.set("")

        self.street_line_one.set("")
        self.street_line_two.set("")
        self.city.set("")
        self.state_code.set("")
        self.postal_code.set("")
        self.address_is_commercial.set(-1)

        self.reference.set("")
        self.weight.set("")

        for i in range(3):
            self.other_emails[i].set("")


    def load_shipment_details(self, test_case=None):
        if test_case:
            request_number = test_case
        else:
            request_number = self.rp_number_entry.get().strip()
            if request_number == "123123":
                self.run_load_shipment_test_cases()
                return

        url = f"https://requestportal.americansystems.com/Request/Request?id={request_number}"

        if not self.scraper.request_number_is_feasible(request_number):
            self.rp_error_label.config(text="Invalid RequestPortal number.")
            return

        if not self.scraper.session_is_authenticated(url):
            self.scraper.authenticate_session(url)

        if not self.scraper.request_is_valid(url):
            self.rp_error_label.config(text="Invalid RequestPortal number.")
            return

        rp_dict = self.scraper.scrape_request(url).model_dump()

        self.clear_preshipment_sections()

        name, email = self.parser.parse_names(rp_dict)
        phone = self.parser.parse_contact_numbers(rp_dict)

        raw_address = self.parser.parse_address(rp_dict)
        address_check_response = self.request_address_validation(
            raw_address.street_line_one,
            raw_address.street_line_two,
            raw_address.city,
            raw_address.state_code,
            raw_address.postal_code
        )

        normalized_address = self.address_from_response(address_check_response)
        address_classification = self.classification_from_response(address_check_response)

        reference = "PLACEHOLDER"
        weight = 6.9
        other_emails = self.parser.parse_others_to_notify(rp_dict)

        self.recipient_name.set(name)
        self.recipient_email.set(email)
        self.recipient_phone.set(phone)

        self.street_line_one.set(normalized_address.street_line_one)
        self.street_line_two.set(normalized_address.street_line_two)
        self.city.set(normalized_address.city)
        self.state_code.set(normalized_address.state_code)
        self.postal_code.set(normalized_address.postal_code)
        self.address_is_commercial.set(address_classification)

        self.reference.set(reference)
        self.weight.set(str(weight))

        for i in range(min(len(other_emails), 3)):
            self.other_emails[i].set(other_emails[i])


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


    @staticmethod
    def build_address(street_line_one, street_line_two, city, state_code, postal_code):
        return Address(
            street_line_one=street_line_one or "",
            street_line_two=street_line_two or "",
            city=city or "",
            state_code=state_code or "",
            postal_code=postal_code or "",
        )


    def build_shipment(self):
        shipment = InputData(
            street_line_one=self.street_line_one.get(),
            street_line_two=self.street_line_two.get(),
            city=self.city.get(),
            state_code=self.state_code.get(),
            postal_code=self.postal_code.get(),
            name=self.recipient_name.get(),
            email_address=self.recipient_email.get(),
            phone_number=self.recipient_phone.get(),
            address_is_commercial=bool(self.address_is_commercial.get()),
            reference=self.reference.get(),
            shipment_weight=float(self.weight.get()),
            other_emails_to_notify=[email.get().strip() for email in self.other_emails if email.get().strip()],
        )

        return shipment


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

        corrected_address = self.build_address(
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
            else:
                address_is_commercial = 1
        else:
            address_is_commercial = -1

        return address_is_commercial


    def validate_fedex_address(self, address):
        response = attempt_address_completion(self.sandbox_token, self.production_token, address, validation_API_config).json()["output"]["resolvedAddresses"][0]

        return response


    def request_address_validation(self, street_line_one, street_line_two, city, state_code, postal_code):
        address_from_entry = self.build_address(
                street_line_one,
                street_line_two,
                city,
                state_code,
                postal_code,
            )

        response = self.validate_fedex_address(address_from_entry)

        return response


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
            confirmed = True
        elif address_type == "NORMALIZED" and resolved == "false" and dpv == "false" and msg == "STANDARDIZED.ADDRESS.NOTFOUND":
            confirmed = False
        else:
            confirmed = f"unknown case.\nType:{address_type}\nResolved:{resolved}\nDPV:{dpv}\nMessage:{msg}"

        print(f"Address confirmed: {confirmed}")
        return confirmed


    def list_valid_inputs(self, name, email, phone, reference, weight, other_email_1, other_email_2, other_email_3,
                       street_line_one, street_line_two, city, state_code, postal_code, classification):

        address_check_response = self.request_address_validation(
                street_line_one,
                street_line_two,
                city,
                state_code,
                postal_code
            )

        results = {
            "recipient_name": self.name_is_valid(name),
            "recipient_email": self.email_is_valid(email),
            "recipient_phone": self.phone_is_valid(phone),

            "reference": self.reference_is_valid(reference),
            "weight": self.weight_is_valid(weight),
            "other_email_1": self.email_is_valid(other_email_1),
            "other_email_2": self.email_is_valid(other_email_2),
            "other_email_3": self.email_is_valid(other_email_3),

            "street_line_one": self.required_text_is_valid(street_line_one),
            "street_line_two": True,
            "city": self.required_text_is_valid(city),
            "state_code": self.state_is_valid(state_code),
            "postal_code": self.required_text_is_valid(postal_code),

            "address_type": classification in (0, 1),
            "address_valid": self.address_is_confirmed(address_check_response)
        }

        return results


    def highlight_errors(self, results: dict) -> None:
        return


    def attempt_retrieve_rates(self):
        results = self.list_valid_inputs(
            self.recipient_name.get().strip(),
            self.recipient_email.get().strip(),
            self.recipient_phone.get().strip(),
            self.reference.get().strip(),
            self.weight.get().strip(),
            self.other_emails[0].get().strip(),
            self.other_emails[1].get().strip(),
            self.other_emails[2].get().strip(),
            self.street_line_one.get().strip(),
            self.street_line_two.get().strip(),
            self.city.get().strip(),
            self.state_code.get(),
            self.postal_code.get().strip(),
            self.address_is_commercial.get()
        )

        print(f"Results: {results}")
        if all(results.values()):
            self.retrieve_rates()
        else:
            self.highlight_errors(results)


    def retrieve_rates(self):
        return
        shipment_data = build_shipment_data(example_input)
        available_rates = populate_rates_options(self.sandbox_token, self.production_token, shipment_data, rates_API_config)

        cheapest_index = min(range(len(available_rates.options)), key=lambda index: available_rates.options[index].estimated_delivery_cost)

        self.selected_rate_index = tkinter.IntVar(value=cheapest_index)
        self.rate_row_frames = []

        SERVICE_WIDTH, DELIVERY_WIDTH, COST_WIDTH = 25, 25, 15

        header_frame = ttk.Frame(self.results_frame)
        header_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(header_frame, text="", width=3).grid(row=0, column=0, padx=5)
        ttk.Label(header_frame, text="Service", width=SERVICE_WIDTH).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(header_frame, text="Est. Delivery", width=DELIVERY_WIDTH).grid(row=0, column=2, padx=5, pady=2)
        ttk.Label(header_frame, text="Estimated Cost", width=COST_WIDTH).grid(row=0, column=3, padx=5, pady=2)

        for index, rate in enumerate(available_rates.options):
            row_frame = tkinter.Frame(self.results_frame, borderwidth=1, relief="flat")
            row_frame.grid(row=index+1, column=0, padx=2, pady=1, sticky="ew")

            self.rate_row_frames.append(row_frame)

            radio_button = ttk.Radiobutton(row_frame, variable=self.selected_rate_index, value=index, command=self.update_rate_selection)
            radio_button.grid(row=0, column=0, padx=5, pady=4)

            service_label = ttk.Label(row_frame, text=rate.service_type, width=SERVICE_WIDTH)
            service_label.grid(row=0, column=1, padx=5, pady=4, sticky="w")

            delivery_label = ttk.Label(row_frame, text=rate.estimated_delivery_time, width=DELIVERY_WIDTH)
            delivery_label.grid(row=0, column=2, padx=5, pady=4, sticky="w")

            cost_label = ttk.Label(row_frame, text=f"${rate.estimated_delivery_cost:.2f}", width=COST_WIDTH)
            cost_label.grid(row=0, column=3, padx=5, pady=4, sticky="w")

            for widget in (row_frame, service_label, delivery_label, cost_label):
                widget.bind("<Button-1>", lambda event, i=index: self.select_rate(i))

        self.update_rate_selection()


    def select_rate(self, index):
        self.selected_rate_index.set(index)
        self.update_rate_selection()


    def update_rate_selection(self):
        selected_index = self.selected_rate_index.get()

        for index, row_frame in enumerate(self.rate_row_frames):
            if index == selected_index:
                row_frame.config(relief="solid")
            else:
                row_frame.config(relief="flat")


    def create_final_shipment(self, pre_shipment_data, available_rates):
        final_shipment_data = select_from_rates_options(pre_shipment_data, available_rates, rates_API_config, ship_API_config)
        label = create_label(self.sandbox_token, self.production_token, final_shipment_data, ship_API_config)
        save_label(label, final_shipment_data.recipient.full_name)


    def run(self):
        self.root.mainloop()


    def run_load_shipment_test_cases(self):
        for num in test_requests:
            print(f"testing {num}:")
            self.load_shipment_details(test_case=num)
            self.attempt_retrieve_rates()