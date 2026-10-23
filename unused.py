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


def finalize_shipment_and_save_label(self, pre_shipment_data, available_rates):
    final_shipment_data = select_from_rates_options(pre_shipment_data, available_rates, rates_API_config, ship_API_config)
    label = create_label(self.sandbox_token, self.production_token, final_shipment_data, ship_API_config)
    save_label(label, final_shipment_data.recipient.full_name)




def select_from_rates_options(shipment, available_rates, rates_environment, ship_environment):
    if rates_environment == APIEnvironment.SANDBOX or ship_environment == APIEnvironment.SANDBOX:
        shipment.selected_service_type = shipment.default_service_type
    else:
        shipment.selected_service_type = shipment.default_service_type
    return shipment


def save_label(response_data, label_recipient_name):
    tracking_number = response_data["output"]["transactionShipments"][0]["masterTrackingNumber"]
    encoded_label = response_data["output"]["transactionShipments"][0]["pieceResponses"][0]["packageDocuments"][0][
        "encodedLabel"]
    label_bytes = base64.b64decode(encoded_label)
    output_directory = Path(__file__).parent / "output_labels"
    output_directory.mkdir(exist_ok=True)
    label_path = output_directory / f"{label_recipient_name}_{tracking_number}.pdf"
    label_path.write_bytes(label_bytes)


example_input = InputData(
    street_line_one="308 Negra Arroyo Lane",
    street_line_two="Apt 737",
    city="Albuquerque",
    state_code="NM",
    postal_code="87104",
    country_code="US",
    name="Walter White",
    email_address="alborz796@gmail.com",
    phone_number="505-503-4455",
    address_is_commercial=False,
    reference="REFNUM",
    shipment_weight=10,
    other_emails_to_notify=["alborzzzz@yahoo.com"]
)