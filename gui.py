import tkinter
from tkinter import ttk
from shipment_processor import Processor
from private import rp_url_prefix
from PIL import Image, ImageTk
from pathlib import Path
from tables import state_codes


class GUI:
    def __init__(self):

        self.processor = Processor()

        self.root = tkinter.Tk()
        self.root.title("FedEx Shipping Label Generator")

        self.main_font = "Segoe UI"
        self.secondary_font = "Segoe UI Symbol"

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
        ttk.Label(header_inner, text="Shipping Label Generator", font=(self.main_font, 18, "bold")).pack(side="left")

        self.rp_outer_frame = ttk.Frame(self.main_frame, padding=(12, 10), style="Card.TFrame")
        self.rp_outer_frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        self.rp_outer_frame.columnconfigure(0, weight=1)

        self.rp_frame = ttk.Frame(self.rp_outer_frame, style="CardInterior.TFrame")
        self.rp_frame.grid(row=0, column=0)

        ttk.Label(self.rp_frame, text="RequestPortal Number", style="Card.TLabel", font=(self.main_font, 15, "bold")).pack(pady=(0, 5))

        rp_controls_frame = ttk.Frame(self.rp_frame, style="CardInterior.TFrame")
        rp_controls_frame.pack()

        validate_command = (self.root.register(self.validate_rp_number_entry), "%P")

        self.rp_number_entry = ttk.Entry(rp_controls_frame, width=26, validate="key", validatecommand=validate_command)
        self.rp_number_entry.pack(side="left")
        self.rp_number_entry.bind("<<Paste>>", self.handle_rp_paste)

        self.rp_paste_button = ttk.Button(rp_controls_frame, text="⧉", width=2, style="Icon.TButton", command=self.handle_rp_paste)
        self.rp_paste_button.pack(side="left", padx=(3, 10))

        self.lookup_button = ttk.Button(rp_controls_frame, text="Lookup", style="Primary.TButton", command=self.lookup_and_display_preshipment_details)
        self.lookup_button.pack(side="left")

        self.rp_number_entry.bind("<Return>", lambda event: self.lookup_button.invoke())

        self.rp_error_label = ttk.Label(self.rp_outer_frame, text="", style="Error.TLabel")
        self.rp_error_label.grid(row=1, column=0, pady=(5, 0))

        self.results_frame = ttk.Frame(self.main_frame)
        self.results_frame.grid(row=2, column=0, sticky="nsew")
        self.results_frame.columnconfigure(0, weight=1, uniform="form")
        self.results_frame.columnconfigure(1, weight=1, uniform="form")

        self.recipient_name = tkinter.StringVar(value=self.processor.preshipment_details["recipient_name"])
        self.recipient_email = tkinter.StringVar(value=self.processor.preshipment_details["recipient_email"])
        self.recipient_phone = tkinter.StringVar(value=self.processor.preshipment_details["recipient_phone"])

        self.street_line_one = tkinter.StringVar(value=self.processor.preshipment_details["street_line_one"])
        self.street_line_two = tkinter.StringVar(value=self.processor.preshipment_details["street_line_two"])
        self.city = tkinter.StringVar(value=self.processor.preshipment_details["city"])
        self.state_code = tkinter.StringVar(value=self.processor.preshipment_details["state_code"])
        self.postal_code = tkinter.StringVar(value=self.processor.preshipment_details["postal_code"])
        self.address_is_commercial = tkinter.IntVar(value=self.processor.preshipment_details["address_is_commercial"])

        self.reference = tkinter.StringVar(value=self.processor.preshipment_details["reference"])
        self.weight = tkinter.StringVar(value=self.processor.preshipment_details["weight"])
        self.other_emails = [
        tkinter.StringVar(value=self.processor.preshipment_details["other_email_1"]),
        tkinter.StringVar(value=self.processor.preshipment_details["other_email_2"]),
        tkinter.StringVar(value=self.processor.preshipment_details["other_email_3"]),
            ]

        self.create_preshipment_sections()

        self._updating_address = False

        address_variables = (
            self.street_line_one,
            self.street_line_two,
            self.city,
            self.state_code,
            self.postal_code,
            self.address_is_commercial
        )

        for variable in address_variables:
            variable.trace_add("write", self.on_address_changed)

        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=3, column=0, pady=(8, 0))

        self.clear_shipment_details_button = ttk.Button(action_frame, text="Clear All", command=self.clear_preshipment_widgets)
        self.clear_shipment_details_button.pack(side="left", padx=7)

        self.retrieve_rates_button = ttk.Button(action_frame, text="Retrieve Rates", style="Primary.TButton", state="disabled", command=self.attempt_retrieve_rates)
        self.retrieve_rates_button.pack(side="left", padx=7)

        lock_image = Image.open(Path(__file__).parent / "lock.png").convert("RGBA")
        lock_image = lock_image.resize((18, 18), Image.Resampling.LANCZOS)
        self.lock_icon = ImageTk.PhotoImage(lock_image)

        check_image = Image.open(Path(__file__).parent / "circle-check.png").convert("RGBA")
        check_image = check_image.resize((18, 18), Image.Resampling.LANCZOS)
        self.check_icon = ImageTk.PhotoImage(check_image)

        self.retrieve_rates_hint = ttk.Label(action_frame, text="Select address", image=self.lock_icon, compound="left", style="ActionHint.TLabel")
        self.retrieve_rates_hint.pack(side="left", padx=(6, 0))


    def configure_styles(self):
        self.colors = {
            "bg": "#eff3f9",
            "surface": "#ffffff",
            "muted": "#e9eff7",
            "border": "#ccd8e6",
            "ink": "#263449",
            "subtitle": "#67798f",
            "success": "#188038",

            "suggestion_bg": "#f3f7fd",
            "suggestion_border": "#b8cce7",
            "suggestion_field": "#e8f0fa",
            "suggestion_button": "#dceafe",

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

        style.configure("Required.TLabel", background=c["surface"], foreground=c["asterisk"], font=(self.main_font, 10, "bold"))
        style.configure("TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["surface"], relief="solid", borderwidth=1, bordercolor=c["border"])
        style.configure("CardInterior.TFrame", background=c["surface"], borderwidth=0, relief="flat")
        style.configure("TLabel", background=c["bg"], foreground=c["ink"], font=(self.main_font, 10))
        style.configure("Card.TLabel", background=c["surface"], foreground=c["ink"], font=(self.main_font, 10))
        style.configure("Hint.TLabel", background=c["surface"], foreground=c["subtitle"], font=(self.main_font, 9))
        style.configure("Error.TLabel", background=c["surface"], foreground=c["hover"], font=(self.main_font, 10))
        style.configure("ActionHint.TLabel", background=c["bg"], foreground=c["subtitle"], font=(self.main_font, 9))
        style.configure("ActionHintSuccess.TLabel", background=c["bg"], foreground=c["success"], font=(self.main_font, 9, "bold"))
        style.configure("TEntry", fieldbackground="white", bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], relief="flat", borderwidth=1, padding=4, font=(self.main_font, 10))
        style.map("TEntry", bordercolor=[("focus", c["input_focus"])])
        style.configure("TCombobox", fieldbackground="white", background=c["combobox"], bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], padding=4, font=(self.main_font, 10))
        style.map("TCombobox", fieldbackground=[("readonly", "white")])
        style.configure("TButton", background=c["button"], foreground=c["ink"], borderwidth=1, relief="flat", bordercolor=c["border"], padding=(10, 5), font=(self.main_font, 10))
        style.map("TButton", background=[("active", c["button_hover"])])
        style.configure("Icon.TButton", background=c["button"], foreground=c["ink"], bordercolor=c["border"], borderwidth=1, relief="flat", padding=(4, 3), font=(self.secondary_font, 11))
        style.map("Icon.TButton", background=[("active", c["button_hover"])])
        style.configure("Primary.TButton", background=c["primary"], foreground="white", bordercolor=c["primary"], padding=(14, 5), font=(self.main_font, 11, "bold"))
        style.map("Primary.TButton", background=[("disabled", c["button"]), ("active", c["primary_hover"])], foreground=[("disabled", c["subtitle"]), ("active", "white")], bordercolor=[("disabled", c["border"])])
        style.configure("Card.TRadiobutton", background="white", foreground=c["ink"], font=(self.main_font, 10))
        style.configure("Compact.TButton", background=c["primary"], foreground="white", padding=(8, 2), font=(self.main_font, 9))
        style.map("Compact.TButton", background=[("disabled", c["button"]), ("active", c["primary_hover"])],
                  foreground=[("disabled", c["subtitle"]), ("active", "white")],
                  bordercolor=[("disabled", c["border"])])
        style.configure("CompactSelected.TButton", background=c["primary"], foreground="white", bordercolor=c["primary"], padding=(8, 2), font=(self.main_font, 9, "bold"))
        style.map("CompactSelected.TButton", background=[("active", c["primary_hover"])], foreground=[("active", "white")])
        style.configure("CompactPrimary.TButton", background=c["primary"], foreground="white", bordercolor=c["primary"], padding=(8, 2), font=(self.main_font, 9, "bold"))
        style.map("CompactPrimary.TButton", background=[("active", c["primary_hover"])], foreground=[("active", "white")])
        style.configure("SuggestionCard.TFrame", background=c["suggestion_bg"], bordercolor=c["suggestion_border"], borderwidth=1, relief="solid")
        style.configure("SuggestionBody.TFrame", background=c["suggestion_bg"])
        style.configure("Suggestion.TLabel", background=c["suggestion_bg"], foreground=c["ink"], font=(self.main_font, 9, "bold"))
        style.configure("SuggestionNote.TLabel", background=c["suggestion_bg"], foreground=c["subtitle"], font=(self.main_font, 9))
        style.configure("Suggestion.TEntry", fieldbackground=c["suggestion_field"], bordercolor=c["suggestion_border"], foreground=c["ink"], padding=3)
        style.map("Suggestion.TEntry", fieldbackground=[("readonly", c["suggestion_field"])], foreground=[("readonly", c["ink"])])
        style.configure("SuggestAction.TButton", background=c["suggestion_button"], foreground=c["primary"], bordercolor=c["suggestion_border"], borderwidth=1, padding=(12, 4), font=(self.main_font, 10, "bold"))
        style.map("SuggestAction.TButton", background=[("active", c["button_hover"])], foreground=[("active", c["primary"])])


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

        self.recipient_header = tkinter.Label(recipient_frame, text="Recipient", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=(self.main_font, 12, "bold"))
        self.recipient_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

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

        self.other_header = tkinter.Label(other_frame, text="Other", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=(self.main_font, 12, "bold"))
        self.other_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

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

        self.address_header = tkinter.Label(address_frame, text="Address", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=(self.main_font, 12, "bold"))
        self.address_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

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

        address_frame.rowconfigure(4, weight=1)

        self.suggestion_panel = ttk.Frame(address_frame, style="SuggestionCard.TFrame", padding=(8, 6))
        self.suggestion_panel.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 2))
        self.suggestion_panel.columnconfigure(0, weight=1)

        # View 1
        self.suggestion_request_view = ttk.Frame(self.suggestion_panel, style="SuggestionBody.TFrame")
        self.suggestion_request_view.grid(row=0, column=0, sticky="nsew")
        self.suggestion_request_view.columnconfigure(0, weight=1)
        self.suggestion_request_view.rowconfigure(0, weight=1)

        pin_image = Image.open(Path(__file__).parent / "map-pin.png").convert("RGBA")
        pin_image = pin_image.resize((18, 18), Image.Resampling.LANCZOS)
        self.pin_icon = ImageTk.PhotoImage(pin_image)

        self.suggest_address_button = ttk.Button(self.suggestion_request_view, text="Validate Address", image=self.pin_icon, compound="left", style="SuggestAction.TButton", command=self.suggest_address)
        self.suggest_address_button.grid(row=0, column=0)

#        ttk.Label(self.suggestion_request_view, text="Choose an address version to enable rates", style="SuggestionNote.TLabel").grid(row=1, column=0, pady=(2, 0))

        # View 2
        self.suggestion_result_view = ttk.Frame(self.suggestion_panel, style="SuggestionBody.TFrame")
        self.suggestion_result_view.grid(row=0, column=0, sticky="nsew")
        self.suggestion_result_view.columnconfigure(0, weight=1)

        ttk.Label(self.suggestion_result_view, text="Address Review - Choose an Option", style="Suggestion.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 3))

        self.suggested_address_display = tkinter.StringVar(value="")
        self.suggested_address_entry = ttk.Entry(self.suggestion_result_view, textvariable=self.suggested_address_display, state="readonly", style="Suggestion.TEntry", takefocus=False)
        self.suggested_address_entry.grid(row=1, column=0, sticky="ew")

        self.no_suggestion_label = ttk.Label(self.suggestion_result_view, text="FedEx could not confirm a suggested address.", style="SuggestionNote.TLabel", padding=(6, 5))
        self.no_suggestion_label.grid(row=1, column=0, sticky="ew")

        choice_frame = ttk.Frame(self.suggestion_result_view, style="SuggestionBody.TFrame")
        choice_frame.grid(row=2, column=0, pady=(5, 0))

        self.use_suggested_button = ttk.Button(choice_frame, text="Use Suggested Address", style="Compact.TButton", state="disabled", command=self.use_suggested_address)
        self.use_suggested_button.pack(side="left", padx=(0, 5))

        self.use_entered_button = ttk.Button(choice_frame, text="Use Address As Entered", style="Compact.TButton", state="disabled", command=self.use_address_as_entered)
        self.use_entered_button.pack(side="left", padx=(5, 0))

        self.suggestion_request_view.tkraise()


    def on_address_changed(self, *args):
        if self._updating_address:
            return

        self.show_suggestion_request_view()


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
        try:
            pasted_text = self.root.clipboard_get().strip()
        except tkinter.TclError:
            self.rp_error_label.configure(
                text="Clipboard is empty or contains no text."
            )
            return "break"

        request_number = self.extract_rp_number(pasted_text)

        if request_number is not None:
            self.rp_number_entry.delete(0, tkinter.END)
            self.rp_number_entry.insert(0, request_number)
            self.rp_error_label.configure(text="")
            return "break"


    def show_suggestion_request_view(self):
        self.suggest_address_button.configure(state="normal")

        self.use_suggested_button.configure(state="disabled", style="Compact.TButton")
        self.use_entered_button.configure(state="disabled", style="Compact.TButton")

        self.retrieve_rates_button.configure(state="disabled")
        self.retrieve_rates_hint.configure(text="Select address", image=self.lock_icon, style="ActionHint.TLabel")

        self.suggested_address_display.set("")
        self.suggestion_request_view.tkraise()


    def show_suggestion_result_view(self, confirmed: bool):
        self.suggest_address_button.configure(state="disabled")

        if confirmed:
            self.suggested_address_entry.tkraise()
            self.use_suggested_button.configure(state="normal")
        else:
            self.no_suggestion_label.tkraise()
            self.use_suggested_button.configure(state="disabled")

        self.use_entered_button.configure(state="normal")

        self.suggestion_result_view.tkraise()


    def clear_preshipment_widgets(self):
        self.processor.clear_preshipment_details()
        self.sync_preshipment_details_from_processor_to_gui()


    def lookup_and_display_preshipment_details(self):
        self.clear_preshipment_widgets()

        request_number = self.rp_number_entry.get().strip()
        lookup_success = self.processor.load_preshipment_details_from_scraper(request_number)

        if lookup_success:
            self.rp_error_label.config(text="")
            self.sync_preshipment_details_from_processor_to_gui()
        else:
            self.rp_error_label.config(text="Invalid RequestPortal number.")


    def sync_preshipment_details_from_processor_to_gui(self):
        self.recipient_name.set(self.processor.preshipment_details["recipient_name"])
        self.recipient_email.set(self.processor.preshipment_details["recipient_email"])
        self.recipient_phone.set(self.processor.preshipment_details["recipient_phone"])

        self.street_line_one.set(self.processor.preshipment_details["street_line_one"])
        self.street_line_two.set(self.processor.preshipment_details["street_line_two"])
        self.city.set(self.processor.preshipment_details["city"])
        self.state_code.set(self.processor.preshipment_details["state_code"])
        self.postal_code.set(self.processor.preshipment_details["postal_code"])
        self.address_is_commercial.set(self.processor.preshipment_details["address_is_commercial"])

        self.reference.set(self.processor.preshipment_details["reference"])
        self.weight.set(self.processor.preshipment_details["weight"])
        self.other_emails[0].set(self.processor.preshipment_details["other_email_1"])
        self.other_emails[1].set(self.processor.preshipment_details["other_email_2"])
        self.other_emails[2].set(self.processor.preshipment_details["other_email_3"])


    def sync_preshipment_details_from_gui_to_processor(self):
        details = {
            "recipient_name": self.recipient_name.get().strip(),
            "recipient_email": self.recipient_email.get().strip(),
            "recipient_phone": self.recipient_phone.get().strip(),

            "street_line_one": self.street_line_one.get().strip(),
            "street_line_two": self.street_line_two.get().strip(),
            "city": self.city.get().strip(),
            "state_code": self.state_code.get(),
            "postal_code": self.postal_code.get().strip(),
            "address_is_commercial": self.address_is_commercial.get(),

            "reference": self.reference.get().strip(),
            "weight": self.weight.get().strip(),
            "other_email_1": self.other_emails[0].get().strip(),
            "other_email_2": self.other_emails[1].get().strip(),
            "other_email_3": self.other_emails[2].get().strip(),
        }

        self.processor.preshipment_details.update(details)


    def attempt_retrieve_rates(self):
        self.sync_preshipment_details_from_gui_to_processor()

        results = self.processor.is_preshipment_valid()

        if all(results.values()):
            rates = self.processor.retrieve_rates()
            print(rates)
#            self.display_rates(rates)
#            self.lock_preshipment_widgets()
#            self.switch_to_create_label_buttons()
        else:
            self.highlight_errors(results)


    def highlight_errors(self, results: dict) -> None:
        return


    def suggest_address(self):
        self.sync_preshipment_details_from_gui_to_processor()
        confirmed, address, is_commercial = self.processor.get_suggested_address()

        if confirmed is True:
            self.processor.set_suggested_address(address, is_commercial)
            self.display_suggested_address()
        else:
            self.suggested_address_display.set("")

        self.show_suggestion_result_view(confirmed=confirmed is True)


    def display_suggested_address(self):
        address = self.processor.suggested_address

        if not address["street_line_two"]:
            text = f"{address["street_line_one"]}, {address["city"]}, {address["state_code"]} {address["postal_code"]}"
        else:
            text = f"{address["street_line_one"]} {address["street_line_two"]}, {address["city"]}, {address["state_code"]} {address["postal_code"]}"

        self.suggested_address_display.set(text)


    def indicate_address_choice(self, choice: str):
        self.use_suggested_button.configure(style="CompactSelected.TButton" if choice == "suggested" else "Compact.TButton")
        self.use_entered_button.configure(style="CompactSelected.TButton" if choice == "entered" else "Compact.TButton")
        self.retrieve_rates_button.configure(state="normal")
        self.retrieve_rates_hint.configure(text="Address selected", image=self.check_icon, compound="left", style="ActionHintSuccess.TLabel")


    def use_suggested_address(self):
        self.processor.suggested_address_to_preshipment_address()

        self._updating_address = True
        self.sync_preshipment_details_from_processor_to_gui()
        self._updating_address = False

        self.indicate_address_choice("suggested")


    def use_address_as_entered(self):
        self.indicate_address_choice("entered")


    def run(self):
        self.root.mainloop()