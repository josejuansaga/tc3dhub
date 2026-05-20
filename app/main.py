import os

from anthropic import Anthropic
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import ensure_database, get_connection


app = FastAPI(title=os.getenv("APP_NAME", "TC3D Hub"))
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def fetch_dashboard_data() -> dict:
    with get_connection() as connection:
        company = connection.execute(
            "SELECT * FROM company_metrics WHERE id = 1"
        ).fetchone()
        production = connection.execute(
            "SELECT * FROM production_metrics WHERE id = 1"
        ).fetchone()
        projects = connection.execute(
            """
            SELECT * FROM projects
            ORDER BY delivery_date ASC
            """
        ).fetchall()
        links = connection.execute(
            "SELECT * FROM quick_links ORDER BY id ASC"
        ).fetchall()
        meetings = connection.execute(
            """
            SELECT * FROM meetings
            ORDER BY meeting_date ASC
            """
        ).fetchall()
        tasks = connection.execute(
            """
            SELECT * FROM meeting_tasks
            ORDER BY id ASC
            """
        ).fetchall()

    active_projects = sum(
        1 for project in projects if project["status"] != "Completado"
    )
    board_columns = [
        "Pendiente inicio",
        "En produccion",
        "Revision cliente",
        "Completado",
    ]
    project_board = {
        column: [dict(project) for project in projects if project["status"] == column]
        for column in board_columns
    }
    next_deliverables = [
        {
            "project_name": project["project_name"],
            "client": project["client"],
            "delivery_date": project["delivery_date"],
        }
        for project in projects[:3]
    ]
    tasks_by_meeting = {}
    for task in tasks:
        tasks_by_meeting.setdefault(task["meeting_id"], []).append(dict(task))

    meetings_with_tasks = []
    for meeting in meetings:
        meeting_dict = dict(meeting)
        meeting_dict["tasks"] = tasks_by_meeting.get(meeting["id"], [])
        meetings_with_tasks.append(meeting_dict)

    return {
        "company": dict(company) if company else {},
        "production": dict(production) if production else {},
        "projects": [dict(project) for project in projects],
        "project_board": project_board,
        "links": [dict(link) for link in links],
        "meetings": meetings_with_tasks,
        "active_projects": active_projects,
        "next_deliverables": next_deliverables,
    }


@app.on_event("startup")
def startup() -> None:
    ensure_database()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    dashboard = fetch_dashboard_data()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"dashboard": dashboard, "app_name": os.getenv("APP_NAME", "TC3D Hub")},
    )


@app.get("/api/dashboard")
def get_dashboard():
    return fetch_dashboard_data()


@app.post("/api/projects")
def create_project(
    client: str = Form(...),
    project_name: str = Form(...),
    status: str = Form(...),
    delivery_date: str = Form(...),
    amount: float = Form(...),
    notes: str = Form(""),
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO projects (
                client, project_name, status, delivery_date, amount, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (client, project_name, status, delivery_date, amount, notes),
        )
        connection.commit()
    return JSONResponse({"ok": True})


@app.post("/api/projects/{project_id}/status")
def update_project_status(project_id: int, status: str = Form(...)):
    with get_connection() as connection:
        connection.execute(
            "UPDATE projects SET status = ? WHERE id = ?",
            (status, project_id),
        )
        connection.commit()
    return JSONResponse({"ok": True})


@app.post("/api/meetings")
def create_meeting(
    title: str = Form(...),
    client: str = Form(...),
    meeting_date: str = Form(...),
    notes: str = Form(""),
    tasks: str = Form(""),
):
    task_lines = [line.strip() for line in tasks.splitlines() if line.strip()]

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO meetings (title, client, meeting_date, notes)
            VALUES (?, ?, ?, ?)
            """,
            (title, client, meeting_date, notes),
        )
        meeting_id = cursor.lastrowid
        for task_text in task_lines:
            cursor.execute(
                """
                INSERT INTO meeting_tasks (meeting_id, task_text, is_done)
                VALUES (?, ?, 0)
                """,
                (meeting_id, task_text),
            )
        connection.commit()

    return JSONResponse({"ok": True})


@app.post("/api/tasks/{task_id}/toggle")
def toggle_task(task_id: int, is_done: int = Form(...)):
    with get_connection() as connection:
        connection.execute(
            "UPDATE meeting_tasks SET is_done = ? WHERE id = ?",
            (is_done, task_id),
        )
        connection.commit()
    return JSONResponse({"ok": True})


@app.post("/api/ai")
def generate_ai(prompt: str = Form(...), mode: str = Form(...)):
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    if not api_key:
        return {
            "result": (
                "Anthropic no esta configurado aun. "
                "Añade ANTHROPIC_API_KEY en tu archivo .env para activar este modulo."
            )
        }

    client = Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

    system_prompt = (
        "Eres un asistente operativo para un estudio pequeño de visualizacion 3D. "
        "Responde de forma clara, breve y util."
    )

    user_prompt = f"Modo: {mode}\n\nContenido:\n{prompt}"

    message = client.messages.create(
        model=model,
        max_tokens=500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    parts = []
    for block in message.content:
        if getattr(block, "type", "") == "text":
            parts.append(block.text)

    return {"result": "\n".join(parts).strip() or "Sin respuesta"}
