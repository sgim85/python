import os, uuid, time, sqlite3

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".webm"}


def iter_videos(roots):
    for root in roots:
        for dirpath, _, files in os.walk(root):
            for f in files:
                if os.path.splitext(f)[1].lower() in VIDEO_EXTS:
                    yield os.path.join(dirpath, f)


def main(db_path, roots):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now = time.time()
    for path in iter_videos(roots):
        st = os.stat(path)
        vid = uuid.uuid5(uuid.NAMESPACE_URL, path).hex
        cur.execute(
            """
            INSERT OR IGNORE INTO videos(video_id, path, size_bytes, mtime, discovered_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (vid, path, st.st_size, st.st_mtime, now),
        )
    conn.commit()
    conn.close()
