# app/clustering_engine.py

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

class ClusteringEngine:
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.optimal_k = None
        self.feature_matrix = None
        self.nim_list = None
    
    def build_feature_matrix(self, bkt_engine, nim_list: list, materi_list: list) -> np.ndarray:
        """
        Membangun matriks fitur (feature matrix) X dari vektor penguasaan (mastery vector) BKT.
        
        Mengembalikan:
            X: ndarray shape (n_mahasiswa, n_materi)
        """
        self.nim_list = nim_list
        rows = []
        for nim in nim_list:
            mastery = bkt_engine.get_mastery_vector(nim)
            row = [mastery.get(m, 0.20) for m in materi_list]
            rows.append(row)
        
        self.feature_matrix = np.array(rows)
        return self.feature_matrix
    
    def find_optimal_k(self, X: np.ndarray, k_range: range = range(2, 8)) -> int:
        """
        Menentukan K optimal menggunakan Elbow Method + Silhouette Score.
        
        Strategi: Gabungkan kedua metrik untuk keputusan yang lebih tangguh (robust).
        - Elbow Method: Cari 'siku' pada kurva inertia (WCSS)
        - Silhouette Score: Pilih K dengan skor tertinggi (semakin tinggi = lebih baik)
        """
        X_scaled = self.scaler.fit_transform(X)
        
        inertias = []
        silhouette_scores = []
        
        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = km.fit_predict(X_scaled)
            inertias.append(km.inertia_)
            if k > 1:
                s_score = silhouette_score(X_scaled, labels)
                silhouette_scores.append(s_score)
        
        # Hitung elbow menggunakan metode kneedle (jarak dari garis lurus)
        x_vals = np.array(list(k_range))
        inertia_vals = np.array(inertias)
        
        # Normalisasi untuk perbandingan
        x_norm = (x_vals - x_vals.min()) / (x_vals.max() - x_vals.min())
        y_norm = (inertia_vals - inertia_vals.min()) / (inertia_vals.max() - inertia_vals.min())
        
        # Jarak titik dari garis lurus (titik pertama ke titik terakhir)
        distances = np.abs(
            (y_norm[-1] - y_norm[0]) * x_norm - (x_norm[-1] - x_norm[0]) * y_norm +
            x_norm[-1] * y_norm[0] - y_norm[-1] * x_norm[0]
        ) / np.sqrt((y_norm[-1] - y_norm[0])**2 + (x_norm[-1] - x_norm[0])**2)
        
        elbow_k = list(k_range)[np.argmax(distances)]
        
        # Pilih K dengan silhouette tertinggi
        if silhouette_scores:
            sil_k = list(k_range)[1 + np.argmax(silhouette_scores)]
        else:
            sil_k = elbow_k
        
        # Konsensus: jika sama pakai itu, jika beda ambil yang lebih kecil (lebih konservatif)
        self.optimal_k = min(elbow_k, sil_k) if elbow_k != sil_k else elbow_k
        
        print(f"Elbow K: {elbow_k}, Silhouette K: {sil_k} -> Optimal K: {self.optimal_k}")
        return self.optimal_k
    
    def fit(self, X: np.ndarray, k: int = None) -> np.ndarray:
        """
        Melatih K-Means dan mengembalikan label klaster tiap mahasiswa.
        """
        if k is None:
            k = self.optimal_k or self.find_optimal_k(X)
        
        X_scaled = self.scaler.transform(X)
        self.kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = self.kmeans.fit_predict(X_scaled)
        return labels
    
    def get_cluster_profile(self, X: np.ndarray, labels: np.ndarray, 
                            materi_list: list) -> pd.DataFrame:
        """
        Menghitung centroid tiap klaster untuk interpretasi profil.
        
        Mengembalikan:
            DataFrame: rata-rata P(Ln) per materi per klaster
        """
        df = pd.DataFrame(X, columns=materi_list)
        df['cluster'] = labels
        return df.groupby('cluster').mean().round(3)

        