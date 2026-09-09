"""Client Strapi REST API per sincronizzazione dati.

Sincronizza Device e BOMEntry verso un'istanza Strapi (headless CMS).
Strapi espone CRUD automatiche su `/api/<nome-plurale>`. Questo client fornisce
le operazioni usate dalla pipeline per caricare i dati elaborati.

Il DB sottostante a Strapi è PostgreSQL (produzione) / SQLite (dev).
Questo client NON dipende da MongoDB (che resta solo per i dati grezzi).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ariadne.models import BOMEntry, Device

logger = logging.getLogger("ariadne.strapi")

# Nome plurale dei Collection Type Strapi
DEVICE_EP = "devices"
BOM_ENTRY_EP = "bom-entries"


class StrapiClient:
    def __init__(self, base_url: str, api_token: str = "", timeout: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        headers = {"Content-Type": "application/json"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        self._client = httpx.Client(base_url=self._base_url, headers=headers, timeout=timeout)

    # ------------------------------------------------------------------ HTTP

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._api_token:
            h["Authorization"] = f"Bearer {self._api_token}"
        return h

    def _post(self, path: str, data: dict) -> dict[str, Any]:
        resp = self._client.post(path, json={"data": data}, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str, params: dict | None = None) -> dict[str, Any]:
        resp = self._client.get(path, params=params, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    def _find_id(self, path: str, filter_field: str, filter_value: str) -> int | None:
        """Cerca un record Strapi per campo univoco e restituisce l'id, se esiste."""
        try:
            data = self._get(
                path,
                params={"filters": {filter_field: {"$eq": filter_value}}, "pagination": {"limit": 1}},
            )
        except Exception:
            return None
        items = data.get("data") or []
        if items:
            return items[0]["id"]
        return None

    # --------------------------------------------------------------- Devices

    def upsert_device(self, device: Device) -> int:
        """Crea o aggiorna un Device per modelName univoco. Ritorna l'id Strapi."""
        existing = self._find_id(DEVICE_EP, "modelName", device.model_name)
        payload = {
            "brand": device.brand,
            "modelName": device.model_name,
            "manufacturer": device.manufacturer,
            "yearOfProduction": device.year_of_production,
            "notes": device.notes,
        }
        if existing is not None:
            resp = self._client.put(
                f"/api/{DEVICE_EP}/{existing}",
                json={"data": payload},
                headers=self._headers(),
            )
            resp.raise_for_status()
            logger.info("Strapi device updated: %s (id=%s)", device.model_name, existing)
            return existing
        resp = self._post(f"/api/{DEVICE_EP}", payload)
        new_id = resp["data"]["id"]
        logger.info("Strapi device created: %s (id=%s)", device.model_name, new_id)
        return new_id

    def push_bom_entry(self, device: Device, entry: BOMEntry, device_strapi_id: int) -> int:
        """Crea un BOMEntry su Strapi collegato al device. Ritorna l'id Strapi."""
        payload = {
            "itemNumber": entry.item_number,
            "quantity": entry.quantity,
            "referenceDesignator": entry.reference_designator,
            "partValue": entry.part_value,
            "package": entry.package,
            "manufacturer": entry.manufacturer,
            "manufacturerOrderCode": entry.manufacturer_order_code,
            "supplier": entry.supplier,
            "supplierOrderCode": entry.supplier_order_code,
            "notes": entry.notes,
            "mountingType": entry.mounting_type,
            "eecCategoryId": entry.eec_category_id,
            "device": device_strapi_id,
        }
        resp = self._post(f"/api/{BOM_ENTRY_EP}", payload)
        new_id = resp["data"]["id"]
        logger.debug("Strapi bom_entry created (id=%s)", new_id)
        return new_id

    # -------------------------------------------------------------- Sync

    def sync_device(self, device: Device, entries: list[BOMEntry]) -> dict[str, int]:
        """Sincronizza un device completo (device + tutte le sue BOMEntry) su Strapi."""
        device_strapi_id = self.upsert_device(device)
        created = 0
        for entry in entries:
            self.push_bom_entry(device, entry, device_strapi_id)
            created += 1
        logger.info("Strapi sync complete: device %s, %d bom entries pushed", device.model_name, created)
        return {"device_id": device_strapi_id, "entries_pushed": created}

    # -------------------------------------------------------------- utility

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
