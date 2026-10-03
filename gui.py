import tkinter
from tkinter import ttk
from scraper import Scraper


class GUI:
    def __init__(self):
        self.scraper = Scraper()

        self.root = tkinter.Tk()
        self.root.title("FedEx Shipping Label Generator")

        self.rp_label = ttk.Label(self.root, text="RequestPortal URL")
        self.rp_label.grid(row=0, column=0, padx=5, pady=5)

        self.rp_url_entry = ttk.Entry(self.root, width=90)
        self.rp_url_entry.grid(row=0, column=1, padx=5, pady=5)

        self.retrieve_rates_button = ttk.Button(self.root, text="Retrieve Rates", command=self.retrieve_rates)
        self.retrieve_rates_button.grid(row=1, column=0, columnspan=2, pady=10)

        self.results_frame = ttk.Frame(self.root)
        self.results_frame.grid(row=2, column=0, columnspan=2, sticky="w")


    def clear_results_frame(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()


    def retrieve_rates(self):
        url = self.rp_url_entry.get().strip()

        if not self.scraper.url_entry_is_valid(url):
            self.clear_results_frame()
            ttk.Label(self.results_frame, text="Please provide a valid RequestPortal URL.").grid(row=0, column=0, sticky="w", padx=5, pady=2)
            return

        if not self.scraper.session_is_authenticated(url):
            self.clear_results_frame()
            ttk.Label(self.results_frame, text="Session expired. Please log in again.")
            self.scraper.authenticate_session(url)

        rp_data = self.scraper.scrape_request(url)

        self.clear_results_frame()
        for index, (field_name, field_value) in enumerate(rp_data.model_dump().items()):
            ttk.Label(self.results_frame, text=field_name).grid(row=index, column=0, sticky="w", padx=5, pady=2)
            ttk.Label(self.results_frame, text=field_value).grid(row=index, column=1, sticky="w", padx=5, pady=2)


    def run(self):
        self.root.mainloop()
