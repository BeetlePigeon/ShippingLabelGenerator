from shipment_processor import Processor
from test_inputs import test_requests


class Tester:
    def __init__(self):
        self.processor = Processor()


    @staticmethod
    def mismatch_str(expected, actual):
        return f"expected <{expected}> vs actual <{actual}>"


    def run_test(self, request, expected_output):
        self.processor.clear_preshipment_details()
        scrape_success = self.processor.load_preshipment_details_from_scraper(request)

        test_results = {
            "valid_request": "Success" if expected_output["valid_request"] == scrape_success else self.mismatch_str(expected_output["valid_request"], scrape_success)
        }

        if not scrape_success:
            return test_results

        for field, expected_result in expected_output.items():
            if field == "valid_request":
                continue

            actual_result = self.processor.preshipment_details[field]
            if expected_result.lower() != actual_result.lower():
                test_results[field] = self.mismatch_str(expected_result, actual_result)
            else:
                test_results[field] = "Success"

        return test_results



if __name__ == "__main__":
    tester = Tester()

    for request_number, expected_fields in test_requests.items():
        test_results = tester.run_test(request_number, expected_fields)

        if all(result == "Success" for result in test_results.values()):
            print(f"{request_number}: All tests successful")
        else:
            failures = [f"{field}: {result}" for field, result in test_results.items() if result != "Success"]
            print(f"{request_number}: {failures}")