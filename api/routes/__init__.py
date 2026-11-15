"""Combined APIRouter that includes all sub-routers in the same path order as the original routes.py."""
from __future__ import annotations

from fastapi import APIRouter

from api.routes import ask, compare, fields, meta, methods

router = APIRouter()

# Meta: /health, /meta/constraint-options
router.include_router(meta.router)

# Fields: /fields/demo must come before /fields/{field_id}
router.include_router(fields.router)

# Compare and analyses: /fields/{id}/compare, /analyses/{id}
router.include_router(compare.router)

# Evidence and methods: /evidence/marsden, /lineage/{id}, /sources, /indicators
router.include_router(methods.router)

# Ask: /analyses/{id}/ask, /fields/{id}/ask
router.include_router(ask.router)
