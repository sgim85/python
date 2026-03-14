import sqlite3


def main(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("\n=== Duplicate Clusters Report ===\n")

    cur.execute("""
        SELECT c.cluster_id, cv.canonical_video_id
        FROM canonical_videos cv
        JOIN duplicate_clusters c ON cv.cluster_id = c.cluster_id
        GROUP BY c.cluster_id
        ORDER BY c.cluster_id
    """)
    clusters = cur.fetchall()

    for cid, canonical in clusters:
        print(f"\n--- Cluster {cid} ---")
        print(f"Canonical: {canonical}")

        cur.execute(
            """
            SELECT dc.video_id, df.is_duplicate
            FROM duplicate_clusters dc
            LEFT JOIN duplicate_flags df ON dc.video_id = df.video_id
            WHERE dc.cluster_id = ?
        """,
            (cid,),
        )
        members = cur.fetchall()

        for vid, is_dup in members:
            tag = "(duplicate)" if is_dup else "(canonical)"
            print(f"  {vid} {tag}")

        print("\n  Metadata:")
        for vid, _ in members:
            cur.execute(
                """
                SELECT width, height, bitrate, codec, duration
                FROM video_metadata
                WHERE video_id = ?
            """,
                (vid,),
            )
            w, h, br, codec, dur = cur.fetchone()
            print(f"    {vid}: {w}x{h}, {br}bps, {codec}, {dur:.2f}s")

    conn.close()
