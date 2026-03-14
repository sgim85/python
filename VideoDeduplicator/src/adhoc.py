import os, uuid, sqlite3
from extract_metadata import probe
from compute_hashes import compute_video_hashes
from similarity import passes_blocking, sliding_window_score, HAMMING_THRESHOLD
from cluster import main as cluster_main
from canonical import main as canon_main


def ensure_video_record(conn, path):
    cur = conn.cursor()
    cur.execute("SELECT video_id FROM videos WHERE path = ?", (path,))
    row = cur.fetchone()
    if row:
        return row[0]
    st = os.stat(path)
    vid = uuid.uuid5(uuid.NAMESPACE_URL, path).hex
    cur.execute(
        """
        INSERT INTO videos(video_id, path, size_bytes, mtime, discovered_at)
        VALUES (?, ?, ?, ?, strftime('%s','now'))
    """,
        (vid, path, st.st_size, st.st_mtime),
    )
    conn.commit()
    return vid


def process_single_video(db_path, path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    vid = ensure_video_record(conn, path)
    cur = conn.cursor()

    meta = probe(path)
    vstream = next(s for s in meta["streams"] if s["codec_type"] == "video")
    duration = float(meta["format"].get("duration", 0.0))
    width = int(vstream.get("width", 0))
    height = int(vstream.get("height", 0))
    codec = vstream.get("codec_name")
    bitrate = int(meta["format"].get("bit_rate", 0) or 0)
    fps_str = vstream.get("r_frame_rate", "0/1")
    num, den = map(int, fps_str.split("/"))
    fps = num / den if den else 0
    frame_count = int(vstream.get("nb_frames") or 0)

    cur.execute(
        """
        INSERT OR REPLACE INTO video_metadata
        (video_id, duration, frame_count, width, height, codec, bitrate, container, fps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            vid,
            duration,
            frame_count,
            width,
            height,
            codec,
            bitrate,
            meta["format"].get("format_name"),
            fps,
        ),
    )
    conn.commit()

    _, hashes = compute_video_hashes((vid, path))
    cur.executemany(
        """
        INSERT OR REPLACE INTO video_hashes(video_id, frame_index, phash)
        VALUES (?, ?, ?)
    """,
        [(vid, idx, ph) for idx, ph in hashes],
    )
    conn.commit()

    cur.execute(
        """
        SELECT video_id, duration, frame_count, height
        FROM video_metadata
        WHERE video_id != ?
    """,
        (vid,),
    )
    others = cur.fetchall()

    cur.execute(
        """
        SELECT frame_index, phash FROM video_hashes
        WHERE video_id = ? ORDER BY frame_index
    """,
        (vid,),
    )
    this_hashes = [r[1] for r in cur.fetchall()]

    for row in others:
        other_id = row["video_id"]
        meta_other = {
            "duration": row["duration"],
            "frame_count": row["frame_count"],
            "height": row["height"],
        }
        meta_this = {
            "duration": duration,
            "frame_count": frame_count,
            "height": height,
        }
        if not passes_blocking(meta_this, meta_other):
            continue

        cur.execute(
            """
            SELECT phash FROM video_hashes
            WHERE video_id = ? ORDER BY frame_index
        """,
            (other_id,),
        )
        other_hashes = [r[0] for r in cur.fetchall()]
        score = sliding_window_score(this_hashes, other_hashes)
        if score <= HAMMING_THRESHOLD:
            cur.execute(
                """
                INSERT OR REPLACE INTO video_similarity(video_id_a, video_id_b, avg_hamming)
                VALUES (?, ?, ?)
            """,
                (vid, other_id, score),
            )

    conn.commit()

    cluster_main(db_path)
    canon_main(db_path)

    cur.execute(
        """
        SELECT cluster_id FROM duplicate_clusters WHERE video_id = ?
    """,
        (vid,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        return {"video_id": vid, "cluster": None}

    cid = row["cluster_id"]
    cur.execute(
        """
        SELECT canonical_video_id FROM canonical_videos WHERE cluster_id = ?
    """,
        (cid,),
    )
    canonical = cur.fetchone()["canonical_video_id"]

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
        (cid,),
    )
    members = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {
        "video_id": vid,
        "cluster_id": cid,
        "canonical": canonical,
        "members": members,
    }
