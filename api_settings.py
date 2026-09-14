from enum import Enum


class APIEnvironment(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


## CONFIG PROJECT ENVIRONMENT HERE
rates_API_config, ship_API_config = APIEnvironment.PRODUCTION, APIEnvironment.SANDBOX