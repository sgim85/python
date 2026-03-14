import json, subprocess, sqlite3

FFPROBE = [
    "ffprobe",
    "-v",
    "quiet",
    "-print_format",
    "json",
    "-show_format",
    "-show_streams",
]


def probe(path):
    out = subprocess.check_output(FFPROBE + [path])
    return json.loads(out)


def main(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT v.video_id, v.path
        FROM videos v
        LEFT JOIN video_metadata m ON v.video_id = m.video_id
        WHERE m.video_id IS NULL
    """)
    rows = cur.fetchall()
    for vid, path in rows:
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
    conn.close()
