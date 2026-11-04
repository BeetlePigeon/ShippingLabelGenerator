import tkinter
from tkinter import ttk
from shipment_processor import Processor
from config import LABEL_SUBDIR
from private import rp_url_prefix
from PIL import Image, ImageTk
from pathlib import Path
from tables import state_codes
from concurrent.futures import ThreadPoolExecutor


class GUI:
    def __init__(self):

        self.processor = Processor()

        self.executor = ThreadPoolExecutor(max_workers=1)
        self.executor_running = False

        self.main_buttons = []
        self.radiobuttons = []
        self.entries = {}

        self.root = tkinter.Tk()
        self.root.title("FedEx Shipping Label Generator")

        self.root.report_callback_exception = self.handle_callback_exception

        self.main_font = "Segoe UI"
        self.secondary_font = "Segoe UI Symbol"

        assets_dir = Path(__file__).parent

        self.company_icon = self.create_company_icon(assets_dir)
        self.root.iconphoto(True, self.company_icon)

        self.configure_styles()

        self.main_frame = ttk.Frame(self.root, padding=(22, 12, 22, 12))
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.columnconfigure(0, weight=1)

        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_frame.columnconfigure(0, weight=1)

        header_inner = ttk.Frame(title_frame)
        header_inner.grid(row=0, column=0)

        fedex_image = Image.open(assets_dir / "fedex_logo.png")
        fedex_image = fedex_image.resize((90, 50))
        self.fedex_logo_image = ImageTk.PhotoImage(fedex_image)

        tkinter.Label(header_inner, image=self.fedex_logo_image, bg=self.colors["bg"], borderwidth=0).pack(side="left", padx=(0, 12))
        ttk.Label(header_inner, text="Shipping Label Generator", font=(self.main_font, 18, "bold")).pack(side="left")

        self.rp_outer_frame = ttk.Frame(self.main_frame, padding=(12, 10), style="Card.TFrame")
        self.rp_outer_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
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
        self.entries["rp_number"] = self.rp_number_entry

        self.rp_paste_button = ttk.Button(rp_controls_frame, text="⧉", width=2, style="Icon.TButton", command=self.handle_rp_paste)
        self.rp_paste_button.pack(side="left", padx=(3, 10))
        self.main_buttons.append(self.rp_paste_button)

        self.lookup_button = ttk.Button(rp_controls_frame, text="Lookup", style="Primary.TButton", command=self.lookup_and_display_preshipment_details)
        self.lookup_button.pack(side="left")
        self.main_buttons.append(self.lookup_button)

        self.rp_number_entry.bind("<Return>", lambda event: self.lookup_button.invoke())

        self.rp_error_label = ttk.Label(self.rp_outer_frame, text="", style="Error.TLabel")
        self.rp_error_label.grid(row=1, column=0, pady=(5, 0))

        self.progress_bar = ttk.Progressbar(self.rp_outer_frame, orient="horizontal", mode="indeterminate", length=180)
        self.root.update_idletasks()
        self.rp_outer_frame.rowconfigure(2, minsize=self.progress_bar.winfo_reqheight())
        self.progress_bar.grid(row=2, column=0)
        self.progress_bar.grid_remove()

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

        self.clear_shipment_details_button = ttk.Button(action_frame, text="Clear All", command=self.clear_preshipment_entries)
        self.clear_shipment_details_button.pack(side="left", padx=7)
        self.main_buttons.append(self.clear_shipment_details_button)

        self.retrieve_rates_button = ttk.Button(action_frame, text="Retrieve Rates", style="Primary.TButton", state="normal", command=self.attempt_retrieve_rates)
        self.retrieve_rates_button.pack(side="left", padx=7)
        self.main_buttons.append(self.retrieve_rates_button)

        self.root.protocol("WM_DELETE_WINDOW", self.exit_application)

        self.root.update_idletasks()
        window_width = self.root.winfo_reqwidth()
        screen_width = self.root.winfo_screenwidth()

        x = (screen_width - window_width) // 2
        self.root.geometry(f"+{x}+0")


    def handle_callback_exception(self, exception, value, traceback):
        self.root.destroy()


    @staticmethod
    def create_company_icon(assets_dir):
        placeholder_company_icon_path = assets_dir / "placeholder_company_icon.png"
        custom_company_icon_path = assets_dir / "my_company_icon.png"

        if custom_company_icon_path.is_file():
            company_icon = Image.open(custom_company_icon_path)
        else:
            company_icon = Image.open(placeholder_company_icon_path)

        company_icon = company_icon.convert("RGBA")
        company_icon.thumbnail((64, 64), Image.Resampling.LANCZOS)
        company_icon = ImageTk.PhotoImage(company_icon)

        return company_icon


    def configure_styles(self):
        self.colors = {
            "bg": "#eff3f9",
            "surface": "#ffffff",
            "sky": "#e5eaf0",
            "muted": "#e9eff7",
            "border": "#ccd8e6",
            "ink": "#263449",
            "subtitle": "#67798f",
            "success": "#188038",

            "suggestion_bg": "#f3f7fd",
            "suggestion_border": "#b8cce7",
            "suggestion_field": "#e8f0fa",
            "suggestion_button": "#dceafe",

            "disabled_fbg": "#d8dee7",
            "disabled_fg": "#8894a6",

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

        style.configure("Horizontal.TProgressbar", thickness=8)
        style.configure("Required.TLabel", background=c["surface"], foreground=c["asterisk"], font=(self.main_font, 10, "bold"))
        style.configure("TFrame", background=c["bg"])
        style.configure("Card.TFrame", background=c["surface"], relief="solid", borderwidth=1, bordercolor=c["border"])
        style.configure("CardInterior.TFrame", background=c["surface"], borderwidth=0, relief="flat")
        style.configure("TLabel", background=c["bg"], foreground=c["ink"], font=(self.main_font, 10))
        style.configure("Card.TLabel", background=c["surface"], foreground=c["ink"], font=(self.main_font, 10))
        style.configure("Hint.TLabel", background=c["surface"], foreground=c["subtitle"], font=(self.main_font, 9))
        style.configure("Error.TLabel", background=c["surface"], foreground=c["hover"], font=(self.main_font, 12))
        style.configure("RatesSuccess.TLabel", foreground=c["success"], font=(self.main_font, 10))
        style.configure("RatesError.TLabel", foreground=c["hover"], font=(self.main_font, 10))
        style.configure("AddressType.TFrame", background=c["surface"], bordercolor=c["surface"], borderwidth=1, relief="solid")
        style.configure("InvalidAddressType.TFrame", background=c["surface"], bordercolor=c["asterisk"], borderwidth=1, relief="solid")
        style.configure("ActionHint.TLabel", background=c["bg"], foreground=c["subtitle"], font=(self.main_font, 9))
        style.configure("ActionHintSuccess.TLabel", background=c["bg"], foreground=c["success"], font=(self.main_font, 9, "bold"))
        style.configure("TEntry", fieldbackground="white", bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], relief="flat", borderwidth=1, padding=4, font=(self.main_font, 10))
        style.map("TEntry", fieldbackground=[("disabled", c["disabled_fbg"])], foreground=[("disabled", c["disabled_fg"])], bordercolor=[("invalid", c["asterisk"]),("focus", c["input_focus"])])
        style.configure("TCombobox", fieldbackground="white", background=c["combobox"], bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"], padding=4, font=(self.main_font, 10))
        style.map("TCombobox", fieldbackground=[("disabled", c["disabled_fbg"]), ("readonly", "white")], foreground=[("disabled", c["disabled_fg"])], bordercolor=[("invalid", c["asterisk"])])
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
        style.configure("SuggestionCheck.TLabel", background=c["suggestion_bg"], borderwidth=0, padding=0)
        style.configure("Suggestion.TEntry", fieldbackground=c["suggestion_field"], bordercolor=c["suggestion_border"], foreground=c["ink"], padding=3)
        style.map("Suggestion.TEntry", fieldbackground=[("readonly", c["suggestion_field"])], foreground=[("readonly", c["ink"])])
        style.configure("SuggestAction.TButton", background=c["suggestion_button"], foreground=c["primary"], bordercolor=c["suggestion_border"], borderwidth=1, padding=(12, 4), font=(self.main_font, 10, "bold"))
        style.map("SuggestAction.TButton", background=[("active", c["button_hover"])], foreground=[("active", c["primary"])])


    @staticmethod
    def create_field_label(parent, text, row, column=0, required=False, padx=5, pady=3, sticky="w"):
        label_frame = ttk.Frame(parent, style="CardInterior.TFrame")
        label_frame.grid(row=row, column=column, sticky=sticky, padx=padx, pady=pady)

        ttk.Label(label_frame, text=text, style="Card.TLabel").pack(side="left")

        if required:
            ttk.Label(label_frame, text=" *", style="Required.TLabel").pack(side="left")


    def create_preshipment_sections(self):
        left_column = ttk.Frame(self.results_frame)
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        left_column.columnconfigure(0, weight=1)

        self.recipient_frame = ttk.Frame(left_column, padding=4, style="Card.TFrame")
        self.recipient_frame.grid(row=0, column=0, sticky="ew")
        self.recipient_frame.columnconfigure(1, weight=1)

        self.recipient_header = tkinter.Label(self.recipient_frame, text="Recipient", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=(self.main_font, 12, "bold"))
        self.recipient_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.create_field_label(self.recipient_frame, "Name", 1, required=True)
        self.entries["recipient_name"] = ttk.Entry(self.recipient_frame, textvariable=self.recipient_name, width=36)
        self.entries["recipient_name"].grid(row=1, column=1, sticky="ew", padx=5, pady=3)

        self.create_field_label(self.recipient_frame, "Email", 2, required=False)
        self.entries["recipient_email"] = ttk.Entry(self.recipient_frame, textvariable=self.recipient_email, width=36)
        self.entries["recipient_email"].grid(row=2, column=1, sticky="ew", padx=5, pady=3)

        phone_validation = (self.root.register(self.validate_phone_entry), "%P")
        self.create_field_label(self.recipient_frame, "Phone", 3, required=False)
        self.entries["recipient_phone"] = ttk.Entry(self.recipient_frame, textvariable=self.recipient_phone, width=36, validate="key", validatecommand=phone_validation)
        self.entries["recipient_phone"].grid(row=3, column=1, sticky="ew", padx=5, pady=3)

        self.other_frame = ttk.Frame(left_column, padding=4, style="Card.TFrame")
        self.other_frame.grid(row=1, column=0, sticky="ew")
        self.other_frame.columnconfigure(1, weight=1)

        self.other_header = tkinter.Label(self.other_frame, text="Other", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=(self.main_font, 12, "bold"))
        self.other_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        fields = [
            ("Reference #", "reference", self.reference),
            ("Weight (lbs)", "weight",  self.weight),
            ("Other Emails to Notify", "other_email_1",  self.other_emails[0]),
            ("", "other_email_2",  self.other_emails[1]),
            ("", "other_email_3",  self.other_emails[2]),
        ]

        weight_validation = (self.root.register(self.validate_weight_entry), "%P")

        for row, (field_name, key, field_value) in enumerate(fields):
            ttk.Label(self.other_frame, style="Card.TLabel", text=field_name).grid(row=row + 1, column=0, sticky="w", padx=5, pady=3)
            entry = ttk.Entry(self.other_frame, textvariable=field_value, width=36)

            self.entries[key] = entry

            if field_name == "Weight (lbs)":
                entry.configure(validate="key", validatecommand=weight_validation)

            entry.grid(row=row+1, column=1, sticky="ew", padx=5, pady=3)

        self.address_frame = ttk.Frame(self.results_frame, padding=4, style="Card.TFrame")
        self.address_frame.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self.address_frame.columnconfigure(1, weight=1)

        self.address_header = tkinter.Label(self.address_frame, text="Address", anchor="w", padx=12, pady=2, bg=self.colors["muted"], fg=self.colors["ink"], font=(self.main_font, 12, "bold"))
        self.address_header.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))

        self.create_field_label(self.address_frame, "Street line 1", row=1, required=True, pady=4)
        self.entries["street_line_one"] = ttk.Entry(self.address_frame, textvariable=self.street_line_one, width=36)
        self.entries["street_line_one"].grid(row=1, column=1, sticky="ew", padx=5, pady=4)

        self.create_field_label(self.address_frame, "Street line 2", row=2, required=False, pady=4)
        self.entries["street_line_two"] = ttk.Entry(self.address_frame, textvariable=self.street_line_two, width=36)
        self.entries["street_line_two"].grid(row=2, column=1, sticky="ew", padx=5, pady=4)

        self.bottom_frame = ttk.Frame(self.address_frame, style="CardInterior.TFrame")
        self.bottom_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=8)
        self.bottom_frame.columnconfigure(0, weight=1, uniform="bottom")
        self.bottom_frame.columnconfigure(1, weight=1, uniform="bottom")

        self.type_frame = ttk.Frame(self.bottom_frame, style="AddressType.TFrame", padding=(8, 0))
        self.type_frame.grid(row=0, column=0, sticky="nsew")
        self.type_frame.columnconfigure(0, weight=1)
        self.type_frame.rowconfigure(1, weight=1)

        self.create_field_label(self.type_frame, "Classification", row=0, required=True, padx=0, pady=(3, 0), sticky="nw")

        radio_frame = ttk.Frame(self.type_frame, style="CardInterior.TFrame")
        radio_frame.grid(row=1, column=0)

        ttk.Label(radio_frame, text="Residential", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=3)
        self.residential_radiobutton = ttk.Radiobutton(radio_frame, style="Card.TRadiobutton", variable=self.address_is_commercial, value=0)
        self.residential_radiobutton.grid(row=0, column=1, padx=8)
        self.radiobuttons.append(self.residential_radiobutton)

        ttk.Label(radio_frame, text="Commercial", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=3)
        self.commercial_radiobutton = ttk.Radiobutton(radio_frame, style="Card.TRadiobutton", variable=self.address_is_commercial, value=1)
        self.commercial_radiobutton.grid(row=1, column=1, padx=8)
        self.radiobuttons.append(self.commercial_radiobutton)

        self.location_frame = ttk.Frame(self.bottom_frame, style="CardInterior.TFrame")
        self.location_frame.grid(row=0, column=1, sticky="ew")
        self.location_frame.columnconfigure(0, weight=1, uniform="location")
        self.location_frame.columnconfigure(1, weight=1, uniform="location")

        self.create_field_label(self.location_frame, "City", row=0, required=True, padx=0, pady=0)
        self.entries["city"] = ttk.Entry(self.location_frame, textvariable=self.city)
        self.entries["city"].grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        self.create_field_label(self.location_frame, "State", row=2, column=0, required=True, padx=0, pady=0)
        self.entries["state_code"] = ttk.Combobox(self.location_frame, textvariable=self.state_code, values=state_codes, state="readonly", width=6)
        self.entries["state_code"].grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=2)

        zip_validation = (self.root.register(self.validate_zip_entry), "%P")
        self.create_field_label(self.location_frame, "ZIP", row=2, column=1, required=True, padx=(5, 0), pady=0)
        self.entries["postal_code"] = ttk.Entry(self.location_frame, textvariable=self.postal_code, width=10, validate="key", validatecommand=zip_validation)
        self.entries["postal_code"].grid(row=3, column=1, sticky="ew", padx=(5, 0), pady=2)

        self.address_frame.rowconfigure(4, weight=1)

        self.suggestion_panel = ttk.Frame(self.address_frame, style="SuggestionCard.TFrame", padding=(8, 6))
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

        self.suggest_address_button = ttk.Button(self.suggestion_request_view, text="Suggest Address?", image=self.pin_icon, compound="left", style="SuggestAction.TButton", command=self.suggest_address)
        self.suggest_address_button.grid(row=0, column=0)
        self.main_buttons.append(self.suggest_address_button)

        # View 2
        self.suggestion_result_view = ttk.Frame(self.suggestion_panel, style="SuggestionBody.TFrame")
        self.suggestion_result_view.grid(row=0, column=0, sticky="nsew")
        self.suggestion_result_view.columnconfigure(0, weight=1)

        ttk.Label(self.suggestion_result_view, text="Address Review - Choose an Option", style="Suggestion.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 3))

        self.suggested_address_display = tkinter.StringVar(value="")
        self.suggested_address_entry = ttk.Entry(self.suggestion_result_view, textvariable=self.suggested_address_display, state="readonly", style="Suggestion.TEntry", takefocus=False)
        self.suggested_address_entry.grid(row=1, column=0, sticky="ew")

        self.no_suggestion_label = ttk.Label(self.suggestion_result_view, text="FedEx could not find an address.", style="SuggestionNote.TLabel", padding=(6, 5))
        self.no_suggestion_label.grid(row=1, column=0, sticky="ew")

        choice_frame = ttk.Frame(self.suggestion_result_view, style="SuggestionBody.TFrame")
        choice_frame.grid(row=2, column=0, pady=(5, 0))

        self.use_suggested_button = ttk.Button(choice_frame, text="Use Suggested Address", style="Compact.TButton", state="disabled", command=self.use_suggested_address)
        self.use_suggested_button.pack(side="left", padx=(0, 5))
        self.main_buttons.append(self.use_suggested_button)

        self.use_entered_button = ttk.Button(choice_frame, text="Use Address As Entered", style="Compact.TButton", state="disabled", command=self.use_address_as_entered)
        self.use_entered_button.pack(side="left", padx=(5, 0))
        self.main_buttons.append(self.use_entered_button)

        # View 3
        self.suggestion_approve_view = ttk.Frame(self.suggestion_panel, style="SuggestionBody.TFrame")
        self.suggestion_approve_view.grid(row=0, column=0, sticky="nsew")
        self.suggestion_approve_view.columnconfigure(0, weight=1)
        self.suggestion_approve_view.rowconfigure(0, weight=1)

        check_image = Image.open(Path(__file__).parent / "circle-check.png").convert("RGBA")
        check_image = check_image.resize((24, 24), Image.Resampling.LANCZOS)
        alpha = check_image.getchannel("A")

        check_image= Image.new("RGBA", check_image.size, self.colors["success"])
        check_image.putalpha(alpha)

        self.check_icon = ImageTk.PhotoImage(check_image)

        self.check_label = ttk.Label(self.suggestion_approve_view, image=self.check_icon, style="SuggestionCheck.TLabel")
        self.check_label.grid(row=0, column=0)

        # Set initial view
        self.suggestion_request_view.tkraise()


    def on_address_changed(self, *args):
        if self._updating_address:
            return

        self.clear_errors()
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
            self.rp_number_entry.delete(0, "end")
            self.rp_number_entry.insert(0, request_number)
            self.rp_error_label.configure(text="")
            return "break"


    def clear_rp_widgets(self):
        self.rp_number_entry.delete(0, "end")
        self.rp_error_label.configure(text="")


    def disable_gui_widgets(self):
        widgets = [*self.entries.values(), *self.main_buttons, *self.radiobuttons]

        self.previously_enabled = [widget for widget in widgets if not widget.instate(["disabled"])]

        for widget in widgets:
            widget.state(["disabled"])


    def enable_gui_widgets(self):
        for widget in self.previously_enabled:
            widget.state(["!disabled"])


    def lookup_and_display_preshipment_details(self):
        if self.executor_running:
            return

        self.rp_error_label.config(text="Request lookup in progress...")
        self.start_progress_bar()
        self.clear_preshipment_entries()

        request_number = self.rp_number_entry.get().strip()
        future = self.executor.submit(self.processor.load_preshipment_details_from_scraper, request_number)
        self.executor_running = True
        self.disable_gui_widgets()
        self.root.after(50, self.check_lookup_result, future)


    def check_lookup_result(self, future):
        if future.done():
            self.executor_running = False
            self.stop_progress_bar()
            self.enable_gui_widgets()

            lookup_success = future.result()

            if lookup_success:
                self.rp_error_label.config(text="")
                self.sync_preshipment_details_from_processor_to_gui()
            else:
                self.rp_error_label.config(text="Invalid RequestPortal number.")
        else:
            self.root.after(50, self.check_lookup_result, future)


    def start_progress_bar(self):
        self.progress_bar.grid()
        self.progress_bar.start(10)


    def stop_progress_bar(self):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()


    def show_suggestion_request_view(self):
        self.suggest_address_button.configure(state="normal")

        self.use_suggested_button.configure(state="disabled", style="Compact.TButton")
        self.use_entered_button.configure(state="disabled", style="Compact.TButton")

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


    def clear_preshipment_entries(self):
        self.processor.clear_preshipment_details()
        self.sync_preshipment_details_from_processor_to_gui()


    def sync_address_from_processor_to_gui(self):
        self.street_line_one.set(self.processor.preshipment_details["street_line_one"])
        self.street_line_two.set(self.processor.preshipment_details["street_line_two"])
        self.city.set(self.processor.preshipment_details["city"])
        self.state_code.set(self.processor.preshipment_details["state_code"])
        self.postal_code.set(self.processor.preshipment_details["postal_code"])
        self.address_is_commercial.set(self.processor.preshipment_details["address_is_commercial"])


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


    def suggest_address(self):
        if self.executor_running:
            return

        if not self.street_line_one.get().strip():
            self.entries["street_line_one"].state(["invalid"])
            return

        self.rp_error_label.config(text="Finding address suggestions...")
        self.start_progress_bar()
        self.executor_running = True
        self.sync_preshipment_details_from_gui_to_processor()
        future = self.executor.submit(self.processor.get_suggested_address)
        self.disable_gui_widgets()
        self.root.after(50, self.check_suggestion_result, future)


    def check_suggestion_result(self, future):
        if future.done():
            self.executor_running = False
            self.stop_progress_bar()
            self.enable_gui_widgets()
            self.rp_error_label.config(text="")

            confirmed, address, is_commercial = future.result()


            if confirmed is True:
                self.processor.set_suggested_address(address, is_commercial)
                self.display_suggested_address()
            else:
                self.suggested_address_display.set("")

            self.show_suggestion_result_view(confirmed=confirmed is True)

        else:
            self.root.after(50, self.check_suggestion_result, future)


    def display_suggested_address(self):
        address = self.processor.suggested_address

        if not address["street_line_two"]:
            text = f"{address["street_line_one"]}, {address["city"]}, {address["state_code"]} {address["postal_code"]}"
        else:
            text = f"{address["street_line_one"]} {address["street_line_two"]}, {address["city"]}, {address["state_code"]} {address["postal_code"]}"

        self.suggested_address_display.set(text)


    def use_suggested_address(self):
        self.processor.suggested_address_to_preshipment_address()

        self._updating_address = True
        self.sync_address_from_processor_to_gui()
        self._updating_address = False

        self.suggestion_approve_view.tkraise()


    def use_address_as_entered(self):
        self.suggestion_approve_view.tkraise()


    def highlight_errors(self, results: dict) -> None:
        for key, entry in self.entries.items():
            if results.get(key, True):
                entry.state(["!invalid"])
            else:
                entry.state(["invalid"])

        if results.get("address_type", True):
            self.type_frame.configure(style="AddressType.TFrame")
        else:
            self.type_frame.configure(style="InvalidAddressType.TFrame")


    def clear_errors(self):
        for key, entry in self.entries.items():
            entry.state(["!invalid"])

        self.type_frame.configure(style="AddressType.TFrame")


    def attempt_retrieve_rates(self):
        if self.executor_running:
            return

        self.rp_error_label.configure(text="")
        self.sync_preshipment_details_from_gui_to_processor()
        results = self.processor.is_preshipment_valid()
        self.highlight_errors(results)

        if all(results.values()):
            self.rp_error_label.config(text="Retrieving rates...")
            self.start_progress_bar()
            self.executor_running = True
            future = self.executor.submit(self.processor.retrieve_rates)
            self.disable_gui_widgets()
            self.root.after(50, self.check_rates_result, future)


    def check_rates_result(self, future):
        if future.done():
            self.executor_running = False
            self.stop_progress_bar()
            self.enable_gui_widgets()
            self.rp_error_label.config(text="")

            rates_success = future.result()

            if rates_success:
                self.display_rates()
            else:
                self.rp_error_label.configure(text="Failed to retrieve rates. Check shipping details and try again.")

        else:
            self.root.after(50, self.check_rates_result, future)


    def display_rates(self):
        self.rates_window = tkinter.Toplevel(self.root)
        self.rates_window.title("Available Shipping Rates")

        width, height = 650, 400

        screen_width = self.rates_window.winfo_screenwidth()
        screen_height = self.rates_window.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.rates_table_configurable = True

        self.rates_window.geometry(f"{width}x{height}+{x}+{y}")
        self.rates_window.transient(self.root)
        self.rates_window.resizable(False, False)

        self.rates_window.protocol("WM_DELETE_WINDOW", self.manually_close_rates)

        columns = ("service_type", "estimated_delivery_time", "estimated_delivery_cost")

        self.rates_table = ttk.Treeview(self.rates_window, columns=columns, show="headings", selectmode="browse")
        self.rates_table.pack(fill="both", expand=True)

        self.rates_table.bind("<<TreeviewSelect>>", self.update_finalize_button)
        self.rates_table.bind("<Button-1>", self.on_table_click)
        self.rates_table.bind("<Up>", self.navigate_rates)
        self.rates_table.bind("<Down>", self.navigate_rates)
        self.rates_table.bind("<Return>", self.finalize_shipment)
        self.rates_table.bind("<space>", self.finalize_shipment)

        self.rates_table.heading("service_type", text="Service")
        self.rates_table.heading("estimated_delivery_time", text="Est. Delivery")
        self.rates_table.heading("estimated_delivery_cost", text="Estimated Cost")

        prev_date = None
        for idx, rate in enumerate(self.processor.rates.options):
            if prev_date != rate.estimated_delivery_time.date():
                prev_date = rate.estimated_delivery_time.date()
                self.rates_table.insert("", "end", iid=f"{prev_date}", tags=("date_header",))

            service_type = rate.table_string
            est_delivery = rate.estimated_delivery_time.strftime("%m-%d %I:%M %p")
            est_cost = f"${rate.estimated_delivery_cost:.2f}"

            self.rates_table.insert("", "end", iid=idx, values=(service_type, est_delivery, est_cost))

        self.rates_table.tag_configure("date_header", background=self.colors["sky"])

        self.rates_button_panel = ttk.Frame(self.rates_window)
        self.rates_button_panel.pack(side="bottom")

        self.rates_status_message = ttk.Label(self.rates_button_panel, text="", style="RatesError.TLabel", width=90)
        self.rates_status_message.grid(row=1, column=0)

        # View 1: Before finalization
        self.finalize_shipment_view = ttk.Frame(self.rates_button_panel, style="SuggestionBody.TFrame")
        self.finalize_shipment_view.grid(row=0, column=0)

        self.edit_shipment_button = ttk.Button(self.finalize_shipment_view, text="Edit Details", width=14, command=self.return_to_preshipment_details)
        self.edit_shipment_button.pack(side="left")

        self.finalize_shipment_button = ttk.Button(self.finalize_shipment_view, text="Finalize Shipment", width=22, style="Primary.TButton", command=self.finalize_shipment, state="disabled")
        self.finalize_shipment_button.pack(side="left")

        # View 2: After finalization attempted
        self.post_finalization_view = ttk.Frame(self.rates_button_panel, style="SuggestionBody.TFrame")
        self.post_finalization_view.grid(row=0, column=0)

        self.new_shipment_button = ttk.Button(self.post_finalization_view, text="New Shipment", width=14, command=self.start_new_shipment)
        self.new_shipment_button.pack(side="left")

        self.exit_application_button = ttk.Button(self.post_finalization_view, text="Exit App", width=22, style="Primary.TButton", command=self.exit_application)
        self.exit_application_button.pack(side="left")

        # Final setup for rates popup
        self.finalize_shipment_view.tkraise()
        self.rates_window.wait_visibility()
        self.rates_window.grab_set()
        self.rates_table.focus_set()


    def manually_close_rates(self):
        if self.rates_table_configurable:
            self.return_to_preshipment_details()
        else:
            self.start_new_shipment()


    def on_table_click(self, event):
        if not self.rates_table_configurable:
            return "break"

        row_id = self.rates_table.identify_row(event.y)

        if row_id and "date_header" in self.rates_table.item(row_id, "tags"):
            return "break"


    def navigate_rates(self, event):
        if not self.rates_table_configurable:
            return "break"

        current_row = self.rates_table.focus()
        if not current_row:
            current_row = "0"
            self.rates_table.focus(current_row)
            self.rates_table.selection_set(current_row)
            return "break"

        if event.keysym == "Up":
            next_row = self.rates_table.prev(current_row)
            if next_row and "date_header" in self.rates_table.item(next_row, "tags"):
                next_row = self.rates_table.prev(next_row)
            if not next_row:
                next_row = "0"
        else:
            next_row = self.rates_table.next(current_row)
            if next_row and "date_header" in self.rates_table.item(next_row, "tags"):
                next_row = self.rates_table.next(next_row)
            if not next_row:
                next_row = str(len(self.processor.rates.options) - 1)

        self.rates_table.focus(next_row)
        self.rates_table.selection_set(next_row)
        return "break"


    def update_finalize_button(self, event=None):
        selection = self.rates_table.selection()

        if selection:
            selected_id = selection[0]

            if "date_header" in self.rates_table.item(selected_id, "tags"):
                self.rates_table.selection_remove(selected_id)

        self.finalize_shipment_button.configure(
            state="normal" if self.rates_table.selection() else "disabled"
        )


    def return_to_preshipment_details(self):
        self.processor.clear_rates()
        self.rates_window.destroy()


    def finalize_shipment(self, event=None):
        if not self.rates_table_configurable:
            return "break"

        selection = self.rates_table.selection()
        if selection:
            selected_rate_id = self.rates_table.selection()[0]
        else:
            return

        selected_rate_option = self.processor.rates.options[int(selected_rate_id)]
        final_shipment_data = self.processor.build_final_shipment_data(selected_rate_option.service_type)
        label_success = self.processor.create_and_save_label(final_shipment_data)

        if label_success:
            output_directory = Path.home() / LABEL_SUBDIR
            self.rates_status_message.configure(text=f"Saved label to {output_directory}", style="RatesSuccess.TLabel")
        else:
            self.rates_status_message.configure(text="Failed to generate FedEx label.")

        self.post_finalization_view.tkraise()
        self.rates_table.configure(selectmode="none", takefocus=False)
        self.rates_table_configurable = False
        self.exit_application_button.focus_set()
        return


    def start_new_shipment(self):
        self.rates_window.destroy()

        self.processor.clear_preshipment_details()
        self.processor.clear_rates()
        self.processor.clear_suggested_address()

        self.sync_preshipment_details_from_processor_to_gui()
        self.clear_rp_widgets()


    def exit_application(self):
        self.root.destroy()


    def run(self):
        self.root.mainloop()