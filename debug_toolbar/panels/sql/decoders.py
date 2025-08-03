import base64
import json


class DebugToolbarJSONDecoder(json.JSONDecoder):
    """Custom JSON decoder that reconstructs binary data during parsing."""

    def decode(self, s):
        """Override decode to apply reconstruction after parsing."""
        obj = super().decode(s)
        return self._reconstruct_params(obj)

    def _reconstruct_params(self, params):
        """Reconstruct parameters, handling lists and dicts recursively."""
        if isinstance(params, list):
            return [self._reconstruct_params(param) for param in params]
        elif isinstance(params, dict):
            if "__djdt_binary__" in params:
                return base64.b64decode(params["__djdt_binary__"])
            else:
                return {
                    key: self._reconstruct_params(value)
                    for key, value in params.items()
                }
        else:
            return params
