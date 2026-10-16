import tkinter
from tkinter import ttk
from scraper import Scraper
from parser import Parser
from tables import state_codes
from private import sandbox_api_key, sandbox_secret_key, production_api_key, production_secret_key, rp_url_prefix
from api_settings import APIEnvironment, rates_API_config, ship_API_config, validation_API_config
from api_requests import get_access_token, build_shipment_data, attempt_address_completion, populate_rates_options, select_from_rates_options, create_label, save_label
from schema_classes import InputData, Address
from input import example_input
import json


class GUI:
    def __init__(self):
        self.sandbox_token = get_access_token(sandbox_api_key, sandbox_secret_key, APIEnvironment.SANDBOX)
        self.production_token = get_access_token(production_api_key, production_secret_key, APIEnvironment.PRODUCTION)

        self.scraper = Scraper()
        self.parser = Parser(self)

        self.root = tkinter.Tk()
        self.root.title("FedEx Shipping Label Generator")

        self.configure_styles()

        self.main_frame = ttk.Frame(self.root, padding=(22, 18, 22, 12))
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        tkinter.Label(title_frame, text="Fe", bg="#623a9d", fg="white", font=("Segoe UI", 14, "bold"), padx=9, pady=6).pack(side="left", padx=(0, 12))
        ttk.Label(title_frame, text="FedEx Shipping Label Generator", font=("Segoe UI", 17, "bold")).pack(side="left")

        self.rp_outer_frame = ttk.Frame(self.main_frame, padding=4, style="Card.TFrame")
        self.rp_outer_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.rp_outer_frame.columnconfigure(0, weight=1)

        self.rp_label = tkinter.Label(self.rp_outer_frame, text="Request Portal", anchor="w", padx=12, pady=9, bg=self.colors["muted"], fg=self.colors["ink"], font=("Segoe UI", 12, "bold"))
        self.rp_label.grid(row=0, column=0, sticky="ew", pady=(0, 12))

        self.rp_frame = ttk.Frame(self.rp_outer_frame, style="CardInterior.TFrame")
        self.rp_frame.grid(row=1, column=0)
        ttk.Label(self.rp_frame, text="RP Number", style="Card.TLabel").pack(side="left", padx=(0, 12))

        validate_command = (self.root.register(self.validate_rp_number), "%P")

        self.rp_number_entry = ttk.Entry(self.rp_frame, width=17, validate="key", validatecommand=validate_command)
        self.rp_number_entry.pack(side="left")
        self.rp_number_entry.bind("<<Paste>>", self.handle_rp_paste)

        self.rp_paste_button = ttk.Button(self.rp_frame, text="Paste", command=self.handle_rp_paste)
        self.rp_paste_button.pack(side="left", padx=(2, 12))

        self.load_shipment_details_button = ttk.Button(self.rp_frame, text="Lookup", style="Primary.TButton", command=self.load_shipment_details)
        self.load_shipment_details_button.pack(side="left")

        self.rp_number_entry.bind("<Return>", lambda event: self.load_shipment_details_button.invoke())

        self.rp_error_label = ttk.Label(self.rp_outer_frame, text="", style="Error.TLabel")
        self.rp_error_label.grid(row=2, column=0, pady=(5, 0))

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
            "primary": "#4878b7"
        }
        c = self.colors
        self.root.configure(bg=c["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")

        style.configure("TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["surface"], relief="solid", borderwidth=1, bordercolor=c["border"])
        style.configure("CardInterior.TFrame", background=c["surface"], borderwidth=0, relief="flat")
        style.configure("TLabel", background=c["bg"], foreground=c["ink"], font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=c["surface"], foreground=c["ink"], font=("Segoe UI", 10))
        style.configure("Hint.TLabel", background=c["surface"], foreground=c["subtitle"], font=("Segoe UI", 9))
        style.configure("Error.TLabel", background=c["surface"], foreground="#b42318", font=("Segoe UI", 10))

        style.configure("TEntry", fieldbackground="white", bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], relief="flat", borderwidth=1, padding=4, font=("Segoe UI", 10))
        style.map("TEntry", bordercolor=[("focus", "#80a7d6")])

        style.configure("TCombobox", fieldbackground="white", background="eaf0f8", bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], padding=4, font=("Segoe UI", 10))
        style.map("TCombobox", fieldbackground=[("readonly", "white")])

        style.configure("TButton", background="#e9f0f8", foreground=c["ink"], borderwidth=1, relief="flat", bordercolor=c["border"], padding=(10, 5), font=("Segoe UI", 10))
        style.map("TButton", background=[("active", "#d7e6f5")])

        style.configure("Primary.TButton", background=c["primary"], foreground="white", bordercolor=c["primary"], padding=(14, 5), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#3968a5")], foreground=[("active", "white")])

        style.configure("Card.TRadiobutton", background="white", foreground=c["ink"], font=("Segoe UI", 10))


    def validate_rp_number(self, text):
        return len(text) <= 6 and (text.isascii() and text.isdigit() or text == "")


    def extract_rp_number(self, text):
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

        fields = [
            ("Name", self.recipient_name),
            ("Email", self.recipient_email),
            ("Phone", self.recipient_phone),
        ]

        for row, (field_name, field_value) in enumerate(fields):
            ttk.Label(recipient_frame, style="Card.TLabel", text=field_name).grid(row=row+1, column=0, sticky="w", padx=5, pady=3)
            ttk.Entry(recipient_frame, textvariable=field_value, width=36).grid(row=row+1, column=1, sticky="ew", padx=5, pady=3)

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

        for row, (field_name, field_value) in enumerate(fields):
            ttk.Label(other_frame, style="Card.TLabel", text=field_name).grid(row=row+1, column=0, sticky="w", padx=5, pady=3)
            ttk.Entry(other_frame, textvariable=field_value, width=36).grid(row=row+1, column=1, sticky="ew", padx=5, pady=3)

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
        self.country_code = tkinter.StringVar(value="US")
        self.address_is_commercial = tkinter.IntVar(value=-1)

        ttk.Label(address_frame, style="Card.TLabel", text="Street line 1").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.street_line_one, width=36).grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(address_frame, style="Card.TLabel", text="Street line 2").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.street_line_two, width=36).grid(row=2, column=1, sticky="ew", padx=5, pady=4)

        bottom_frame = ttk.Frame(address_frame, style="CardInterior.TFrame")
        bottom_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=8)
        bottom_frame.columnconfigure(0, weight=1, uniform="bottom")
        bottom_frame.columnconfigure(1, weight=1, uniform="bottom")

        type_frame = ttk.Frame(bottom_frame, style="CardInterior.TFrame")
        type_frame.grid(row=0, column=0, sticky="w")

        ttk.Label(type_frame, style="Card.TLabel", text="Residential").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Radiobutton(type_frame, style="Card.TRadiobutton", variable=self.address_is_commercial, value=0).grid(row=0, column=1, sticky="w", padx=8)

        ttk.Label(type_frame, style="Card.TLabel", text="Commercial").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Radiobutton(type_frame, style="Card.TRadiobutton", variable=self.address_is_commercial, value=1).grid(row=1, column=1, sticky="w", padx=8)

        location_frame = ttk.Frame(bottom_frame, style="CardInterior.TFrame")
        location_frame.grid(row=0, column=1, sticky="ew")
        location_frame.columnconfigure(0, weight=1, uniform="location")
        location_frame.columnconfigure(1, weight=1, uniform="location")

        ttk.Label(location_frame, style="Card.TLabel", text="City").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Entry(location_frame, textvariable=self.city).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2,10))

        ttk.Label(location_frame, style="Card.TLabel", text="State").grid(row=2, column=0, sticky="w")
        ttk.Combobox(location_frame, textvariable=self.state_code, values=state_codes, state="readonly", width=6).grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=2)

        ttk.Label(location_frame, style="Card.TLabel", text="ZIP").grid(row=2, column=1, sticky="w", padx=(5, 0))
        ttk.Entry(location_frame, textvariable=self.postal_code, width=10).grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=2)

        ttk.Label(address_frame, text="Country: US", style="Hint.TLabel").grid(row=4, column=0, columnspan=2, sticky="w", pady=(22, 2))


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


    @staticmethod
    def field_is_valid(field) -> bool:
        pass


    def validate_shipment(self):
        self.field_is_valid(self.street_line_one.get())


    def load_shipment_details(self):
        request_number = self.rp_number_entry.get().strip()
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

        self.display_preshipment_details(rp_dict)


    def display_preshipment_details(self, rp_dict):
        self.clear_preshipment_sections()
        name, email = self.parser.parse_names(rp_dict)
        phone = self.parser.parse_contact_numbers(rp_dict)

        raw_address = self.parser.parse_address(rp_dict)
        address, classification = self.correct_address(raw_address)

        if classification and classification == "RESIDENTIAL" or classification == "UNKNOWN":
            address_is_commercial = False
        else:
            address_is_commercial = True

        other_emails = self.parser.parse_others_to_notify(rp_dict)
        reference = "CAS-35251_56262_802331"
        weight = 10

        self.recipient_name.set(name)
        self.recipient_email.set(email)
        self.recipient_phone.set(phone)

        self.street_line_one.set(address.street_line_one)
        self.street_line_two.set(address.street_line_two)
        self.city.set(value=address.city)
        self.state_code.set(value=address.state_code)
        self.postal_code.set(value=address.postal_code)
        self.country_code.set(value=address.country_code)
        self.address_is_commercial.set(value=address_is_commercial)

        self.reference.set(value=reference)
        self.weight.set(value=str(weight))

        for i in range(min(len(other_emails), 3)):
            self.other_emails[i].set(other_emails[i])


    def correct_address(self, address):
        response = attempt_address_completion(self.sandbox_token, self.production_token, address, validation_API_config).json()["output"]["resolvedAddresses"][0]
        pretty_json = json.dumps(response, indent=4)
        print(pretty_json)

        street_lines = response.get("streetLinesToken")
        if street_lines:
            street_line_one = street_lines[0]
            if len(street_lines) == 1:
                street_line_two = ""
            else:
                street_line_two = street_lines[1]
        else:
            street_line_one, street_line_two = "", ""

        city = response.get("city") or ""
        state_code = response.get("stateOrProvinceCode") or ""
        postal_code = response.get("postalCode") or ""
        country_code = response.get("countryCode") or ""
        address_classification = response.get("classification") or ""

        return Address(
            street_line_one=street_line_one,
            street_line_two=street_line_two,
            city=city,
            state_code=state_code,
            postal_code=postal_code,
            country_code=country_code
        ), address_classification


    def build_shipment(self):
        shipment = InputData(
            street_line_one=self.street_line_one.get(),
            street_line_two=self.street_line_two.get(),
            city=self.city.get(),
            state_code=self.state_code.get(),
            postal_code=self.postal_code.get(),
            country_code=self.country_code.get(),
            name=self.recipient_name.get(),
            email_address=self.recipient_email.get(),
            phone_number=self.recipient_phone.get(),
            address_is_commercial=bool(self.address_is_commercial.get()),
            reference=self.reference.get(),
            shipment_weight=int(self.weight.get()),
            other_emails_to_notify=[email.get().strip() for email in self.other_emails if email.get().strip()],
        )

        return shipment


    def input_is_valid(self) -> bool:
        pass


    def highlight_errors(self) -> None:
        pass


    def attempt_retrieve_rates(self):
        if self.input_is_valid():
            shipment = self.build_shipment()
            pass
        else:
            self.highlight_errors()


    def retrieve_rates(self):
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
