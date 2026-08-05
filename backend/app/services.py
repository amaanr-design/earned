import sqlite3
from dataclasses import dataclass


@dataclass
class ItemService:
    conn: sqlite3.Connection

    def list_names(self) -> list[str]:
        rows = self.conn.execute("SELECT name FROM items ORDER BY id").fetchall()
        return [row["name"] for row in rows]

    def add(self, name: str) -> None:
        self.conn.execute("INSERT INTO items (name) VALUES (?)", (name,))
        self.conn.commit()


def item_service_factory(svcs_container):
    conn = svcs_container.get(sqlite3.Connection)
    yield ItemService(conn)
