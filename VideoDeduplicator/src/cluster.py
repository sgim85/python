import sqlite3
from collections import defaultdict, deque


def build_graph(cur, threshold):
    graph = defaultdict(set)
    cur.execute("SELECT video_id_a, video_id_b, avg_hamming FROM video_similarity")
    for a, b, d in cur.fetchall():
        if d <= threshold:
            graph[a].add(b)
            graph[b].add(a)
    return graph


def connected_components(graph):
    visited = set()
    for node in graph:
        if node in visited:
            continue
        comp = []
        q = deque([node])
        visited.add(node)
        while q:
            v = q.popleft()
            comp.append(v)
            for nb in graph[v]:
                if nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        yield comp


def main(db_path, threshold=12.0):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    graph = build_graph(cur, threshold)
    cluster_id = 1
    cur.execute("DELETE FROM duplicate_clusters")
    for comp in connected_components(graph):
        for vid in comp:
            cur.execute(
                """
                INSERT OR REPLACE INTO duplicate_clusters(cluster_id, video_id)
                VALUES (?, ?)
            """,
                (cluster_id, vid),
            )
        cluster_id += 1
    conn.commit()
    conn.close()
