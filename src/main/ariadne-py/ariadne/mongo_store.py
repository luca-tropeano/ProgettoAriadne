"""MongoDB raw-data storage.

Archivia i documenti sorgente (grezzi) prima dell'elaborazione della BOM.
L'archivio è opzionale: se MongoDB non è raggiungibile, la pipeline continua
senza errore (graceful degradation) e lo store viene segnalato come inattivo.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any

from ariadne.config import MongoConfig

logger = logging.getLogger("ariadne.mongo")

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError

    _HAS_PYMONGO = True
except ImportError:  # pragma: no cover
    MongoClient = None
    PyMongoError = None
    _HAS_PYMONGO = False


class RawDataStore:
    """Salva i documenti BOM grezzi in MongoDB (collection `bom_files`)."""

    def __init__(self, config: MongoConfig):
        self._config = config
        self._client = None
        self._collection = None
        self.available = False
        if _HAS_PYMONGO:
            self._connect()

    def _connect(self) -> None:
        try:
            self._client = MongoClient(
                self._config.uri,
                serverSelectionTimeoutMS=1500,
            )
            db = self._client[self._config.database]
            self._collection = db[self._config.collection]
            self._client.admin.command("ping")
            self.available = True
            logger.info(
                "MongoDB connected: %s/%s.%s",
                self._config.uri,
                self._config.database,
                self._config.collection,
            )
        except (PyMongoError, Exception) as e:
            logger.warning("MongoDB not available (%s); raw storage disabled", e)
            self._client = None
            self._collection = None
            self.available = False

    @staticmethod
    def _content_hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def store(
        self,
        filename: str,
        file_format: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> str | None:
        """Salva un documento grezzo. Restituisce l'ObjectId (str) o None se inattivo."""
        if not self.available or self._collection is None:
            logger.debug("Raw storage skipped (MongoDB unavailable)")
            return None

        doc = {
            "filename": filename,
            "file_format": file_format,
            "content": content,
            "content_hash": self._content_hash(content),
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc),
        }
        try:
            result = self._collection.insert_one(doc)
            doc_id = str(result.inserted_id)
            logger.info("Raw document stored: %s (id=%s)", filename, doc_id)
            return doc_id
        except (PyMongoError, Exception) as e:
            logger.warning("Failed to store raw document %s: %s", filename, e)
            return None

    def count(self) -> int:
        if not self.available or self._collection is None:
            return 0
        try:
            return self._collection.count_documents({})
        except (PyMongoError, Exception) as e:
            logger.warning("MongoDB count failed: %s", e)
            return 0

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._collection = None
            self.available = False
