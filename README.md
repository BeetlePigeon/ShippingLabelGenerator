# FedEx Shipping Label Generator

This is a Python application for creating FedEx shipping labels and retrieving available shipping rates using the FedEx REST APIs.

The intention of this project is to streamline, automate, and improve accuracy for an internal IT workflow, reducing both mistakes and the amount of manual work required of IT technicians during the process of shipping IT assets to internal users.

## Current Status: V1

The application currently supports
- Manual input of shipping address details and IT asset reference info
- Shipping label creation via FedEx Ship API
- Rate retrieval via FedEx Rates and Transit Times API
- Dynamic service selection based on retrieved rates

## Features

- Authenticates with FedEx Ship API and Rates and Transit Times API using OAuth 2.0
- Retrieves available account-specific FedEx shipping rates and delivery times for the particular shipment details input
- Identifies cheapest and fastest shipping options from the available delivery options
- Creates FedEx shipping labels and saves the returned Base64-encoded labels as PDF files
- Supports generating email tracking notifications for shipper, receiver, and optional additional notification recipients
- Supports both sandbox and production API environments
- Uses Pydantic models for shipment, address, and rate data
- Loads credentials and environment-specific configuration from '.env'

## Planned Features and Improvements

- V2: Input shipment address information is parsed from a single pasted block, further reducing the amount of manual work user needs to do
- V2: Automated tests and shipment edge-case testing
- V3: Input shipment information is parsed from the internal IT asset request webpage automatically into application input, user just provides the URL
- V4: Once available shipping rates are returned to the user, they can choose from the default (cheapest rate), fastest delivery time, or manually select a service option based on the estimated delivery date and cost using a simple GUI to make the process more user friendly

## Example Workflow

0. For users in my company the relevant API keys, account information, shipper details etc. are already filled out. Otherwise, configure these in '.env' using your own company and FedEx account details (step by step instructions under Initial Setup)
1. Input shipping recipient and shipment reference details into the fields in 'input.py'
2. Run 'main.py', the available shipping rates and delivery dates will print to the console. A shipping label will be created and saved as a PDF file using the default shipping option (cheapest).
3. The selected service type from the available options in the previous step can be manually entered in the 'input.py' field 'selected_service_type' to generate a new label using that service type, if desired. Otherwise, the saved PDF label can be printed and used for shipping.

## Initial Setup

1. Create a .env file based on '.env.example' in the same directory as 'main.py' and the other scripts, this will contain your API credentials and FedEx account information. DO NOT COMMIT .ENV TO SOURCE CONTROL (add .env to '.gitignore') - it contains production credentials and sensitive account information.
2. Clone the repository and install dependencies:
   git clone https://github.com/BeetlePigeon/ShippingLabelGenerator.git
   cd ShippingLabelGenerator

   python -m venv .venv
3. Activate the virtual environment, then
   pip install -r requirements.txt

## Technologies

-  Python
-  Requests
-  FedEx REST APIs
-  OAuth 2.0
-  Pydantic
-  python-dotenv
