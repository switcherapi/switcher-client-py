import json
from typing import Any, List, Union


def payload_reader(payload: Any) -> List[str]:
    """Extract all field keys from a JSON payload structure.
    
    This function recursively traverses a JSON structure
    and returns all possible field paths in dot notation.
    """
    # Handle string payload - if it's a string, try to parse it as JSON
    if isinstance(payload, str):
        parsed = parse_json(payload)
        if parsed is not None:
            payload = parsed
    
    # If payload is a list/array, recursively process each element
    if isinstance(payload, list):
        result = []
        for item in payload:
            result.extend(payload_reader(item))
        return result
    
    # If payload is not a dict, return empty list (primitive values don't have keys)
    if not isinstance(payload, dict):
        return []
    
    # Process dictionary keys
    result = []
    
    for field in payload.keys():
        result.append(field)
        nested_fields = payload_reader(payload[field])
        for nested_field in nested_fields:
            result.append(f"{field}.{nested_field}")

    return result

def parse_json(json_str: str) -> Union[Any, None]:
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return None
