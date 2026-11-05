import logging
import os
from pathlib import Path


log_dir = Path(os.environ["LOCALAPPDATA"]) / "ASCShippingLabelTool"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=log_dir / "errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s -%(message)s"
)