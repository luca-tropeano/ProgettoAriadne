"""Pure-Python decompressor for LZ-String `decompressFromBase64` payloads.

Used to decode the BOM JSON embedded in KiCad Interactive HTML BOM (IBOM)
files:  `var pcbdata = JSON.parse(LZString.decompressFromBase64("..."))`.

Only the decompression path required by Ariadne is ported.  Section 5 of
LZW-style dictionary decompression, faithful to the reference lz-string
JavaScript library (MIT / pieroxy).  No third-party dependencies.
"""

from __future__ import annotations

KEY_STR_BASE64 = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
)
KEY_STR_URI_SAFE = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-$"
)

_base_reverse: dict[str, dict[str, int]] = {}


def _get_base_value(alphabet: str, character: str) -> int:
    if alphabet not in _base_reverse:
        _base_reverse[alphabet] = {
            i: index for index, i in enumerate(alphabet)
        }
    return _base_reverse[alphabet][character]


class _Data:
    __slots__ = ("val", "position", "index")

    def __init__(self, val: int, position: int, index: int):
        self.val = val
        self.position = position
        self.index = index


def _decompress(length: int, reset_value: int, get_next_value) -> str:
    dictionary: dict[int, str] = {}
    enlarge_in = 4
    dict_size = 4
    num_bits = 3
    entry = ""
    result: list[str] = []

    data = _Data(get_next_value(0), reset_value, index=1)

    for i in range(3):
        dictionary[i] = chr(i)

    bits = 0
    maxpower = 2 ** 2
    power = 1
    while power != maxpower:
        resb = data.val & data.position
        data.position >>= 1
        if data.position == 0:
            data.position = reset_value
            data.val = get_next_value(data.index)
            data.index += 1
        bits |= power if resb > 0 else 0
        power <<= 1

    next_val = bits
    if next_val == 0:
        bits = 0
        maxpower = 2 ** 8
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = reset_value
                data.val = get_next_value(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1
        c = chr(bits)
    elif next_val == 1:
        bits = 0
        maxpower = 2 ** 16
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = reset_value
                data.val = get_next_value(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1
        c = chr(bits)
    elif next_val == 2:
        return ""

    dictionary[3] = c
    w = c
    result.append(c)

    while True:
        if data.index > length:
            return ""

        bits = 0
        maxpower = 2 ** num_bits
        power = 1
        while power != maxpower:
            resb = data.val & data.position
            data.position >>= 1
            if data.position == 0:
                data.position = reset_value
                data.val = get_next_value(data.index)
                data.index += 1
            bits |= power if resb > 0 else 0
            power <<= 1

        c = bits
        if c == 0:
            bits = 0
            maxpower = 2 ** 8
            power = 1
            while power != maxpower:
                resb = data.val & data.position
                data.position >>= 1
                if data.position == 0:
                    data.position = reset_value
                    data.val = get_next_value(data.index)
                    data.index += 1
                bits |= power if resb > 0 else 0
                power <<= 1
            dictionary[dict_size] = chr(bits)
            dict_size += 1
            c = dict_size - 1
            enlarge_in -= 1
        elif c == 1:
            bits = 0
            maxpower = 2 ** 16
            power = 1
            while power != maxpower:
                resb = data.val & data.position
                data.position >>= 1
                if data.position == 0:
                    data.position = reset_value
                    data.val = get_next_value(data.index)
                    data.index += 1
                bits |= power if resb > 0 else 0
                power <<= 1
            dictionary[dict_size] = chr(bits)
            dict_size += 1
            c = dict_size - 1
            enlarge_in -= 1
        elif c == 2:
            return "".join(result)

        if enlarge_in == 0:
            enlarge_in = 2 ** num_bits
            num_bits += 1

        if c in dictionary:
            entry = dictionary[c]
        else:
            if c == dict_size:
                entry = w + w[0]
            else:
                return None  # type: ignore[return-value]

        result.append(entry)

        dictionary[dict_size] = w + entry[0]
        dict_size += 1
        enlarge_in -= 1

        w = entry
        if enlarge_in == 0:
            enlarge_in = 2 ** num_bits
            num_bits += 1


def decompress_from_base64(compressed: str | None) -> str | None:
    """Decompress an LZ-String base64-encoded payload to a UTF-8 string.

    Returns ``None`` for empty or invalid input (mirrors the JS empty-string
    null semantics), otherwise the decompressed string.
    """
    if compressed is None:
        return ""
    if compressed == "":
        return None
    try:
        result = _decompress(
            len(compressed),
            32,
            lambda index: _get_base_value(KEY_STR_BASE64, compressed[index]),
        )
    except (IndexError, KeyError, ValueError):
        return None
    return result


def decompress(compressed: str | None) -> str | None:
    """Decompress a plain LZ-String payload (16-bit/char variant)."""
    if compressed is None:
        return ""
    if compressed == "":
        return None
    return _decompress(len(compressed), 32768, lambda index: ord(compressed[index]))
