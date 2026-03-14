import sqlite3
from itertools import combinations

DURATION_TOL = 2.0  # seconds
FRAMECOUNT_TOL = 0.05  # ±5%
HAMMING_THRESHOLD = 16.0  # max avg hamming to store similarity


def hamming64(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def sliding_window_score(hashes_a, hashes_b):
    if not hashes_a or not hashes_b:
        return float("inf")

    if len(hashes_a) > len(hashes_b):
        hashes_a, hashes_b = hashes_b, hashes_a

    la, lb = len(hashes_a), len(hashes_b)
    best = float("inf")

    for offset in range(lb - la + 1):
        total = 0
        for i in range(la):
            total += hamming64(hashes_a[i], hashes_b[i + offset])
        avg = total / la
        if avg < best:
            best = avg

    return best


def resolution_class(h):
    if h < 720:
        return "SD"
    elif h < 1080:
        return "HD"
    elif h < 1440:
        return "FHD"
    else:
        return "4K"


def passes_blocking(meta_a, meta_b):
    if abs(meta_a["duration"] - meta_b["duration"]) > DURATION_TOL:
        return False

    fa, fb = meta_a["frame_count"], meta_b["frame_count"]
    if fa and fb:
        if abs(fa - fb) > FRAMECOUNT_TOL * max(fa, fb):
            return False

    if resolution_class(meta_a["height"]) != resolution_class(meta_b["height"]):
        return False

    return True


def main(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT video_id, duration, frame_count, height
        FROM video_metadata
    """)
    metadata = {
        vid: {"duration": dur, "frame_count": fc, "height": h}
        for vid, dur, fc, h in cur.fetchall()
    }

    cur.execute("SELECT DISTINCT video_id FROM video_hashes")
    vids = [r[0] for r in cur.fetchall()]

    hashes = {}
    for vid in vids:
        cur.execute(
            """
            SELECT frame_index, phash FROM video_hashes
            WHERE video_id = ? ORDER BY frame_index
        """,
            (vid,),
        )
        hashes[vid] = [row[1] for row in cur.fetchall()]

    for a, b in combinations(vids, 2):
        if not passes_blocking(metadata[a], metadata[b]):
            continue

        score = sliding_window_score(hashes[a], hashes[b])
        if score <= HAMMING_THRESHOLD:
            cur.execute(
                """
                INSERT OR REPLACE INTO video_similarity(video_id_a, video_id_b, avg_hamming)
                VALUES (?, ?, ?)
            """,
                (a, b, score),
            )

    conn.commit()
    conn.close()
