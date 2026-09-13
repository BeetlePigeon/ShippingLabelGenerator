from private import account_number, company_name


def build_email_notifications_schema_list(shipment):
    notification_events_to_include = [
        "ON_SHIPMENT",
        "ON_TENDER",
        "ON_ESTIMATED_DELIVERY",
        "ON_DELIVERY",
        "ON_EXCEPTION",
    ]

    notifications_data = [
        {
            "name": shipment.shipper.full_name,
            "emailNotificationRecipientType": "SHIPPER",
            "emailAddress": shipment.shipper.email_address,
            "notificationEventType": notification_events_to_include,
        },

        {
            "name": shipment.recipient.full_name,
            "emailNotificationRecipientType": "RECIPIENT",
            "emailAddress": shipment.recipient.email_address,
            "notificationEventType": notification_events_to_include,
        }
    ]

    for other_party_email in shipment.other_emails_to_notify:
        notifications_data.append(
            {
                "name": other_party_email,
                "emailNotificationRecipientType": "OTHER",
                "emailAddress": other_party_email,
                "notificationEventType": notification_events_to_include,
            }
        )

    return notifications_data


def build_fedex_ship_payload(shipment):

    email_notifications_schema_list = build_email_notifications_schema_list(shipment)

    ship_schema = {
        "requestedShipment": {
            "shipper": {
                "address": {
                    "streetLines": shipment.shipper.address.street_lines,
                    "city": shipment.shipper.address.city,
                    "stateOrProvinceCode": shipment.shipper.address.state_code,
                    "postalCode": shipment.shipper.address.postal_code,
                    "countryCode": shipment.shipper.address.country_code,
                    "residential": shipment.shipper.address.is_residential,
                },
                "contact": {
                    "personName": shipment.shipper.full_name,
                    "emailAddress": shipment.shipper.email_address,
                    "phoneNumber": shipment.shipper.phone_number,
                    "companyName": company_name}
            },
            "recipients": [{
                "address": {
                    "streetLines": shipment.recipient.address.street_lines,
                    "city": shipment.recipient.address.city,
                    "stateOrProvinceCode": shipment.recipient.address.state_code,
                    "postalCode": shipment.recipient.address.postal_code,
                    "countryCode": shipment.recipient.address.country_code,
                    "residential": shipment.recipient.address.is_residential,
                },
                "contact": {
                    "personName": shipment.recipient.full_name,
                    "emailAddress": shipment.recipient.email_address,
                    "phoneNumber": shipment.recipient.phone_number,
                    "companyName": company_name}
            }],
            "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
            "serviceType": shipment.service_type,
            "packagingType": "YOUR_PACKAGING",
            "totalWeight": shipment.shipment_weight,
            "shippingChargesPayment": {"paymentType": "SENDER"},
            "emailNotificationDetail": {
                "aggregationType": "PER_SHIPMENT",
                "emailNotificationRequests": email_notifications_schema_list,
            },
            "labelSpecification": {"labelStockType": "PAPER_4X6", "imageType": "PDF", "labelFormatType": "COMMON2D"},
            "requestedPackageLineItems": [
                {
                    "customerReferences": [
                        {"customerReferenceType": "CUSTOMER_REFERENCE", "value": f"{shipment.case_number}_{shipment.asset_number}"},
                        {"customerReferenceType": "DEPARTMENT_NUMBER", "value": shipment.charge_code},
                    ],
                    "weight": {"units": "LB", "value": shipment.shipment_weight}
                }
            ],
        },
        "labelResponseOptions": "LABEL",
        "accountNumber": {"value": account_number}
    }

    return ship_schema


def build_fedex_rates_payload(shipment):

    rates_schema = {
        "accountNumber": {"value": account_number},
        "rateRequestControlParameters": {"returnTransitTimes": True},
        "requestedShipment": {
            "shipper": {
                "address": {
                    "city": shipment.shipper.address.city,
                    "stateOrProvinceCode": shipment.shipper.address.state_code,
                    "postalCode": shipment.shipper.address.postal_code,
                    "countryCode": shipment.shipper.address.country_code,
                    "residential": shipment.shipper.address.is_residential,
                }
            },
            "recipient": {
                "address": {
                    "city": shipment.recipient.address.city,
                    "stateOrProvinceCode": shipment.recipient.address.state_code,
                    "postalCode": shipment.recipient.address.postal_code,
                    "countryCode": shipment.recipient.address.country_code,
                    "residential": shipment.recipient.address.is_residential,
                }
            },
            "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
            "requestedPackageLineItems": [
                {
                "weight": shipment.shipment_weight,
            }
            ],
            "packagingType": "YOUR_PACKAGING",
            "totalPackageCount": 1,
            "totalWeight": shipment.shipment_weight,
        },
    }

    return rates_schema