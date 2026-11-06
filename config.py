from enum import Enum


class APIEnvironment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


## CONFIG PROJECT ENVIRONMENT HERE
ship_API_config = APIEnvironment.PRODUCTION
rates_API_config = APIEnvironment.PRODUCTION
validation_API_config = APIEnvironment.PRODUCTION

LABEL_SUBDIR = "ShippingLabels"