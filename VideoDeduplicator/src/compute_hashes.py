import cv2, sqlite3, imagehash, os
from PIL import Image
from multiprocessing import Pool, cpu_count

N_FRAMES = 32
WORKERS = int(os.environ.get("HASH_WORKERS", cpu_count()))


def compute_video_hashes(args):
    video_id, path = args
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release()
        return video_id, []

    step = max(total // N_FRAMES, 1)
    hashes = []
    frame_idx = 0
    for i in range(0, total, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok:
            continue
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        h = imagehash.phash(pil)
        hashes.append((frame_idx, int(str(h), 16)))
        frame_idx += 1
    cap.release()
    return video_id, hashes


def main(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT v.video_id, v.path
        FROM videos v
        LEFT JOIN video_hashes h ON v.video_id = h.video_id
        WHERE h.video_id IS NULL
    """)
    jobs = cur.fetchall()
    conn.close()

    if not jobs:
        return

    with Pool(WORKERS) as pool:
        for video_id, hashes in pool.imap_unordered(compute_video_hashes, jobs):
            if not hashes:
                continue
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.executemany(
                """
                INSERT OR REPLACE INTO video_hashes(video_id, frame_index, phash)
                VALUES (?, ?, ?)
            """,
                [(video_id, idx, ph) for idx, ph in hashes],
            )
            conn.commit()
            conn.close()
