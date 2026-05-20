import os
import shutil
import sqlite3
from contextlib import contextmanager


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.getenv(
    "DATA_DIR",
    os.path.normpath(os.path.join(BASE_DIR, "..", "data")),
)
DB_PATH = os.path.join(DATA_DIR, "tc3d_hub.db")
LEGACY_DB_PATH = "/data/tc3d_hub.db"


def ensure_database() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    migrate_legacy_database()
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

            CREATE TABLE IF NOT EXISTS project_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                notes TEXT DEFAULT '',
                FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                contact_person TEXT DEFAULT '',
                email TEXT DEFAULT '',
                phone TEXT DEFAULT '',
                city TEXT DEFAULT '',
                gallery_url TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT ''
            );
            """
        )
        ensure_project_columns(cursor)
        ensure_client_links(cursor)
        connection.commit()
        seed_data(connection)


def migrate_legacy_database() -> None:
    if DB_PATH == LEGACY_DB_PATH:
        return
    if os.path.exists(DB_PATH):
        return
    if os.path.exists(LEGACY_DB_PATH):
        shutil.copy2(LEGACY_DB_PATH, DB_PATH)


def ensure_project_columns(cursor: sqlite3.Cursor) -> None:
    columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(projects)").fetchall()
    }
    if "description" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN description TEXT DEFAULT ''")
    if "folder_path" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN folder_path TEXT DEFAULT ''")
    if "created_at" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN created_at TEXT DEFAULT ''")
    if "due_date" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN due_date TEXT DEFAULT ''")
    cursor.execute(
        """
        UPDATE projects
        SET created_at = COALESCE(NULLIF(created_at, ''), date('now'))
        """
    )
    cursor.execute(
        """
        UPDATE projects
        SET due_date = COALESCE(NULLIF(due_date, ''), delivery_date)
        """
    )


def ensure_client_links(cursor: sqlite3.Cursor) -> None:
    columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(projects)").fetchall()
    }
    if "client_id" not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN client_id INTEGER")

    project_clients = cursor.execute(
        "SELECT DISTINCT client FROM projects WHERE COALESCE(client, '') != ''"
    ).fetchall()
    for row in project_clients:
        name = row[0]
        cursor.execute(
            """
            INSERT OR IGNORE INTO clients (name, created_at)
            VALUES (?, COALESCE(date('now'), ''))
            """,
            (name,),
        )
    cursor.execute(
        """
        UPDATE projects
        SET client_id = (
            SELECT id FROM clients WHERE clients.name = projects.client
        )
        WHERE client_id IS NULL AND COALESCE(client, '') != ''
        """
    )


def seed_data(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()

    if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO projects (
                client, project_name, status, delivery_date, amount, notes, description, folder_path, created_at, due_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    "Promociones Rivera",
                    "Infografias vivienda piloto",
                    "En produccion",
                    "2026-05-24",
                    1450,
                    "Faltan 2 renders exteriores",
                    "Proyecto de visualizacion interior y exterior para vivienda piloto.",
                    "file:///D:/Proyectos3D/Rivera/Vivienda-piloto",
                    "2026-05-20",
                    "2026-05-24",
                ),
                (
                    "Estudio Armonia",
                    "Render cocina premium",
                    "Revision cliente",
                    "2026-05-22",
                    680,
                    "Esperando feedback final",
                    "Imagenes de cocina premium para aprobacion comercial.",
                    "file:///D:/Proyectos3D/Armonia/Cocina-premium",
                    "2026-05-20",
                    "2026-05-22",
                ),
                (
                    "Habita Norte",
                    "Tour 3D adosados",
                    "Pendiente inicio",
                    "2026-05-29",
                    2100,
                    "Presupuesto aprobado esta semana",
                    "Recorrido para promocion de adosados con enfoque comercial.",
                    "file:///D:/Proyectos3D/HabitaNorte/Tour-adosados",
                    "2026-05-20",
                    "2026-05-29",
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

    if cursor.execute("SELECT COUNT(*) FROM project_tasks").fetchone()[0] == 0:
        project_rows = cursor.execute(
            "SELECT id, project_name FROM projects ORDER BY id ASC"
        ).fetchall()
        project_map = {row[1]: row[0] for row in project_rows}
        task_rows = [
            (
                project_map.get("Infografias vivienda piloto"),
                "Definir encuadres finales",
                "Por hacer",
                "Esperando validacion del cliente.",
            ),
            (
                project_map.get("Infografias vivienda piloto"),
                "Render exterior principal",
                "En marcha",
                "Prioridad alta.",
            ),
            (
                project_map.get("Render cocina premium"),
                "Corregir materiales encimera",
                "Bloqueado",
                "A falta de referencia nueva.",
            ),
            (
                project_map.get("Tour 3D adosados"),
                "Preparar estructura del tour",
                "Por hacer",
                "",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO project_tasks (project_id, title, status, notes)
            VALUES (?, ?, ?, ?)
            """,
            [row for row in task_rows if row[0] is not None],
        )

    cursor.execute(
        """
        UPDATE clients
        SET gallery_url = CASE name
            WHEN 'Promociones Rivera' THEN 'https://example.com/galeria/rivera'
            WHEN 'Estudio Armonia' THEN 'https://example.com/galeria/armonia'
            WHEN 'Habita Norte' THEN 'https://example.com/galeria/habita-norte'
            ELSE gallery_url
        END
        WHERE COALESCE(gallery_url, '') = ''
        """
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
