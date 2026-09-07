from schema_classes import ShippingContact


sample_recipient = ShippingContact(
    street_line_one = "308 Negra Arroyo Ln",
    city = "Albuquerque",
    state_code= "NM",
    postal_code= "87104",
    country_code = "US",
    is_residential = True,
    full_name = "Walter White",
    email_address = "walter.white@graymatter.technologies",
    phone_number = "505-503-4455",
)

def get_sample_recipient_info():
    return sample_recipient