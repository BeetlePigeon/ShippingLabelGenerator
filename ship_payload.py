from private import account_number, company_name


SERVICE_TYPES = {
    # Expedited
    0: "PRIORITY_OVERNIGHT",        # 1 business day
    1: "FEDEX_2_DAY",               # 2 business days
    2: "FEDEX_EXPRESS_SAVER",       # 3 business days

    # Regular
    3: "FEDEX_GROUND",              # Use for commercial address deliveries
    4: "GROUND_HOME_DELIVERY",      # Use for residential address deliveries
}

def build_fedex_ship_payload(shipper, recipient, service_type, shipment_weight=10):
    ship_schema = {
        "requestedShipment": {
            "shipper": {
                "address": {
                    "streetLines": [shipper.street_line_one, shipper.street_line_two],
                    "city": shipper.city,
                    "stateOrProvinceCode": shipper.state_code,
                    "postalCode": shipper.postal_code,
                    "countryCode": shipper.country_code,
                    "residential": shipper.is_residential,
                },
                "contact": {
                    "personName": shipper.full_name,
                    "emailAddress": shipper.email_address,
                    "phoneNumber": shipper.phone_number,
                    "companyName": company_name}
            },
            "recipients": [{
                "address": {
                    "streetLines": recipient.street_lines,
                    "city": recipient.city,
                    "stateOrProvinceCode": recipient.state_code,
                    "postalCode": recipient.postal_code,
                    "countryCode": recipient.country_code,
                    "residential": recipient.is_residential,
                },
                "contact": {
                    "personName": recipient.full_name,
                    "emailAddress": recipient.email_address,
                    "phoneNumber": recipient.phone_number,
                    "companyName": company_name}
            }],
            "pickupType": "USE_SCHEDULED_PICKUP",
            "serviceType": service_type,
            "packagingType": "YOUR_PACKAGING",
            "totalWeight": shipment_weight,
            "shippingChargesPayment": {"paymentType": "SENDER"},
            "labelSpecification": {"labelStockType": "PAPER_4X6", "imageType": "PDF", "labelFormatType": "COMMON2D"},
            "requestedPackageLineItems": [{"weight": {"units": "LB", "value": shipment_weight}}],
        },
        "labelResponseOptions": "LABEL",
        "accountNumber": {"value": account_number}
    }

    return ship_schema