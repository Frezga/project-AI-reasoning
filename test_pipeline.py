import sys
import os

from app.pipeline import run_pipeline

mahasiswa_csv = "dataset/mahasiswa.csv"
kuis_csv = "dataset/kuis_struktur.csv"
log_csv = "dataset/mahasiswa_log_jawaban.csv"

try:
    results = run_pipeline(mahasiswa_csv, kuis_csv, log_csv, group_size=4)
    print("Pipeline executed successfully!")
    print(f"Number of groups formed: {len(results['groups'])}")
    print(f"Cluster profile: \n{results['cluster_profile']}")
    for g in results['groups']:
        print(f"\nGroup {g['kelompok_id']}:")
        for m in g['anggota']:
            print(f"  - NIM: {m['nim']} | Cluster: {m['cluster_label']} | Avg Mastery: {m['avg_mastery']}")
        print(f"  Heterogeneity Score: {g['heterogeneity_score']}")
        print(f"  Reasoning: {g['reasoning']}")
except Exception as e:
    print(f"Failed to execute pipeline: {e}")
    import traceback
    traceback.print_exc()
