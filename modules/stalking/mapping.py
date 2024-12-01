from datetime import datetime, UTC
from typing import Any, Dict


def convert_response_to_entry(data: Any) -> Dict[str, Any]:
    return {'data': data, 'timestamp': datetime.now(UTC)}
