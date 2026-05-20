import os
import sqlite3
from contextlib import contextmanager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
DB_PATH = os.path.join(DATA_DIR, "tc3d_hub.db")


def ensure_database() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client TEXT NOT NULL,
                project_name TEXT NOT NULL,
                status TEXT NOT NULL,
                delivery_date TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS company_metrics (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                monthly_billing REAL NOT NULL,
                pending_quotes INTEGER NOT NULL,
                pending_payments REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS production_metrics (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                pending_renders INTEGER NOT NULL,
                estimated_hours INTEGER NOT NULL,
                available_pcs INTEGER NOT NULL,
                render_queue TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS quick_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT NOT NULL,
                url TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                client TEXT NOT NULL,
                meeting_date TEXT NOT NULL,
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS meeting_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                task_text TEXT NOT NULL,
                is_done INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id) ON DELETE CASCADE
            );
            """
        )
        connection.commit()
        seed_data(connection)


def seed_data(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()

    if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO projects (
                client, project_name, status, delivery_date, amount, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Promociones Rivera",
                    "Infografias vivienda piloto",
                    "En produccion",
                    "2026-05-24",
                    1450,
                    "Faltan 2 renders exteriores",
                ),
                (
                    "Estudio Armonia",
                    "Render cocina premium",
                    "Revision cliente",
                    "2026-05-22",
                    680,
                    "Esperando feedback final",
                ),
                (
                    "Habita Norte",
                    "Tour 3D adosados",
                    "Pendiente inicio",
                    "2026-05-29",
                    2100,
                    "Presupuesto aprobado esta semana",
                ),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM company_metrics").fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO company_metrics (
                id, monthly_billing, pending_quotes, pending_payments
            ) VALUES (1, 4230, 3, 1890)
            """
        )

    if cursor.execute("SELECT COUNT(*) FROM production_metrics").fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO production_metrics (
                id, pending_renders, estimated_hours, available_pcs, render_queue
            ) VALUES (1, 7, 26, 2, 'Exterior A, Salon B, Cocina C')
            """
        )

    if cursor.execute("SELECT COUNT(*) FROM quick_links").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO quick_links (label, url) VALUES (?, ?)",
            [
                ("Carpeta proyectos", "file:///D:/Proyectos3D"),
                ("Presupuestos", "https://example.com/presupuestos"),
                ("WhatsApp", "https://web.whatsapp.com"),
                ("Trello", "https://trello.com"),
                ("NAS Synology", "http://synology.local:5000"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM meetings").fetchone()[0] == 0:
        cursor.execute(
            """
            INSERT INTO meetings (title, client, meeting_date, notes)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Revision materiales salon piloto",
                "Promociones Rivera",
                "2026-05-21 10:00",
                "Validar tonos, encuadres y cambios de mobiliario.",
            ),
        )
        meeting_id = cursor.lastrowid
        cursor.executemany(
            """
            INSERT INTO meeting_tasks (meeting_id, task_text, is_done)
            VALUES (?, ?, ?)
            """,
            [
                (meeting_id, "Preparar renders previos para compartir", 1),
                (meeting_id, "Anotar cambios pedidos por cliente", 0),
                (meeting_id, "Enviar resumen y tareas al terminar", 0),
            ],
        )

    connection.commit()


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()
