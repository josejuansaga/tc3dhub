import os

from anthropic import Anthropic
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import ensure_database, get_connection


app = FastAPI(title=os.getenv("APP_NAME", "TC3D Hub"))
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

PROJECT_COLUMNS = [
    "Pendiente inicio",
    "En produccion",
    "Revision cliente",
    "Completado",
]
TASK_COLUMNS = [
    "Por hacer",
    "En marcha",
    "Bloqueado",
    "Hecho",
]


def fetch_dashboard_data() -> dict:
    with get_connection() as connection:
        company = connection.execute(
            "SELECT * FROM company_metrics WHERE id = 1"
        ).fetchone()
        production = connection.execute(
            "SELECT * FROM production_metrics WHERE id = 1"
        ).fetchone()
        projects = connection.execute(
            "SELECT * FROM projects ORDER BY delivery_date ASC"
        ).fetchall()
        links = connection.execute(
            "SELECT * FROM quick_links ORDER BY id ASC"
        ).fetchall()
        meetings = connection.execute(
            "SELECT * FROM meetings ORDER BY meeting_date ASC"
        ).fetchall()
        tasks = connection.execute(
            "SELECT * FROM meeting_tasks ORDER BY id ASC"
        ).fetchall()

    active_projects = sum(
        1 for project in projects if project["status"] != "Completado"
    )
    next_deliverables = [
        {
            "project_name": project["project_name"],
            "client": project["client"],
            "delivery_date": project["delivery_date"],
        }
        for project in projects[:4]
    ]
    recent_projects = [dict(project) for project in projects[:5]]

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
        "links": [dict(link) for link in links],
        "meetings": meetings_with_tasks,
        "active_projects": active_projects,
        "next_deliverables": next_deliverables,
        "recent_projects": recent_projects,
    }


def fetch_projects_data() -> dict:
    with get_connection() as connection:
        projects = connection.execute(
            "SELECT * FROM projects ORDER BY delivery_date ASC, id DESC"
        ).fetchall()

    project_list = [dict(project) for project in projects]
    project_board = {
        column: [project for project in project_list if project["status"] == column]
        for column in PROJECT_COLUMNS
    }

    return {
        "projects": project_list,
        "project_board": project_board,
        "project_columns": PROJECT_COLUMNS,
    }


def fetch_project_detail(project_id: int) -> dict:
    with get_connection() as connection:
        project = connection.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")

        tasks = connection.execute(
            """
            SELECT * FROM project_tasks
            WHERE project_id = ?
            ORDER BY id ASC
            """,
            (project_id,),
        ).fetchall()

    task_list = [dict(task) for task in tasks]
    task_board = {
        column: [task for task in task_list if task["status"] == column]
        for column in TASK_COLUMNS
    }

    return {
        "project": dict(project),
        "task_board": task_board,
        "task_columns": TASK_COLUMNS,
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


@app.get("/projects", response_class=HTMLResponse)
def projects_page(request: Request):
    project_data = fetch_projects_data()
    return templates.TemplateResponse(
        request=request,
        name="projects.html",
        context={
            "projects_data": project_data,
            "app_name": os.getenv("APP_NAME", "TC3D Hub"),
        },
    )


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_detail_page(request: Request, project_id: int):
    detail = fetch_project_detail(project_id)
    return templates.TemplateResponse(
        request=request,
        name="project_detail.html",
        context={
            "detail": detail,
            "app_name": os.getenv("APP_NAME", "TC3D Hub"),
        },
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
    description: str = Form(""),
    folder_path: str = Form(""),
):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO projects (
                client, project_name, status, delivery_date, amount, notes, description, folder_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                client,
                project_name,
                status,
                delivery_date,
                amount,
                notes,
                description,
                folder_path,
            ),
        )
        project_id = cursor.lastrowid
        connection.commit()
    return JSONResponse({"ok": True, "project_id": project_id})


@app.post("/api/projects/{project_id}/status")
def update_project_status(project_id: int, status: str = Form(...)):
    with get_connection() as connection:
        connection.execute(
            "UPDATE projects SET status = ? WHERE id = ?",
            (status, project_id),
        )
        connection.commit()
    return JSONResponse({"ok": True})


@app.post("/api/projects/{project_id}")
def update_project(
    project_id: int,
    client: str = Form(...),
    project_name: str = Form(...),
    status: str = Form(...),
    delivery_date: str = Form(...),
    amount: float = Form(...),
    notes: str = Form(""),
    description: str = Form(""),
    folder_path: str = Form(""),
):
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE projects
            SET client = ?, project_name = ?, status = ?, delivery_date = ?,
                amount = ?, notes = ?, description = ?, folder_path = ?
            WHERE id = ?
            """,
            (
                client,
                project_name,
                status,
                delivery_date,
                amount,
                notes,
                description,
                folder_path,
                project_id,
            ),
        )
        connection.commit()
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.post("/api/projects/{project_id}/tasks")
def create_project_task(
    project_id: int,
    title: str = Form(...),
    status: str = Form(...),
    notes: str = Form(""),
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO project_tasks (project_id, title, status, notes)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, title, status, notes),
        )
        connection.commit()
    return JSONResponse({"ok": True})


@app.post("/api/project-tasks/{task_id}/status")
def update_project_task_status(task_id: int, status: str = Form(...)):
    with get_connection() as connection:
        connection.execute(
            "UPDATE project_tasks SET status = ? WHERE id = ?",
            (status, task_id),
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
                "Anade ANTHROPIC_API_KEY en tu archivo .env para activar este modulo."
            )
        }

    client = Anthropic(api_key=api_key)
    model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-latest")

    system_prompt = (
        "Eres un asistente operativo para un estudio pequeno de visualizacion 3D. "
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
