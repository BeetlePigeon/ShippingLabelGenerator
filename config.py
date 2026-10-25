from enum import Enum


class APIEnvironment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


## CONFIG PROJECT ENVIRONMENT HERE
rates_API_config = APIEnvironment.PRODUCTION
ship_API_config = APIEnvironment.PRODUCTION
validation_API_config = APIEnvironment.PRODUCTION

DEFAULT_SHIPMENT_WEIGHT = "8"