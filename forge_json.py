"""Strict local JSON parsing shared by the optional helpers (standard library only)."""
import json
import math
from pathlib import Path


def loads(text):
    def unique(pairs):
        result = {}
        for k, v in pairs:
            if k in result:
                raise ValueError('duplicate JSON key: ' + k)
            result[k] = v
        return result

    def invalid(value):
        raise ValueError('non-finite JSON: ' + value)

    def finite_float(value):
        n = float(value)
        if not math.isfinite(n):
            raise ValueError('JSON number out of finite float range')
        return n

    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=invalid, parse_float=finite_float)


def load(path):
    return loads(Path(path).read_text(encoding='utf-8'))
