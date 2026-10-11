import tkinter
from tkinter import ttk
from scraper import Scraper
from parser import Parser
from tables import state_codes
from private import sandbox_api_key, sandbox_secret_key, production_api_key, production_secret_key
from api_settings import APIEnvironment, rates_API_config, ship_API_config, validation_API_config
from generator import get_access_token, build_shipment_data, attempt_address_completion, populate_rates_options, select_from_rates_options, create_label, save_label
from schema_classes import InputData
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

        self.rp_frame = ttk.Frame(self.root)
        self.rp_frame.grid(row=0, column=0, columnspan=2)

        self.rp_label = ttk.Label(self.rp_frame, text="RequestPortal number")
        self.rp_label.grid(row=0, column=0, padx=5, pady=5)

        validate_rp_number = lambda text: len(text) <= 6 and (text.isdigit() or text == "")
        validate_command = (self.root.register(validate_rp_number), "%P")

        self.rp_number_entry = ttk.Entry(self.rp_frame, width=10, validate="key", validatecommand=validate_command)
        self.rp_number_entry.grid(row=0, column=1, padx=5, pady=5)

        self.load_shipment_details_button = ttk.Button(self.rp_frame, text="Load Shipment Details", command=self.load_shipment_details)
        self.load_shipment_details_button.grid(row=0, column=2, pady=10, sticky="e")

        self.results_frame = ttk.Frame(self.root)
        self.results_frame.grid(row=1, column=0, columnspan=2, sticky="w")

        self.rp_scrape_status_frame = ttk.Frame(self.root)
        self.rp_scrape_status_frame.grid(row=1, column=1, sticky="w")

        self.create_preshipment_sections()

        self.retrieve_rates_button = ttk.Button(self.root, text="Retrieve Rates", command=self.attempt_retrieve_rates)
        self.retrieve_rates_button.grid(row=2, column=0, columnspan=2, pady=10)


    def create_preshipment_sections(self):
        left_column = ttk.Frame(self.results_frame)
        left_column.grid(row=0, column=0, sticky="nw", padx=(0, 8))

        recipient_frame = ttk.Frame(left_column, padding=8, relief="solid", borderwidth=1)
        recipient_frame.grid(row=0, column=0, sticky="ew")
        recipient_frame.columnconfigure(1, weight=1)

        self.recipient_header = tkinter.Label(recipient_frame, text="Recipient", anchor="w", padx=8, pady=5, bg="#e6e6e6", font=("Segoe UI", 11, "bold"))
        self.recipient_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.recipient_name = tkinter.StringVar(value="")
        self.recipient_email = tkinter.StringVar(value="")
        self.recipient_phone = tkinter.StringVar(value="")

        fields = [
            ("Name", self.recipient_name),
            ("Email", self.recipient_email),
            ("Phone", self.recipient_phone),
        ]

        for row, (field_name, field_value) in enumerate(fields):
            ttk.Label(recipient_frame, text=field_name).grid(row=row+1, column=0, sticky="w", padx=5, pady=4)
            ttk.Entry(recipient_frame, textvariable=field_value, width=55).grid(row=row+1, column=1, sticky="ew", padx=5, pady=4)

        other_frame = ttk.Frame(left_column, padding=8, relief="solid", borderwidth=1)
        other_frame.grid(row=1, column=0, sticky="ew")
        other_frame.columnconfigure(1, weight=1)

        self.other_header = tkinter.Label(other_frame, text="Other", anchor="w", padx=8, pady=5, bg="#e6e6e6", font=("Segoe UI", 11, "bold"))
        self.other_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.other_emails = tkinter.StringVar(value="")
        self.reference = tkinter.StringVar(value="")
        self.weight = tkinter.StringVar(value="")

        fields = [
            ("Other Email Recipients", self.other_emails),
            ("Reference #", self.reference),
            ("Weight (lbs)", self.weight),
        ]

        for row, (field_name, field_value) in enumerate(fields):
            ttk.Label(other_frame, text=field_name).grid(row=row+1, column=0, sticky="w", padx=5, pady=4)
            ttk.Entry(other_frame, textvariable=field_value, width=55).grid(row=row+1, column=1, sticky="ew", padx=5, pady=4)


        address_frame = ttk.Frame(self.results_frame, padding=8, relief="solid", borderwidth=1)
        address_frame.grid(row=0, column=1, sticky="nws")
        address_frame.columnconfigure(1, weight=1)

        self.address_header = tkinter.Label(address_frame, text="Address", anchor="w", padx=8, pady=5, bg="#e6e6e6", font=("Segoe UI", 11, "bold"))
        self.address_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.street_line_one = tkinter.StringVar(value="")
        self.street_line_two = tkinter.StringVar(value="")
        self.city = tkinter.StringVar(value="")
        self.state_code = tkinter.StringVar(value="")
        self.postal_code = tkinter.StringVar(value="")
        self.country_code = tkinter.StringVar(value="US")
        self.address_is_commercial = tkinter.IntVar(value=0)

        ttk.Label(address_frame, text="Street line 1").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.street_line_one, width=55).grid(row=1, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(address_frame, text="Street line 2").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.street_line_two, width=55).grid(row=2, column=1, sticky="ew", padx=5, pady=4)
        ttk.Label(address_frame, text="City").grid(row=3, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.city, width=55).grid(row=3, column=1, sticky="w", padx=5, pady=4)
        ttk.Label(address_frame, text="State").grid(row=4, column=0, sticky="w", padx=5, pady=4)
        ttk.Combobox(address_frame, textvariable=self.state_code, values=state_codes, state="readonly", width=6).grid(row=4, column=1, sticky="w", padx=5, pady=4)
        ttk.Label(address_frame, text="ZIP").grid(row=5, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.postal_code, width=6).grid(row=5, column=1, sticky="w", padx=5, pady=4)
        ttk.Label(address_frame, text="Country").grid(row=6, column=0, sticky="w", padx=5, pady=4)
        ttk.Entry(address_frame, textvariable=self.country_code, width=6, state="disabled").grid(row=6, column=1, sticky="w", padx=5, pady=4)
        ttk.Label(address_frame, text="Residential/Commercial address").grid(row=7, column=0, sticky="w", padx=5, pady=4)
        residential_radiobutton = ttk.Radiobutton(address_frame, variable=self.address_is_commercial, text="Residential", value=0)
        residential_radiobutton.grid(row=7, column=1, sticky="w", padx=5, pady=4)
        commercial_radiobutton = ttk.Radiobutton(address_frame, variable=self.address_is_commercial, text="Commercial", value=1)
        commercial_radiobutton.grid(row=8, column=1, sticky="w", padx=5, pady=4)


    @staticmethod
    def field_is_valid(field) -> bool:
        pass


    def validate_shipment(self):
        self.field_is_valid(self.street_line_one.get())


    def load_shipment_details(self):
        request_number = self.rp_number_entry.get().strip()
        url = f"https://requestportal.americansystems.com/Request/Request?id={request_number}"

        if not self.scraper.request_number_is_feasible(request_number):
            ttk.Label(self.rp_frame, text="Invalid request. Please provide a valid RequestPortal request number.").grid(row=0, column=4, sticky="w", padx=5, pady=2)
            return

        if not self.scraper.session_is_authenticated(url):
            self.scraper.authenticate_session(url)

        if not self.scraper.request_is_valid(url):
            ttk.Label(self.rp_frame, text="Invalid request. Please provide a valid RequestPortal request number.").grid(row=0, column=4, sticky="w", padx=5, pady=2)
            return

        rp_dict = self.scraper.scrape_request(url).model_dump()

        self.display_preshipment_details(rp_dict)


    def display_preshipment_details(self, rp_dict):
        name, email = self.parser.parse_names(rp_dict)
        phone = self.parser.parse_contact_numbers(rp_dict)

        raw_address = self.parser.parse_address(rp_dict)
        corrected_address = self.correct_address(raw_address)
        print(corrected_address)

        address = raw_address
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

        self.other_emails.set(";".join(other_emails))
        self.reference.set(value=reference)
        self.weight.set(value=str(weight))


    def correct_address(self, address):
        response = attempt_address_completion(self.sandbox_token, self.production_token, address, validation_API_config)
        x = response.json()["output"]["resolvedAddresses"][0]
        y = json.dumps(x, indent=4)
        print(y)


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
            other_emails_to_notify=self.other_emails.get().split(";"),
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
