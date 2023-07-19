import io
import base64
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
except ImportError as e:
    logger.warn("pandas not found")

def read_bas64_csv(base64_string: "str") -> "pd.DataFrame":
    csv_bytes = base64.b64decode(base64_string)
    csv_text = csv_bytes.decode('latin-1')
    csv_text = io.StringIO(csv_text)
    df = pd.read_csv(csv_text)
    return df
    