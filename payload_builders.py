def build_address_validation_payload(address, account_number):
    validation_schema = {
        "addressesToValidate": [
            {
                "address": {
                    "streetLines": address.street_lines,
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
        if other_party_email:
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
                    "streetLines": shipment.shipper_address.street_lines,
                    "city": shipment.shipper_address.city,
                    "stateOrProvinceCode": shipment.shipper_address.state_code,
                    "postalCode": shipment.shipper_address.postal_code,
                    "countryCode": shipment.shipper_address.country_code,
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
                        "streetLines": shipment.recipient_address.street_lines,
                        "city": shipment.recipient_address.city,
                        "stateOrProvinceCode": shipment.recipient_address.state_code,
                        "postalCode": shipment.recipient_address.postal_code,
                        "countryCode": shipment.recipient_address.country_code,
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
            "totalWeight": float(shipment.weight),
            "shippingChargesPayment": {"paymentType": "SENDER"},
            "shipmentSpecialServices": {
                "specialServiceTypes": ["EVENT_NOTIFICATION"],
            },
            "emailNotificationDetail": {
                "aggregationType": "PER_SHIPMENT",
                "emailNotificationRecipients": email_notifications_schema_list,
                "personalMessage": "You have a FedEx package on the way!"
            },
            "labelSpecification": {"labelStockType": "PAPER_4X6", "imageType": "PDF", "labelFormatType": "COMMON2D"},
            "requestedPackageLineItems": [
                {
                    "customerReferences": [
                        {"customerReferenceType": "CUSTOMER_REFERENCE", "value": shipment.reference},
                        {"customerReferenceType": "DEPARTMENT_NUMBER", "value": shipment.charge_code},
                    ],
                    "weight": {"units": "LB", "value": float(shipment.weight)}
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
                    "city": shipment.shipper_address.city,
                    "stateOrProvinceCode": shipment.shipper_address.state_code,
                    "postalCode": shipment.shipper_address.postal_code,
                    "countryCode": shipment.shipper_address.country_code,
                    "residential": shipment.shipper_address_is_residential,
                }
            },
            "recipient": {
                "address": {
                    "city": shipment.recipient_address.city,
                    "stateOrProvinceCode": shipment.recipient_address.state_code,
                    "postalCode": shipment.recipient_address.postal_code,
                    "countryCode": shipment.recipient_address.country_code,
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
                    "value": float(shipment.weight),
                },
            }
            ],
        },
    }

    return rates_schema