"""Parsing di Material Composition Declaration IPC-1752A/B — Class D (XML).

Struttura di riferimento: schema ufficiale IPC-1752A (Amendment 3),
file "IPC 1752A Amendment 3 Schema.xsd" (targetNamespace
``http://webstds.ipc.org/175x/2.0``, root ``<MainDeclaration>``).

Percorso Class D "Material Composition Declaration — Homogeneous Material
Level" (campo di Table A1-5 dello standard)::

    MainDeclaration
      └─ Product                                      (@unitType)
          ├─ ProductID                                (@itemName, @itemNumber, ...)
          └─ MaterialInfo
              └─ HomogeneousMaterialList
                  └─ HomogeneousMaterial              (@name, @materialGroupName, @comment)
                      ├─ Amount                        (@value, @UOM ∈ {mg,g,kg,ppm,massPercent})
                      └─ SubstanceCategoryList
                          └─ SubstanceCategory         (@name)
                              └─ Substance             (@name)
                                  ├─ SubstanceID       (= UniqueID @identity, @authority=CAS)
                                  ├─ Amount            (@value, @UOM)
                                  └─ Concentration     (@value, massa %)

Il parser è deliberatamente "namespace-tolorente": confronta i nomi locali
dei tag (strippando ``{...}``), così da reggere sia file con prefisso
namespace che file senza, e varianti B/Am3. Funziona su XML validati contro
questo schema; documenti legacy v1.x (i vecchi PDF form 1752-1/2) NON sono
supportati.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

#: Conteggio masse per creare la massa assoluta in mg.
_MASS_TO_MG = {"mg": 1.0, "g": 1000.0, "kg": 1_000_000.0}

#: UOM che rappresentano una concentrazione, non una massa assoluta.
_CONCENTRATION_UOMS = {"ppm", "masspercent"}


@dataclass
class DeclaredSubstance:
    """Una sostanza dichiarata dentro un materiale omogeneo."""

    name: str
    cas: str | None = None
    mass_mg: float | None = None
    concentration_pct: float | None = None


@dataclass
class HomogeneousMaterial:
    """Materiale omogeneo (es. ceramica del dielettrico, terminale, plating)."""

    name: str
    mass_mg: float | None = None
    material_group: str | None = None
    substances: list["DeclaredSubstance"] = field(default_factory=list)


@dataclass
class ClassDProduct:
    """Un prodotto dichiarato, con i suoi materiali omogenei (Class D)."""

    product_name: str | None = None
    item_numbers: list[str] = field(default_factory=list)
    homogeneous_materials: list["HomogeneousMaterial"] = field(default_factory=list)


def _local(tag: str) -> str:
    """Nome locale di un tag (ignora namespace)."""
    return tag.rsplit("}", 1)[-1]


def _attr(element: ET.Element | None, name: str) -> str | None:
    """Attributo opzionale, con fallback al nome senza namespace."""

    def _get(e, k):
        for key in (k, "{http://webstds.ipc.org/175x/2.0}" + k):
            if key in e.attrib:
                return e.attrib[key]
        return None

    if element is None:
        return None
    value = _get(element, name)
    return value.strip() if isinstance(value, str) else value


def _amount_to_mg(amount: ET.Element | None) -> float | None:
    """Converte un elemento ``Amount`` (``@value``, ``@UOM``) in massa mg.

    Se la UOM è una concentrazione (ppm/massPercent) ritorna None.
    """
    if amount is None:
        return None
    raw_value = _attr(amount, "value")
    uom = (_attr(amount, "UOM") or "mg").lower()
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return None
    if uom in _CONCENTRATION_UOMS:
        return None
    return value * _MASS_TO_MG.get(uom, 1.0)


def _amount_to_pct(amount: ET.Element | None) -> float | None:
    """Converte un ``Amount`` espresso come concentrazione in percentuale massa."""
    if amount is None:
        return None
    uom = (_attr(amount, "UOM") or "").lower()
    try:
        value = float(_attr(amount, "value"))
    except (TypeError, ValueError):
        return None
    if uom == "ppm":
        return value / 10_000.0
    if uom in {"masspercent", "mass"} or "%" in uom:
        return value
    return None


def _parse_substance(elem: ET.Element) -> DeclaredSubstance | None:
    name = (_attr(elem, "name") or "").strip()
    if not name:
        return None

    cas: str | None = None
    authority: str | None = None
    for sub_id in elem.iter():
        if _local(sub_id.tag) not in ("SubstanceID", "UniqueID"):
            continue
        identity = (_attr(sub_id, "identity") or "").strip()
        auth = (_attr(sub_id, "authority") or "").strip().upper()
        if identity and (auth == "CAS" or cas is None):
            cas, authority = identity, auth or authority

    amount = next((e for e in elem if _local(e.tag) == "Amount"), None)
    concentration = next((e for e in elem if _local(e.tag) == "Concentration"), None)

    mass_mg = _amount_to_mg(amount)
    if mass_mg is None and amount is not None:
        # Amount espresso come concentrazione (ppm / mass%) → nessuna massa assoluta
        pct = _amount_to_pct(amount)
        concentration_pct = pct
    elif concentration is not None:
        try:
            concentration_pct = float(_attr(concentration, "value"))
        except (TypeError, ValueError):
            concentration_pct = None
    else:
        concentration_pct = None

    return DeclaredSubstance(name=name, cas=cas, mass_mg=mass_mg,
                             concentration_pct=concentration_pct)


def _parse_homogeneous_material(elem: ET.Element) -> HomogeneousMaterial:
    name = (_attr(elem, "name") or "").strip() or "un-named"
    amount = next((e for e in elem if _local(e.tag) == "Amount"), None)
    material = HomogeneousMaterial(
        name=name,
        mass_mg=_amount_to_mg(amount),
        material_group=_attr(elem, "materialGroupName"),
    )
    for sub_elem in elem.iter():
        if _local(sub_elem.tag) != "Substance":
            continue
        sub = _parse_substance(sub_elem)
        if sub is not None:
            material.substances.append(sub)
    return material


def parse_class_d_xml(xml_text: str) -> list["ClassDProduct"]:
    """Estrae i prodotti Class D (materiali omogenei + sostanze) da un XML IPC-1752A/B.

    Ritorna una lista di :class:`ClassDProduct`. Solleva ``ValueError`` se il
    documento non è riconosciuto come IPC-1752A/B (nessun ``Product`` con
    ``HomogeneousMaterial``).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"XML malformato: {exc}") from exc

    products: list[ClassDProduct] = []
    for prod in root.iter():
        if _local(prod.tag) != "Product":
            continue

        product = ClassDProduct()
        for pid in prod.iter():
            if _local(pid.tag) != "ProductID":
                continue
            item_name = _attr(pid, "itemName")
            item_number = _attr(pid, "itemNumber")
            if item_name and not product.product_name:
                product.product_name = item_name
            if item_number:
                product.item_numbers.append(item_number)

        for hm in prod.iter():
            if _local(hm.tag) != "HomogeneousMaterial":
                continue
            product.homogeneous_materials.append(_parse_homogeneous_material(hm))

        if product.homogeneous_materials:
            products.append(product)

    if not products:
        raise ValueError(
            "Non riconosciuto come IPC-1752A/B Class D: "
            "nessun Product con HomogeneousMaterial trovato."
        )
    return products