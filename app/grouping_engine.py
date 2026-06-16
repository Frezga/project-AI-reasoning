# app/grouping_engine.py

import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict

# Engine untuk membentuk kelompok belajar heterogen menggunakan algoritma greedy
class GroupingEngine:
    
    # Inisialisasi target ukuran kelompok
    def __init__(self, group_size: int = 4):
        self.group_size = group_size
    
    # Algoritma Round-Robin Greedy untuk menyusun kelompok heterogen
    def form_groups(self,
                    nim_list: List[str],
                    cluster_labels: np.ndarray,
                    feature_matrix: np.ndarray,
                    cluster_semantic: Dict[int, str],
                    materi_list: List[str]) -> List[Dict]:
        n = len(nim_list)
        
        # Kelompokkan mahasiswa per cluster
        cluster_buckets: Dict[int, List[int]] = defaultdict(list)
        for idx, nim in enumerate(nim_list):
            cluster_id = int(cluster_labels[idx])
            cluster_buckets[cluster_id].append(idx)
        
        # Sort cluster berdasarkan rata-rata penguasaan (Mahir -> Remedial)
        avg_mastery_per_cluster = {}
        for c_id, indices in cluster_buckets.items():
            avg_mastery_per_cluster[c_id] = np.mean(feature_matrix[indices].mean(axis=1))
        
        sorted_clusters = sorted(
            cluster_buckets.keys(),
            key=lambda c: avg_mastery_per_cluster[c],
            reverse=True
        )
        
        # Proses pembagian anggota kelompok dengan Round-Robin
        groups_indices = []  
        current_group = []
        cluster_pointers = {c: 0 for c in sorted_clusters}
        assigned = set()
        
        while len(assigned) < n:
            progress = False
            for c_id in sorted_clusters:
                bucket = cluster_buckets[c_id]
                ptr = cluster_pointers[c_id]
                
                while ptr < len(bucket) and bucket[ptr] in assigned:
                    ptr += 1
                cluster_pointers[c_id] = ptr
                
                if ptr < len(bucket):
                    idx = bucket[ptr]
                    current_group.append(idx)
                    assigned.add(idx)
                    cluster_pointers[c_id] = ptr + 1
                    progress = True
                    
                    if len(current_group) == self.group_size:
                        groups_indices.append(current_group)
                        current_group = []
            
            if not progress:
                break
        
        # Sisa mahasiswa yang tidak pas dimasukkan ke kelompok terakhir
        if current_group:
            groups_indices.append(current_group)
        
        # Menyusun data keluaran lengkap kelompok
        groups_output = []
        for g_idx, group in enumerate(groups_indices):
            group_members = []
            for idx in group:
                nim = nim_list[idx]
                c_id = int(cluster_labels[idx])
                mastery_vec = feature_matrix[idx]
                avg_mastery = float(np.mean(mastery_vec))
                
                group_members.append({
                    'nim': nim,
                    'cluster_id': c_id,
                    'cluster_label': cluster_semantic.get(c_id, f"Cluster-{c_id}"),
                    'avg_mastery': round(avg_mastery, 3),
                    'mastery_vector': {
                        materi: round(float(mastery_vec[i]), 3)
                        for i, materi in enumerate(materi_list)
                    }
                })
            
            reason = self._generate_reasoning(group_members, materi_list)
            
            groups_output.append({
                'kelompok_id': g_idx + 1,
                'anggota': group_members,
                'heterogeneity_score': self._calc_heterogeneity(group_members),
                'reasoning': reason
            })
        
        return groups_output
    
    # Menghitung skor keberagaman klaster (Heterogeneity Score)
    def _calc_heterogeneity(self, members: List[Dict]) -> float:
        clusters = [m['cluster_id'] for m in members]
        unique_ratio = len(set(clusters)) / len(clusters)
        return round(unique_ratio, 3)
    
    # Membuat analisis dinamika kelompok dan tutor sebaya
    def _generate_reasoning(self, members: List[Dict], materi_list: List[str]) -> str:
        sorted_members = sorted(members, key=lambda m: m['avg_mastery'], reverse=True)
        top = sorted_members[0]
        n_clusters = len(set(m['cluster_id'] for m in members))
        
        reason_lines = [
            f"Komposisi: Heterogen dari {n_clusters} level kompetensi.",
            f"Peer-Mentor: {top['nim']} ({top['cluster_label']}, avg={top['avg_mastery']:.1%})",
            "Dynamics:"
        ]
        
        for m in sorted_members[1:]:
            weak_materi = min(
                materi_list, key=lambda mat: m['mastery_vector'].get(mat, 0)
            )
            
            helper = max(
                sorted_members,
                key=lambda x: x['mastery_vector'].get(weak_materi, 0)
                if x['nim'] != m['nim'] else -1
            )
            
            weak_val = m['mastery_vector'].get(weak_materi, 0)
            helper_val = helper['mastery_vector'].get(weak_materi, 0)
            
            reason_lines.append(
                f"  * {m['nim']} ({m['cluster_label']}) butuh bantuan '{weak_materi}' ({weak_val:.1%}) -> dibantu {helper['nim']} ({helper_val:.1%})"
            )
        
        return "\n".join(reason_lines)

# Blok eksekusi mandiri untuk demo Grouping
if __name__ == "__main__":
    import os
    import sys
    import pandas as pd
    
    # Impor sibling bkt_engine dan clustering_engine
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from bkt_engine import BKTEngine
    from clustering_engine import ClusteringEngine
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(app_dir)
    mahasiswa_csv = os.path.join(base_dir, "dataset", "mahasiswa.csv")
    kuis_csv = os.path.join(base_dir, "dataset", "kuis_struktur.csv")
    log_csv = os.path.join(base_dir, "dataset", "mahasiswa_log_jawaban.csv")
    
    print("\n" + "="*70)
    print(" GREEDY GROUPING ")
    print("="*70)
    
    print("Processing logs using BKT & Clustering Engines...")
    df_kuis = pd.read_csv(kuis_csv)
    df_log = pd.read_csv(log_csv).merge(df_kuis[['ID_Soal', 'Materi']], on='ID_Soal')
    
    bkt = BKTEngine()
    bkt.process_log(df_log)
    
    df_mhs = pd.read_csv(mahasiswa_csv)
    materi_list = df_kuis['Materi'].unique().tolist()
    nim_list = df_mhs['NIM'].astype(str).tolist()
    mhs_map = dict(zip(df_mhs['NIM'].astype(str), df_mhs['Nama']))
    
    ce = ClusteringEngine()
    X = ce.build_feature_matrix(bkt, nim_list, materi_list)
    optimal_k = ce.find_optimal_k(X)
    cluster_labels = ce.fit(X, k=optimal_k)
    profile = ce.get_cluster_profile(X, cluster_labels, materi_list)
    
    # Penentuan nama klaster secara lokal
    avg_mastery = profile.mean(axis=1).sort_values(ascending=False)
    semantic_labels = {}
    rank_labels = ["Mahir", "Cukup", "Perlu Bimbingan"]
    for rank, cluster_id in enumerate(avg_mastery.index):
        label = rank_labels[rank] if rank < len(rank_labels) else f"Cluster-{rank}"
        semantic_labels[cluster_id] = label
        
    ge = GroupingEngine(group_size=4)
    print("Menyusun kelompok heterogen (Round-Robin Greedy)...")
    groups = ge.form_groups(nim_list, cluster_labels, X, semantic_labels, materi_list)
    
    print(f"\n[OUTPUT] Berhasil membentuk {len(groups)} kelompok belajar:")
    for group in groups[:5]: 
        g_id = group['kelompok_id']
        h_score = group['heterogeneity_score']
        reasoning = group['reasoning']
        
        print(f"\n[KELOMPOK {g_id}] (Diversity Score: {h_score})")
        print("-" * 90)
        print(f"  {'NIM':<10} | {'Nama Mahasiswa':<25} | {'Klaster':<15} | {'Rata-rata P(Ln)':<15}")
        print("-" * 90)
        for member in group['anggota']:
            nim_str = str(member['nim'])
            nama = mhs_map.get(nim_str, "Tidak Dikenal")
            print(f"  {nim_str:<10} | {nama:<25} | {member['cluster_label']:<15} | {member['avg_mastery']:<15.3f}")
        print("  Dinamika Kelompok:")
        for line in reasoning.split('\n'):
            print(f"    {line}")
        print()
