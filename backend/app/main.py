import sqlite3
from datetime import date
from typing import Literal

import svcs
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from svcs.fastapi import DepContainer, lifespan as svcs_lifespan

from .constants import CATEGORIES, STAKES
from .db import make_connection_factory
from .services import CommitmentService, commitment_service_factory


async def register_services(app: FastAPI, registry: svcs.Registry):
    registry.register_factory(sqlite3.Connection, make_connection_factory)
    registry.register_factory(CommitmentService, commitment_service_factory)
    yield


app = FastAPI(title="Earned API", lifespan=svcs_lifespan(register_services))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # spec/api.md §1 — error shape is { "error": { "code", "message", "field" } }
    errors = exc.errors()
    first = errors[0] if errors else {}
    loc = [str(p) for p in first.get("loc", ()) if p != "body"]
    field = ".".join(loc) or None
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": first.get("msg", "Invalid request"),
                "field": field,
            }
        },
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# spec/spec.md §5.2, spec/api.md §10 — POST /api/commitments


class CommitmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    category: Literal[*CATEGORIES]
    stakes: Literal[*STAKES]
    deadline: date
    effort_minutes: int = Field(gt=0)
    proposed_effort_minutes: int | None = None
    source: Literal["parsed", "manual"]


class CommitmentsCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    commitments: list[CommitmentIn] = Field(min_length=1)


@app.post("/api/commitments", status_code=201)
async def create_commitments(
    payload: CommitmentsCreateRequest, services: DepContainer
):
    commitment_service = await services.aget(CommitmentService)
    items = [
        {
            "title": c.title,
            "category": c.category,
            "stakes": c.stakes,
            "deadline": c.deadline.isoformat(),
            "effort_minutes": c.effort_minutes,
            "proposed_effort_minutes": c.proposed_effort_minutes,
            "source": c.source,
        }
        for c in payload.commitments
    ]
    created = commitment_service.create_commitments(items)
    return {"commitments": created}
