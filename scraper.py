from playwright.sync_api import sync_playwright, Error
from pathlib import Path
from private import rp_url_prefix
from schema_classes import RequestPortalData


class Scraper:
    def __init__(self):
        self.playwright_profile = Path(__file__).parent / "playwright_profile"


    def get_field_value(self, page, field_name):
        label = page.locator("span.greyText", has_text=field_name)
        if label.count() == 0:
            return ""
        cell = label.first.locator("xpath=..")
        return cell.locator("span").nth(1).inner_text().strip()


    def session_is_authenticated(self, url):
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.playwright_profile,
                headless=True,
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded")
            except Error:
                pass

            request_for_label = page.locator("span.greyText", has_text="Request For:")
            if request_for_label.count() > 0:
                context.close()
                return True
            return False


    def url_entry_is_valid(self, url):
        if not url:
            return False

        if not url.startswith(rp_url_prefix):
            return False

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.playwright_profile,
                headless=True,
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded")
            except Error:
                pass

            error_heading = page.locator("#leftContent h2", has_text="Sorry, an error occurred while processing your request.")

            if error_heading.count() > 0:
                context.close()
                return False

            return True


    def authenticate_session(self, url):
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.playwright_profile,
                headless=False,
                no_viewport=True,
                args=["--start-maximized"]
            )
            page = context.pages[0] if context.pages else context.new_page()

            try:
                page.goto(url, wait_until="domcontentloaded")
            except Error:
                pass

            page.wait_for_url("https://requestportal.americansystems.com/**", timeout=300_000)
            context.close()


    def scrape_request(self, url):
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.playwright_profile,
                headless=True,
            )
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded")
            except Error:
                pass

            rp_data = RequestPortalData(
                request_for=self.get_field_value(page, "Request For:"),
                request_by=self.get_field_value(page, "Request By:"),
                comments=self.get_field_value(page, "Comments:"),
                new_hire_name=self.get_field_value(page, "New Hire Name:"),
                new_hire_date=self.get_field_value(page, "New Hire Date:"),
                facility=self.get_field_value(page, "Facility:"),
                office=self.get_field_value(page, "Office:"),
                address=self.get_field_value(page, "Address:"),
                phone_number=self.get_field_value(page, "Phone Number:"),
                cell_phone=self.get_field_value(page, "Cellphone:"),
                needed_by_date=self.get_field_value(page, "Needed by Date:"),
                instructions=self.get_field_value(page, "Instructions:"),
                others_to_notify=self.get_field_value(page, "Others to Notify:"),
            )
            context.close()
            return rp_data