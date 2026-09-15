import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .config import EARNED_USER_ID


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class CommitmentService:
    conn: sqlite3.Connection

    def create_commitments(self, items: list[dict]) -> list[dict]:
        """spec/api.md §10 — one endpoint, two callers, same validation both ways.
        Nothing touches the database until the whole batch is valid (decisions.md §5)."""
        created_at = _now_iso()
        rows = []
        for item in items:
            rows.append(
                {
                    "id": f"cm_{uuid.uuid4().hex}",
                    "user_id": EARNED_USER_ID,
                    "title": item["title"],
                    "category": item["category"],
                    "stakes": item["stakes"],
                    "deadline": item["deadline"],
                    "effort_minutes": item["effort_minutes"],
                    "proposed_effort_minutes": item.get("proposed_effort_minutes"),
                    "source": item["source"],
                    "status": "open",
                    "created_at": created_at,
                }
            )

        try:
            for row in rows:
                self.conn.execute(
                    """
                    INSERT INTO commitment (
                        id, user_id, title, category, stakes, deadline,
                        effort_minutes, proposed_effort_minutes, source,
                        status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["id"],
                        row["user_id"],
                        row["title"],
                        row["category"],
                        row["stakes"],
                        row["deadline"],
                        row["effort_minutes"],
                        row["proposed_effort_minutes"],
                        row["source"],
                        row["status"],
                        row["created_at"],
                    ),
                )
        except sqlite3.Error:
            self.conn.rollback()
            raise
        self.conn.commit()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "category": row["category"],
                "stakes": row["stakes"],
                "deadline": row["deadline"],
                "effort_minutes": row["effort_minutes"],
                "proposed_effort_minutes": row["proposed_effort_minutes"],
                "source": row["source"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]


def commitment_service_factory(svcs_container):
    conn = svcs_container.get(sqlite3.Connection)
    yield CommitmentService(conn)
