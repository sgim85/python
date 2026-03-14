import os, argparse
from scan_folders import main as scan_main
from extract_metadata import main as meta_main
from compute_hashes import main as hash_main
from similarity import main as sim_main
from cluster import main as cluster_main
from canonical import main as canon_main
from report_clusters import main as report_main

DB_PATH = os.environ.get("DB_PATH", "/data/videos.db")
ROOTS = os.environ.get("VIDEO_ROOTS", "/videos").split(":")


def run_all():
    scan_main(DB_PATH, ROOTS)
    meta_main(DB_PATH)
    hash_main(DB_PATH)
    sim_main(DB_PATH)
    cluster_main(DB_PATH)
    canon_main(DB_PATH)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "command",
        choices=["scan", "meta", "hash", "sim", "cluster", "canon", "report", "all"],
    )
    args = p.parse_args()
    if args.command == "scan":
        scan_main(DB_PATH, ROOTS)
    elif args.command == "meta":
        meta_main(DB_PATH)
    elif args.command == "hash":
        hash_main(DB_PATH)
    elif args.command == "sim":
        sim_main(DB_PATH)
    elif args.command == "cluster":
        cluster_main(DB_PATH)
    elif args.command == "canon":
        canon_main(DB_PATH)
    elif args.command == "report":
        report_main(DB_PATH)
    elif args.command == "all":
        run_all()
