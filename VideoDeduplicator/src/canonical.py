import sqlite3

CODEC_SCORE = {
    "hevc": 3,
    "h264": 2,
    "vp9": 2,
    "mpeg4": 1,
}
CONTAINER_SCORE = {
    "mp4": 3,
    "matroska,webm": 2,
    "mov,mp4,m4a,3gp,3g2,mj2": 2,
    "avi": 1,
}


def score(meta):
    res = (meta["width"] or 0) * (meta["height"] or 0)
    bitrate = meta["bitrate"] or 0
    codec_s = CODEC_SCORE.get(meta["codec"], 0)
    cont_s = CONTAINER_SCORE.get(meta["container"], 0)
    return 3 * res + 2 * bitrate + 1000 * codec_s + 500 * cont_s


def main(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DELETE FROM canonical_videos")
    cur.execute("DELETE FROM duplicate_flags")

    cur.execute("SELECT DISTINCT cluster_id FROM duplicate_clusters")
    clusters = [r[0] for r in cur.fetchall()]

    for cid in clusters:
        cur.execute(
            """
            SELECT v.video_id, m.width, m.height, m.bitrate, m.codec, m.container
            FROM duplicate_clusters c
            JOIN videos v ON c.video_id = v.video_id
            JOIN video_metadata m ON v.video_id = m.video_id
            WHERE c.cluster_id = ?
        """,
            (cid,),
        )
        rows = cur.fetchall()
        best_vid, best_score = None, -1
        metas = {}
        for vid, w, h, br, codec, container in rows:
            meta = {
                "width": w,
                "height": h,
                "bitrate": br,
                "codec": codec,
                "container": container,
            }
            metas[vid] = meta
            s = score(meta)
            if s > best_score:
                best_score, best_vid = s, vid

        cur.execute(
            """
            INSERT OR REPLACE INTO canonical_videos(cluster_id, canonical_video_id)
            VALUES (?, ?)
        """,
            (cid, best_vid),
        )

        for vid in metas.keys():
            cur.execute(
                """
                INSERT OR REPLACE INTO duplicate_flags(video_id, is_duplicate, canonical_of)
                VALUES (?, ?, ?)
            """,
                (vid, 0 if vid == best_vid else 1, best_vid),
            )

    conn.commit()
    conn.close()
