import os, sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from pipeline import run_stage
from adhoc import process_single_video

DB_PATH = os.environ.get("DB_PATH", "/data/videos.db")
VIDEO_ROOTS = os.environ.get("VIDEO_ROOTS", "/videos").split(":")

app = FastAPI(title="Video Deduper")
templates = Jinja2Templates(directory="templates")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------- REST: clusters ----------


@app.get("/clusters")
def list_clusters(min_size: int = 2, q: str | None = None):
    conn = get_db()
    cur = conn.cursor()
    base = """
        SELECT cv.cluster_id, cv.canonical_video_id, COUNT(dc.video_id) AS count
        FROM canonical_videos cv
        JOIN duplicate_clusters dc ON cv.cluster_id = dc.cluster_id
        JOIN videos v ON dc.video_id = v.video_id
    """
    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND v.path LIKE ?"
        params.append(f"%{q}%")
    group = (
        " GROUP BY cv.cluster_id HAVING COUNT(dc.video_id) >= ? ORDER BY cv.cluster_id"
    )
    params.append(min_size)
    cur.execute(base + where + group, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


@app.get("/clusters/{cluster_id}")
def cluster_detail(cluster_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT cv.canonical_video_id
        FROM canonical_videos cv
        WHERE cv.cluster_id = ?
    """,
        (cluster_id,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"error": "cluster not found"}

    canonical = row["canonical_video_id"]

    cur.execute(
        """
        SELECT dc.video_id, df.is_duplicate, v.path,
               m.width, m.height, m.bitrate, m.codec, m.duration
        FROM duplicate_clusters dc
        JOIN videos v ON dc.video_id = v.video_id
        JOIN video_metadata m ON v.video_id = m.video_id
        LEFT JOIN duplicate_flags df ON dc.video_id = df.video_id
        WHERE dc.cluster_id = ?
    """,
        (cluster_id,),
    )
    members = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"cluster_id": cluster_id, "canonical": canonical, "members": members}


@app.get("/videos/{video_id}")
def video_detail(video_id: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT v.video_id, v.path, m.*
        FROM videos v
        JOIN video_metadata m ON v.video_id = m.video_id
        WHERE v.video_id = ?
    """,
        (video_id,),
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        return {"error": "video not found"}
    return dict(row)


# ---------- REST: proposals ----------


@app.get("/proposals.json")
def proposals_json():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT df.video_id, df.canonical_of, v.path AS dup_path, vc.path AS canonical_path
        FROM duplicate_flags df
        JOIN videos v ON df.video_id = v.video_id
        JOIN videos vc ON df.canonical_of = vc.video_id
        WHERE df.is_duplicate = 1
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# ---------- REST: pipeline triggers ----------


@app.post("/run/{stage}")
def run_pipeline_stage(stage: str):
    allowed = {"scan", "meta", "hash", "sim", "cluster", "canon", "all"}
    if stage not in allowed:
        return {"error": "invalid stage"}
    run_stage(DB_PATH, VIDEO_ROOTS, stage)
    return {"status": "ok", "stage": stage}


# ---------- REST: adhoc ----------


class AdhocRequest(BaseModel):
    path: str


@app.post("/adhoc")
def adhoc_process(req: AdhocRequest):
    if not os.path.exists(req.path):
        return {"error": "path does not exist"}
    result = process_single_video(DB_PATH, req.path)
    return result


# ---------- DASHBOARD ----------


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, min_size: int = 2, q: str | None = None):
    conn = get_db()
    cur = conn.cursor()
    base = """
        SELECT cv.cluster_id, cv.canonical_video_id, COUNT(dc.video_id) AS count
        FROM canonical_videos cv
        JOIN duplicate_clusters dc ON cv.cluster_id = dc.cluster_id
        JOIN videos v ON dc.video_id = v.video_id
    """
    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND v.path LIKE ?"
        params.append(f"%{q}%")
    group = (
        " GROUP BY cv.cluster_id HAVING COUNT(dc.video_id) >= ? ORDER BY cv.cluster_id"
    )
    params.append(min_size)
    cur.execute(base + where + group, params)
    clusters = cur.fetchall()
    conn.close()
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "clusters": clusters, "min_size": min_size, "q": q or ""},
    )


@app.get("/cluster/{cluster_id}", response_class=HTMLResponse)
def cluster_page(cluster_id: int, request: Request):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT canonical_video_id FROM canonical_videos WHERE cluster_id = ?
    """,
        (cluster_id,),
    )
    canonical_row = cur.fetchone()
    if not canonical_row:
        conn.close()
        return HTMLResponse("Cluster not found", status_code=404)

    canonical = canonical_row["canonical_video_id"]

    cur.execute(
        """
        SELECT dc.video_id, df.is_duplicate, v.path,
               m.width, m.height, m.bitrate, m.codec, m.duration
        FROM duplicate_clusters dc
        JOIN videos v ON dc.video_id = v.video_id
        JOIN video_metadata m ON v.video_id = m.video_id
        LEFT JOIN duplicate_flags df ON dc.video_id = df.video_id
        WHERE dc.cluster_id = ?
    """,
        (cluster_id,),
    )
    members = cur.fetchall()
    conn.close()

    return templates.TemplateResponse(
        "cluster.html",
        {
            "request": request,
            "cluster_id": cluster_id,
            "canonical": canonical,
            "members": members,
        },
    )


@app.get("/proposals", response_class=HTMLResponse)
def proposals(request: Request):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT df.video_id, df.canonical_of, v.path AS dup_path, vc.path AS canonical_path
        FROM duplicate_flags df
        JOIN videos v ON df.video_id = v.video_id
        JOIN videos vc ON df.canonical_of = vc.video_id
        WHERE df.is_duplicate = 1
        ORDER BY df.canonical_of
    """)
    rows = cur.fetchall()
    conn.close()
    return templates.TemplateResponse(
        "proposals.html", {"request": request, "rows": rows}
    )
