def build_address_validation_payload(address, account_number):
    validation_schema = {
        "addressesToValidate": [
            {
                "address": {
                    "streetLines": [line for line in [address.street_line_one, address.street_line_two] if line is not None],
                    "city": address.city,
                    "stateOrProvinceCode": address.state_code,
                    "postalCode": address.postal_code,
                    "countryCode": address.country_code,
                }
            }
        ]
    }

    return validation_schema


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
            "name": shipment.shipper_name,
            "emailNotificationRecipientType": "SHIPPER",
            "emailAddress": shipment.shipper_email_address,
            "notificationEventType": notification_events_to_include,
            "notificationFormatType": "HTML",
            "notificationType": "EMAIL",
            "locale": "en_US",
        },

        {
            "name": shipment.recipient_name,
            "emailNotificationRecipientType": "RECIPIENT",
            "emailAddress": shipment.recipient_email_address,
            "notificationEventType": notification_events_to_include,
            "notificationFormatType": "HTML",
            "notificationType": "EMAIL",
            "locale": "en_US",
        }
    ]

    for other_party_email in shipment.other_emails_to_notify:
        notifications_data.append(
            {
                "name": other_party_email,
                "emailNotificationRecipientType": "OTHER",
                "emailAddress": other_party_email,
                "notificationEventType": notification_events_to_include,
                "notificationFormatType": "HTML",
                "notificationType": "EMAIL",
                "locale": "en_US",
            }
        )

    return notifications_data


def build_fedex_ship_payload(shipment, account_number):

    email_notifications_schema_list = build_email_notifications_schema_list(shipment)

    ship_schema = {
        "requestedShipment": {
            "shipper": {
                "address": {
                    "streetLines": shipment.shipper_street_lines,
                    "city": shipment.shipper_city,
                    "stateOrProvinceCode": shipment.shipper_state_code,
                    "postalCode": shipment.shipper_postal_code,
                    "countryCode": shipment.shipper_country_code,
                    "residential": shipment.shipper_address_is_residential,
                },
                "contact": {
                    "personName": shipment.shipper_name,
                    "emailAddress": shipment.shipper_email_address,
                    "phoneNumber": shipment.shipper_phone_number,
                    "companyName": shipment.company_name}
            },
            "recipients": [
                {
                    "address": {
                        "streetLines": shipment.recipient_street_lines,
                        "city": shipment.recipient_city,
                        "stateOrProvinceCode": shipment.recipient_state_code,
                        "postalCode": shipment.recipient_postal_code,
                        "countryCode": shipment.recipient_country_code,
                        "residential": shipment.recipient_address_is_residential,
                    },
                    "contact": {
                        "personName": shipment.recipient_name,
                        "emailAddress": shipment.recipient_email_address,
                        "phoneNumber": shipment.recipient_phone_number,
                        "companyName": shipment.company_name}
                }
            ],
            "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
            "serviceType": shipment.service_type,
            "packagingType": "YOUR_PACKAGING",
            "totalWeight": shipment.shipment_weight,
            "shippingChargesPayment": {"paymentType": "SENDER"},
            "shipmentSpecialServices": {
                "specialServiceTypes": ["EVENT_NOTIFICATION"],
            },
            "emailNotificationDetail": {
                "aggregationType": "PER_SHIPMENT",
                "emailNotificationRecipients": email_notifications_schema_list,
                "personalMessage": "You have a FedEx package on the way Mr. Marnoshk Michaels!"
            },
            "labelSpecification": {"labelStockType": "PAPER_4X6", "imageType": "PDF", "labelFormatType": "COMMON2D"},
            "requestedPackageLineItems": [
                {
                    "customerReferences": [
                        {"customerReferenceType": "CUSTOMER_REFERENCE", "value": shipment.reference_number},
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


def build_fedex_rates_payload(shipment, account_number):

    rates_schema = {
        "accountNumber": {
            "value": account_number
        },
        "rateRequestControlParameters": {
            "returnTransitTimes": True
        },
        "requestedShipment": {
            "shipper": {
                "address": {
                    "city": shipment.shipper_city,
                    "stateOrProvinceCode": shipment.shipper_state_code,
                    "postalCode": shipment.shipper_postal_code,
                    "countryCode": shipment.shipper_country_code,
                    "residential": shipment.shipper_address_is_residential,
                }
            },
            "recipient": {
                "address": {
                    "city": shipment.recipient_city,
                    "stateOrProvinceCode": shipment.recipient_state_code,
                    "postalCode": shipment.recipient_postal_code,
                    "countryCode": shipment.recipient_country_code,
                    "residential": shipment.recipient_address_is_residential,
                }
            },
            "pickupType": "DROPOFF_AT_FEDEX_LOCATION",
            "packagingType": "YOUR_PACKAGING",
            "rateRequestType": [
                "ACCOUNT"
            ],
            "requestedPackageLineItems": [
                {
                "weight": {
                    "units": "LB",
                    "value": shipment.shipment_weight,
                },
            }
            ],
        },
    }

    return rates_schema