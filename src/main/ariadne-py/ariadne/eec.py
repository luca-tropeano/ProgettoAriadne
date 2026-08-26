from __future__ import annotations

_EEC_MAP: dict[str, int] = {
    "R": 1,
    "C": 2,
    "L": 3,
    "D": 4,
    "Q": 5,
    "U": 6,
    "J": 7,
    "CN": 7,
    "SW": 8,
    "T": 9,
    "F": 10,
    "X": 11,
    "Y": 11,
    "LED": 12,
    "TP": 16,
    "K": 7,
    "BT": 15,
    "EMI": 16,
    "JP": 16,
    "Module": 16,
}

_EEC_NAMES = {
    1: "Resistors",
    2: "Capacitors",
    3: "Inductors",
    4: "Diodes",
    5: "Transistors",
    6: "Integrated Circuits",
    7: "Connectors",
    8: "Switches",
    9: "Transformers",
    10: "Fuses",
    11: "Crystals/Oscillators",
    12: "LEDs",
    13: "Sensors",
    14: "Actuators",
    15: "Batteries",
    16: "Other",
}


def classify_designator(designator: str) -> int | None:
    if not designator:
        return None
    prefix = designator.strip().upper()
    for key in sorted(_EEC_MAP, key=len, reverse=True):
        if prefix.startswith(key):
            return _EEC_MAP[key]
    return 16


def eec_name(category_id: int) -> str:
    return _EEC_NAMES.get(category_id, "Other")


def classify_all(designators: str) -> int | None:
    if not designators:
        return None
    text = designators.replace(";", ",")
    if "," in text:
        parts = [p.strip() for p in text.split(",") if p.strip()]
    else:
        parts = [p.strip() for p in text.split() if p.strip()]
    counts: dict[int, int] = {}
    for part in parts:
        prefix = "".join(c for c in part if c.isalpha())
        cat = classify_designator(prefix)
        if cat:
            counts[cat] = counts.get(cat, 0) + 1
    if not counts:
        return 16
    return max(counts, key=counts.get)
