from scan_folders import main as scan_main
from extract_metadata import main as meta_main
from compute_hashes import main as hash_main
from similarity import main as sim_main
from cluster import main as cluster_main
from canonical import main as canon_main


def run_stage(db_path, roots, stage: str):
    if stage == "scan":
        scan_main(db_path, roots)
    elif stage == "meta":
        meta_main(db_path)
    elif stage == "hash":
        hash_main(db_path)
    elif stage == "sim":
        sim_main(db_path)
    elif stage == "cluster":
        cluster_main(db_path)
    elif stage == "canon":
        canon_main(db_path)
    elif stage == "all":
        scan_main(db_path, roots)
        meta_main(db_path)
        hash_main(db_path)
        sim_main(db_path)
        cluster_main(db_path)
        canon_main(db_path)
