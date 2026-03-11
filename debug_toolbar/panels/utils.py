def convert_keys_to_strings(obj):
    """
    Recursively convert non-string dictionary keys to strings.

    This ensures data is JSON-serializable before being passed to the store.

    Args:
        obj: Any Python object (dict, list, tuple, or primitive)

    Returns:
        Object with all dict keys converted to strings
    """
    from uuid import UUID

    if isinstance(obj, dict):
        result = {
            str(k)
            if not isinstance(k, (str, int, float, bool, type(None)))
            else k: convert_keys_to_strings(v)
            for k, v in obj.items()
        }
        return result
    elif isinstance(obj, tuple):
        result = str(obj)
        return result
    elif isinstance(obj, UUID):
        result = str(obj)
        return result
    elif isinstance(obj, list):
        result = [convert_keys_to_strings(item) for item in obj]
        return result
    return obj
