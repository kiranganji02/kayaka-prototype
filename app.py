from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sqlite3, json, re

BASE = Path(__file__).parent
DB = BASE / "kayaka.db"
app = FastAPI(title="Kayaka – Hyper-local voice-first jobs")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

SEED_JOBS = [
    ("Electrician helper", "electrician", "Vijay Nagar", 2.1, 650, "Ravi Electricals", "2 days"),
    ("House wiring technician", "electrician", "Shahapur", 4.3, 900, "Shree Services", "1 week"),
    ("Masonry helper", "mason", "Old City", 3.2, 550, "Patil Contractors", "3 days"),
    ("Plumbing assistant", "plumber", "Vidya Nagar", 1.7, 700, "AquaFix", "2 days"),
    ("Shop assistant", "helper", "Market Road", 2.8, 500, "Mahalaxmi Stores", "Permanent"),
]

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, skill TEXT, area TEXT,
            distance REAL, wage INTEGER, employer TEXT, duration TEXT, status TEXT DEFAULT 'Open'
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, skill TEXT, area TEXT,
            distance REAL, availability TEXT, phone TEXT
        )""")
        if c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
            c.executemany("INSERT INTO jobs(title,skill,area,distance,wage,employer,duration) VALUES(?,?,?,?,?,?,?)", SEED_JOBS)

init_db()

@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static" / "index.html").read_text()

@app.get("/api/jobs")
def jobs():
    with conn() as c:
        rows = c.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@app.post("/api/workers")
def create_worker(name: str = Form(...), skill: str = Form(...), area: str = Form(...),
                  distance: float = Form(2.0), availability: str = Form("Available now"),
                  phone: str = Form("")):
    with conn() as c:
        cur = c.execute("INSERT INTO workers(name,skill,area,distance,availability,phone) VALUES(?,?,?,?,?,?)",
                        (name, skill.lower(), area, distance, availability, phone))
        worker_id = cur.lastrowid
    return {"id": worker_id, "name": name, "skill": skill, "area": area,
            "distance": distance, "availability": availability}

@app.post("/api/jobs")
def create_job(title: str = Form(...), skill: str = Form(...), area: str = Form(...),
               distance: float = Form(2.0), wage: int = Form(...), employer: str = Form(...),
               duration: str = Form("Short-term")):
    with conn() as c:
        cur = c.execute("INSERT INTO jobs(title,skill,area,distance,wage,employer,duration) VALUES(?,?,?,?,?,?,?)",
                        (title, skill.lower(), area, distance, wage, employer, duration))
        job_id = cur.lastrowid
    return {"id": job_id, "title": title}

@app.get("/api/matches/{worker_id}")
def matches(worker_id: int):
    with conn() as c:
        worker = c.execute("SELECT * FROM workers WHERE id=?", (worker_id,)).fetchone()
        if not worker:
            return JSONResponse({"error": "Worker not found"}, status_code=404)
        rows = c.execute("SELECT * FROM jobs WHERE status='Open'").fetchall()
    skill_terms = set(re.findall(r"[a-z]+", worker["skill"].lower()))
    ranked = []
    for row in rows:
        job = dict(row)
        job_terms = set(re.findall(r"[a-z]+", (job["skill"] + " " + job["title"]).lower()))
        overlap = len(skill_terms & job_terms)
        skill_score = 1 if overlap else 0
        distance_score = max(0, 1 - abs(float(job["distance"]) - float(worker["distance"])) / 10)
        score = round(0.75 * skill_score + 0.25 * distance_score, 2)
        job["match_score"] = score
        if skill_score or score >= 0.25:
            ranked.append(job)
    return sorted(ranked, key=lambda x: x["match_score"], reverse=True)[:3]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "Kayaka demo"}
