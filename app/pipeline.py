# app/pipeline.py
import sys
import os
import pandas as pd

# Add the directory containing this file to sys.path so sibling imports resolve correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bkt_engine import BKTEngine
from clustering_engine import ClusteringEngine
from grouping_engine import GroupingEngine



def label_clusters(cluster_profile: pd.DataFrame) -> dict:
    """
    Memberikan label semantik ke setiap cluster berdasarkan rata-rata penguasaan materi.
    Masing-masing cluster diurutkan berdasarkan rata-rata nilai P(Ln).
    - Nilai tertinggi -> "Mahir"
    - Nilai terendah -> "Remedial"
    - Nilai di antaranya -> "Cukup"
    """
    # Hitung rata-rata penguasaan tiap cluster (mean across columns/materi)
    cluster_means = cluster_profile.mean(axis=1)
    sorted_clusters = cluster_means.sort_values(ascending=False).index.tolist()
    
    semantic_labels = {}
    n_clusters = len(sorted_clusters)
    
    if n_clusters == 1:
        semantic_labels[sorted_clusters[0]] = "Umum"
    elif n_clusters == 2:
        semantic_labels[sorted_clusters[0]] = "Mahir"
        semantic_labels[sorted_clusters[1]] = "Remedial"
    else:
        semantic_labels[sorted_clusters[0]] = "Mahir"
        semantic_labels[sorted_clusters[-1]] = "Remedial"
        for i in range(1, n_clusters - 1):
            semantic_labels[sorted_clusters[i]] = "Cukup"
            
    return semantic_labels

# Alur eksekusi lengkap
def run_pipeline(mahasiswa_csv, kuis_csv, log_csv, group_size=4):
    # 1. Load data
    df_mhs = pd.read_csv(mahasiswa_csv)
    df_kuis = pd.read_csv(kuis_csv)
    df_log = pd.read_csv(log_csv).merge(df_kuis[['ID_Soal','Materi']], on='ID_Soal')
    
    # 2. BKT: update penguasaan materi per mahasiswa
    bkt = BKTEngine()
    bkt.process_log(df_log)
    
    materi_list = df_kuis['Materi'].unique().tolist()
    nim_list = df_mhs['NIM'].astype(str).tolist()
    
    # 3. Clustering: bangun feature matrix → cari K optimal → fit
    ce = ClusteringEngine()
    X = ce.build_feature_matrix(bkt, nim_list, materi_list)
    optimal_k = ce.find_optimal_k(X)
    cluster_labels = ce.fit(X, k=optimal_k)
    cluster_profile = ce.get_cluster_profile(X, cluster_labels, materi_list)
    cluster_semantic = label_clusters(cluster_profile)
    
    # 4. Greedy Grouping
    ge = GroupingEngine(group_size=group_size)
    groups = ge.form_groups(nim_list, cluster_labels, X, cluster_semantic, materi_list)
    
    # 5. Learning Path per mahasiswa
    learning_paths = {
        nim: bkt.get_learning_path(nim, materi_list)
        for nim in nim_list
    }
    
    return {
        'groups': groups,
        'learning_paths': learning_paths,
        'cluster_profile': cluster_profile,
        'cluster_labels': dict(zip(nim_list, cluster_labels.tolist()))
    }
