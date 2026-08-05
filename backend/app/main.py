import sqlite3

import svcs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from svcs.fastapi import DepContainer, lifespan as svcs_lifespan

from .db import make_connection_factory
from .services import ItemService, item_service_factory


def register_services(registry: svcs.Registry) -> None:
    registry.register_factory(sqlite3.Connection, make_connection_factory)
    registry.register_factory(ItemService, item_service_factory)


app = FastAPI(title="Earned API", lifespan=svcs_lifespan)
app.state.registry = svcs.Registry()
register_services(app.state.registry)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/items")
async def list_items(services: DepContainer):
    item_service = await services.aget(ItemService)
    return {"items": item_service.list_names()}


@app.post("/api/items")
async def add_item(name: str, services: DepContainer):
    item_service = await services.aget(ItemService)
    item_service.add(name)
    return {"items": item_service.list_names()}
