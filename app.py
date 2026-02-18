from __future__ import annotations

import json
import sqlite3
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "recipes.db"
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"


class RecipeStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        self._seed_default_data()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    notes TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    recipe_id INTEGER NOT NULL,
                    ingredient_id INTEGER NOT NULL,
                    grams_per_kg REAL NOT NULL,
                    PRIMARY KEY (recipe_id, ingredient_id),
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                    FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE RESTRICT
                );
                """
            )

    def _seed_default_data(self) -> None:
        with self._connect() as conn:
            ingredients_count = conn.execute("SELECT COUNT(*) AS total FROM ingredients").fetchone()["total"]
            if ingredients_count == 0:
                defaults = ["Leche entera", "Nata montar", "LPD", "Yemas", "Sacarosa"]
                for ingredient in defaults:
                    conn.execute("INSERT INTO ingredients (name) VALUES (?)", (ingredient,))

            recipe_count = conn.execute("SELECT COUNT(*) AS total FROM recipes").fetchone()["total"]
            if recipe_count > 0:
                return

            conn.execute(
                "INSERT INTO recipes (name, notes) VALUES (?, ?)",
                ("Stracciatella", "Receta base de ejemplo para arrancar."),
            )
            recipe_id = conn.execute("SELECT id FROM recipes WHERE name = ?", ("Stracciatella",)).fetchone()["id"]
            grams_map = {
                "Leche entera": 333,
                "Nata montar": 292,
                "LPD": 83,
                "Yemas": 83,
                "Sacarosa": 208,
            }
            for ingredient, grams in grams_map.items():
                ingredient_id = conn.execute(
                    "SELECT id FROM ingredients WHERE name = ?", (ingredient,)
                ).fetchone()["id"]
                conn.execute(
                    "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, grams_per_kg) VALUES (?, ?, ?)",
                    (recipe_id, ingredient_id, grams),
                )

    def list_recipes(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id, name, notes FROM recipes ORDER BY name ASC").fetchall()
            return [dict(row) for row in rows]

    def create_recipe(self, name: str, notes: str, items: list[dict]) -> tuple[dict | None, str | None]:
        name = name.strip()
        notes = notes.strip()
        if not name:
            return None, "El nombre de la receta es obligatorio."
        if not items:
            return None, "Debes añadir al menos un ingrediente."

        try:
            with self._connect() as conn:
                recipe_id = conn.execute(
                    "INSERT INTO recipes (name, notes) VALUES (?, ?)", (name, notes)
                ).lastrowid

                used_ingredients: set[int] = set()
                for item in items:
                    ingredient_id = int(item.get("ingredient_id") or 0)
                    grams_per_kg = float(item.get("grams_per_kg") or 0)
                    if ingredient_id <= 0 or grams_per_kg <= 0:
                        return None, "Cada ingrediente necesita selección y gramos por kg válidos."
                    if ingredient_id in used_ingredients:
                        return None, "No repitas ingredientes dentro de la misma receta."
                    exists = conn.execute(
                        "SELECT id FROM ingredients WHERE id = ?", (ingredient_id,)
                    ).fetchone()
                    if not exists:
                        return None, "Ingrediente seleccionado no existe."
                    used_ingredients.add(ingredient_id)

                    conn.execute(
                        "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, grams_per_kg) VALUES (?, ?, ?)",
                        (recipe_id, ingredient_id, grams_per_kg),
                    )

                recipe = conn.execute(
                    "SELECT id, name, notes FROM recipes WHERE id = ?", (recipe_id,)
                ).fetchone()
                return dict(recipe), None
        except sqlite3.IntegrityError:
            return None, "Ya existe una receta con ese nombre."

    def calculate_recipe(self, recipe_id: int, kg: float) -> tuple[dict | None, str | None]:
        if kg <= 0:
            return None, "Los kilos deben ser mayores a cero."

        with self._connect() as conn:
            recipe = conn.execute("SELECT id, name FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
            if recipe is None:
                return None, "Receta no encontrada."

            rows = conn.execute(
                """
                SELECT i.name, ri.grams_per_kg
                FROM recipe_ingredients ri
                JOIN ingredients i ON i.id = ri.ingredient_id
                WHERE ri.recipe_id = ?
                ORDER BY i.name ASC
                """,
                (recipe_id,),
            ).fetchall()

            return (
                {
                    "recipe": recipe["name"],
                    "kg": kg,
                    "result": [
                        {"ingredient": row["name"], "grams": round(row["grams_per_kg"] * kg, 2)}
                        for row in rows
                    ],
                },
                None,
            )

    def list_ingredients(self, order: str = "asc") -> list[dict]:
        order_sql = "DESC" if order.lower() == "desc" else "ASC"
        with self._connect() as conn:
            rows = conn.execute(f"SELECT id, name FROM ingredients ORDER BY name {order_sql}").fetchall()
            data: list[dict] = []
            for row in rows:
                recipes = conn.execute(
                    """
                    SELECT r.name
                    FROM recipe_ingredients ri
                    JOIN recipes r ON r.id = ri.recipe_id
                    WHERE ri.ingredient_id = ?
                    ORDER BY r.name ASC
                    """,
                    (row["id"],),
                ).fetchall()
                data.append(
                    {
                        "id": row["id"],
                        "name": row["name"],
                        "present_in": [rec["name"] for rec in recipes],
                    }
                )
            return data

    def create_ingredient(self, name: str) -> tuple[dict | None, str | None]:
        clean = name.strip()
        if not clean:
            return None, "El nombre del ingrediente es obligatorio."
        try:
            with self._connect() as conn:
                ingredient_id = conn.execute(
                    "INSERT INTO ingredients (name) VALUES (?)", (clean,)
                ).lastrowid
                return {"id": ingredient_id, "name": clean}, None
        except sqlite3.IntegrityError:
            return None, "Ya existe un ingrediente con ese nombre."

    def delete_ingredient(self, ingredient_id: int) -> tuple[bool, str | None]:
        with self._connect() as conn:
            in_use = conn.execute(
                "SELECT COUNT(*) AS total FROM recipe_ingredients WHERE ingredient_id = ?", (ingredient_id,)
            ).fetchone()["total"]
            if in_use > 0:
                return False, "No se puede borrar: está usado en una receta."
            deleted = conn.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,)).rowcount
            if deleted == 0:
                return False, "Ingrediente no encontrado."
            return True, None


STORE = RecipeStore(DATABASE_PATH)


class AppHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: HTTPStatus, payload: dict | list) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path == "/":
            content = TEMPLATE_PATH.read_bytes()
            self._send_text(HTTPStatus.OK, content, "text/html; charset=utf-8")
            return

        if parsed.path.startswith("/static/"):
            file_path = STATIC_DIR / parsed.path.replace("/static/", "", 1)
            if not file_path.exists() or not file_path.is_file():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Archivo no encontrado."})
                return
            content_type = "text/plain; charset=utf-8"
            if file_path.suffix == ".css":
                content_type = "text/css; charset=utf-8"
            elif file_path.suffix == ".js":
                content_type = "application/javascript; charset=utf-8"
            self._send_text(HTTPStatus.OK, file_path.read_bytes(), content_type)
            return

        if parsed.path == "/api/recipes":
            self._send_json(HTTPStatus.OK, STORE.list_recipes())
            return

        if parsed.path.startswith("/api/recipes/") and parsed.path.endswith("/calculate"):
            parts = parsed.path.strip("/").split("/")
            recipe_id = int(parts[2])
            params = parse_qs(parsed.query)
            kg = float(params.get("kg", ["0"])[0])
            data, error = STORE.calculate_recipe(recipe_id, kg)
            if error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": error})
                return
            self._send_json(HTTPStatus.OK, data)
            return

        if parsed.path == "/api/ingredients":
            params = parse_qs(parsed.query)
            order = params.get("order", ["asc"])[0]
            self._send_json(HTTPStatus.OK, STORE.list_ingredients(order=order))
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada."})

    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_payload = self.rfile.read(content_length)
        payload = json.loads(raw_payload or b"{}")

        if self.path == "/api/recipes":
            recipe, error = STORE.create_recipe(
                name=payload.get("name", ""),
                notes=payload.get("notes", ""),
                items=payload.get("items", []),
            )
            if error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": error})
                return
            self._send_json(HTTPStatus.CREATED, recipe)
            return

        if self.path == "/api/ingredients":
            ingredient, error = STORE.create_ingredient(payload.get("name", ""))
            if error:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": error})
                return
            self._send_json(HTTPStatus.CREATED, ingredient)
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada."})

    def do_DELETE(self) -> None:  # noqa: N802
        if not self.path.startswith("/api/ingredients/"):
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Ruta no encontrada."})
            return

        ingredient_id = int(self.path.split("/")[-1])
        deleted, error = STORE.delete_ingredient(ingredient_id)
        if not deleted:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": error})
            return
        self._send_text(HTTPStatus.NO_CONTENT, b"", "text/plain; charset=utf-8")


def run_server(host: str = "0.0.0.0", port: int = 5000) -> None:
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Servidor activo en http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
