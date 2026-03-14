-- 1) Files discovered
CREATE TABLE IF NOT EXISTS videos (
    video_id      TEXT PRIMARY KEY,
    path          TEXT NOT NULL UNIQUE,
    size_bytes    INTEGER,
    mtime         REAL,
    discovered_at REAL
);

-- 2) Metadata
CREATE TABLE IF NOT EXISTS video_metadata (
    video_id    TEXT PRIMARY KEY,
    duration    REAL,
    frame_count INTEGER,
    width       INTEGER,
    height      INTEGER,
    codec       TEXT,
    bitrate     INTEGER,
    container   TEXT,
    fps         REAL,
    FOREIGN KEY(video_id) REFERENCES videos(video_id)
);

-- 3) Content hashes (per sampled frame)
CREATE TABLE IF NOT EXISTS video_hashes (
    video_id    TEXT,
    frame_index INTEGER,
    phash       INTEGER,
    PRIMARY KEY (video_id, frame_index),
    FOREIGN KEY(video_id) REFERENCES videos(video_id)
);

-- 4) Pairwise similarity
CREATE TABLE IF NOT EXISTS video_similarity (
    video_id_a  TEXT,
    video_id_b  TEXT,
    avg_hamming REAL,
    PRIMARY KEY (video_id_a, video_id_b),
    FOREIGN KEY(video_id_a) REFERENCES videos(video_id),
    FOREIGN KEY(video_id_b) REFERENCES videos(video_id)
);

-- 5) Clusters
CREATE TABLE IF NOT EXISTS duplicate_clusters (
    cluster_id INTEGER,
    video_id   TEXT,
    PRIMARY KEY (cluster_id, video_id),
    FOREIGN KEY(video_id) REFERENCES videos(video_id)
);

-- 6) Canonical per cluster
CREATE TABLE IF NOT EXISTS canonical_videos (
    cluster_id         INTEGER PRIMARY KEY,
    canonical_video_id TEXT,
    FOREIGN KEY(canonical_video_id) REFERENCES videos(video_id)
);

-- 7) Duplicate flags
CREATE TABLE IF NOT EXISTS duplicate_flags (
    video_id     TEXT PRIMARY KEY,
    is_duplicate INTEGER,
    canonical_of TEXT,
    FOREIGN KEY(video_id) REFERENCES videos(video_id),
    FOREIGN KEY(canonical_of) REFERENCES videos(video_id)
);