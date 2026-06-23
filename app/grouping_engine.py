# app/grouping_engine.py

import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict

class GroupingEngine:
    
    def __init__(self, group_size: int = 4):
        self.group_size = group_size
    
    def form_groups(self,
                    nim_list: List[str],
                    cluster_labels: np.ndarray,
                    feature_matrix: np.ndarray,
                    cluster_semantic: Dict[int, str],
                    materi_list: List[str]) -> List[Dict]:
        """
        Algoritma Greedy untuk membentuk kelompok heterogen.
        
        Strategi:
        1. Urutkan mahasiswa berdasarkan klaster (urutan: Mahir, Cukup, Remedial)
        2. Gunakan Round-Robin Greedy: ambil satu mahasiswa dari tiap klaster
           secara bergiliran sampai kelompok penuh.
        3. Sisa mahasiswa (jika N tidak habis dibagi group_size) 
           didistribusikan ke kelompok yang paling heterogen.
        
        Mengembalikan:
            List of group dictionaries dengan informasi lengkap + reasoning (alasan pembentukan)
        """
        n = len(nim_list)
        
        # Kelompokkan mahasiswa per cluster
        cluster_buckets: Dict[int, List[int]] = defaultdict(list)
        for idx, nim in enumerate(nim_list):
            cluster_id = int(cluster_labels[idx])
            cluster_buckets[cluster_id].append(idx)
        
        # Sort cluster berdasarkan rank (Mahir dulu, lalu Cukup, lalu Remedial)
        avg_mastery_per_cluster = {}
        for c_id, indices in cluster_buckets.items():
            avg_mastery_per_cluster[c_id] = np.mean(feature_matrix[indices].mean(axis=1))
        
        sorted_clusters = sorted(
            cluster_buckets.keys(),
            key=lambda c: avg_mastery_per_cluster[c],
            reverse=True  # Mahir di depan
        )
        
        # Round-Robin Greedy Assignment
        groups_indices = []  # List of lists of student indices
        current_group = []
        
        # Iterator round-robin antar cluster
        cluster_pointers = {c: 0 for c in sorted_clusters}
        
        # Flatten dengan round-robin
        assigned = set()
        while len(assigned) < n:
            progress = False
            for c_id in sorted_clusters:
                bucket = cluster_buckets[c_id]
                ptr = cluster_pointers[c_id]
                
                # Temukan mahasiswa berikutnya yang belum di-assign
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
        
        # Sisa mahasiswa → distribusikan ke kelompok terakhir
        if current_group:
            groups_indices.append(current_group)
        
        # Build output dengan reasoning
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
    
    def _calc_heterogeneity(self, members: List[Dict]) -> float:
        """
        Heterogenitas = proporsi klaster unik dalam kelompok.
        Skor = 1.0 berarti semua anggota berasal dari klaster berbeda (ideal).
        """
        clusters = [m['cluster_id'] for m in members]
        unique_ratio = len(set(clusters)) / len(clusters)
        return round(unique_ratio, 3)
    
    def _generate_reasoning(self, members: List[Dict], materi_list: List[str]) -> str:
        """
        Menghasilkan string alasan (reasoning) mengapa kelompok ini dibentuk.
        
        Logika:
        1. Identifikasi siapa "mentor" (mahir) dan siapa yang butuh bantuan
        2. Identifikasi keunggulan spesifik tiap anggota pada materi tertentu
        3. Format alasan (reasoning) sebagai narasi yang mudah dibaca (readable)
        """
        reasons = []
        
        # Sort by avg_mastery descending
        sorted_members = sorted(members, key=lambda m: m['avg_mastery'], reverse=True)
        
        # Identifikasi peran
        top = sorted_members[0]
        bottom = sorted_members[-1]
        
        reasons.append(
            f"Kelompok ini dirancang heterogen dari {len(set(m['cluster_id'] for m in members))} "
            f"level kompetensi berbeda."
        )
        
        reasons.append(
            f"{top['nim']} ({top['cluster_label']}, rata-rata penguasaan={top['avg_mastery']:.1%}) "
            f"berperan sebagai peer-mentor untuk anggota lain."
        )
        
        # Identifikasi materi unggulan & kelemahan
        for m in sorted_members[1:]:
            strong_materi = max(
                materi_list, key=lambda mat: m['mastery_vector'].get(mat, 0)
            )
            weak_materi = min(
                materi_list, key=lambda mat: m['mastery_vector'].get(mat, 0)
            )
            
            # Cari siapa yang kuat di weak_materi tersebut
            helper = max(
                sorted_members,
                key=lambda x: x['mastery_vector'].get(weak_materi, 0)
                if x['nim'] != m['nim'] else -1
            )
            
            reasons.append(
                f"{m['nim']} ({m['cluster_label']}) unggul di '{strong_materi}' "
                f"(P(L)={m['mastery_vector'].get(strong_materi, 0):.1%}) "
                f"namun perlu penguatan di '{weak_materi}' "
                f"(P(L)={m['mastery_vector'].get(weak_materi, 0):.1%}), "
                f"di mana {helper['nim']} dapat membantu "
                f"(P(L)={helper['mastery_vector'].get(weak_materi, 0):.1%})."
            )
        
        return " ".join(reasons)