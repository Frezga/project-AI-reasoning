# app/clustering_engine.py

# ALGORITMA K-MEANS

import os
import sys
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


# Engine untuk mengklasifikasikan mahasiswa ke dalam klaster kemampuan
class ClusteringEngine:

    # Inisialisasi model scaler dan K-Means
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.optimal_k = None
        self.feature_matrix = None
        self.nim_list = None

    # Membangun matriks fitur X dari vektor penguasaan BKT
    def build_feature_matrix(self, bkt_engine, nim_list: list, materi_list: list) -> np.ndarray:
        self.nim_list = nim_list
        rows = []

        for nim in nim_list:
            mastery = bkt_engine.get_mastery_vector(nim)
            row = [mastery.get(materi, 0.20) for materi in materi_list]
            rows.append(row)

        self.feature_matrix = np.array(rows)
        return self.feature_matrix

    # Menentukan nilai K optimal dengan Elbow Method dan Silhouette Score
    def find_optimal_k(self, X: np.ndarray, k_range: range = range(2, 8)) -> int:
        X_scaled = self.scaler.fit_transform(X)

        inertias = []
        silhouette_scores = []

        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)

            inertias.append(km.inertia_)

            if k > 1:
                score = silhouette_score(X_scaled, labels)
                silhouette_scores.append(score)

        x_vals = np.array(list(k_range))
        inertia_vals = np.array(inertias)

        x_norm = (x_vals - x_vals.min()) / (x_vals.max() - x_vals.min())
        y_norm = (inertia_vals - inertia_vals.min()) / (inertia_vals.max() - inertia_vals.min())

        distances = np.abs(
            (y_norm[-1] - y_norm[0]) * x_norm
            - (x_norm[-1] - x_norm[0]) * y_norm
            + x_norm[-1] * y_norm[0]
            - y_norm[-1] * x_norm[0]
        ) / np.sqrt(
            (y_norm[-1] - y_norm[0]) ** 2
            + (x_norm[-1] - x_norm[0]) ** 2
        )

        elbow_k = list(k_range)[np.argmax(distances)]

        if silhouette_scores:
            sil_k = list(k_range)[np.argmax(silhouette_scores)]
        else:
            sil_k = elbow_k

        self.optimal_k = min(elbow_k, sil_k) if elbow_k != sil_k else elbow_k

        print(f"Elbow K: {elbow_k}, Silhouette K: {sil_k} -> Optimal K: {self.optimal_k}")

        return self.optimal_k

    # Melakukan clustering K-Means pada data mahasiswa
    def fit(self, X: np.ndarray, k: int = None) -> np.ndarray:
        if k is None:
            k = self.optimal_k or self.find_optimal_k(X)

        # Pakai fit_transform supaya scaler belajar dari data dulu
        X_scaled = self.scaler.fit_transform(X)

        self.kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(X_scaled)

        return labels

    # Menghitung profil rata-rata tiap cluster
    def get_cluster_profile(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        materi_list: list
    ) -> pd.DataFrame:
        df = pd.DataFrame(X, columns=materi_list)
        df["cluster"] = labels

        return df.groupby("cluster").mean().round(3)


# Blok eksekusi mandiri untuk demo clustering
if __name__ == "__main__":

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from bkt_engine import BKTEngine

    app_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(app_dir)

    mahasiswa_csv = os.path.join(base_dir, "dataset", "mahasiswa.csv")
    kuis_csv = os.path.join(base_dir, "dataset", "kuis_struktur.csv")
    log_csv = os.path.join(base_dir, "dataset", "mahasiswa_log_jawaban.csv")

    print("\n" + "=" * 70)
    print("K-MEANS CLUSTERING")
    print("=" * 70)

    print("Memproses logs menggunakan BKT Engine...")

    df_kuis = pd.read_csv(kuis_csv)
    df_log = pd.read_csv(log_csv)

    df_log = df_log.merge(
        df_kuis[["ID_Soal", "Materi"]],
        on="ID_Soal",
        how="left"
    )

    bkt = BKTEngine()
    bkt.process_log(df_log)

    df_mhs = pd.read_csv(mahasiswa_csv)

    materi_list = df_kuis["Materi"].unique().tolist()
    nim_list = df_mhs["NIM"].astype(str).tolist()

    ce = ClusteringEngine()

    print("Membangun matriks fitur X...")
    X = ce.build_feature_matrix(bkt, nim_list, materi_list)

    print(f"Ukuran Feature Matrix X: {X.shape}")

    print("\nSampel Matriks Fitur 5 Mahasiswa Pertama:")
    print("-" * 115)

    headers = [f"{materi[:12]}..." for materi in materi_list]
    print(f"{'NIM':<10} | " + " | ".join(f"{header:<13}" for header in headers))

    print("-" * 115)

    for i in range(min(5, len(nim_list))):
        row = " | ".join(f"{X[i][j]:<13.3f}" for j in range(len(materi_list)))
        print(f"{nim_list[i]:<10} | {row}")

    print("-" * 115)

    print("\nMenghitung K optimal menggunakan Elbow Method dan Silhouette Score...")
    optimal_k = ce.find_optimal_k(X)

    print(f"\nFitting K-Means dengan K = {optimal_k}...")
    cluster_labels = ce.fit(X, k=optimal_k)

    profile = ce.get_cluster_profile(X, cluster_labels, materi_list)

    avg_mastery = profile.mean(axis=1).sort_values(ascending=False)

    semantic_labels = {}
    rank_labels = ["Mahir", "Cukup", "Perlu Bimbingan"]

    for rank, cluster_id in enumerate(avg_mastery.index):
        if rank < len(rank_labels):
            semantic_labels[cluster_id] = rank_labels[rank]
        else:
            semantic_labels[cluster_id] = f"Cluster-{rank}"

    print("\n[OUTPUT] Centroid Profil Klaster:")
    print("-" * 110)

    print(
        f"{'Cluster ID':<10} | {'Label Semantik':<15} | "
        + " | ".join(f"{materi[:10]:<10}" for materi in materi_list)
    )

    print("-" * 110)

    for cluster_id in profile.index:
        label = semantic_labels.get(cluster_id, f"Cluster-{cluster_id}")
        row_scores = " | ".join(f"{profile.loc[cluster_id, materi]:<10.3f}" for materi in materi_list)
        print(f"{cluster_id:<10} | {label:<15} | {row_scores}")

    print("-" * 110)