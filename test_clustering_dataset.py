import os
import pandas as pd
from app.clustering_engine import ClusteringEngine

print("Program clustering mulai jalan...")

# =========================
# 1. Baca dataset
# =========================

mahasiswa_path = "dataset/mahasiswa.csv"
kuis_path = "dataset/kuis_struktur.csv"
log_path = "dataset/mahasiswa_log_jawaban.csv"

df_mahasiswa = pd.read_csv(mahasiswa_path)
df_kuis = pd.read_csv(kuis_path)
df_log = pd.read_csv(log_path)

print("\nKolom mahasiswa:")
print(df_mahasiswa.columns.tolist())

print("\nKolom kuis:")
print(df_kuis.columns.tolist())

print("\nKolom log jawaban:")
print(df_log.columns.tolist())


# =========================
# 2. Samakan nama kolom
# =========================
# Sesuaikan bagian ini kalau nama kolom di CSV kamu beda

df_mahasiswa.columns = df_mahasiswa.columns.str.lower()
df_kuis.columns = df_kuis.columns.str.lower()
df_log.columns = df_log.columns.str.lower()

print("\nKolom setelah dibuat lowercase:")
print("mahasiswa:", df_mahasiswa.columns.tolist())
print("kuis:", df_kuis.columns.tolist())
print("log:", df_log.columns.tolist())


# =========================
# 3. Tentukan nama kolom penting
# =========================

# Kolom NIM
nim_col = "nim"

# Kolom nama mahasiswa
nama_col = "nama"

# Kolom id soal / id kuis
# Biasanya bisa bernama: id_soal, soal_id, id_kuis
if "id_soal" in df_log.columns:
    soal_col_log = "id_soal"
elif "soal_id" in df_log.columns:
    soal_col_log = "soal_id"
elif "id_kuis" in df_log.columns:
    soal_col_log = "id_kuis"
else:
    raise Exception("Kolom id soal di mahasiswa_log_jawaban.csv tidak ditemukan.")

if "id_soal" in df_kuis.columns:
    soal_col_kuis = "id_soal"
elif "soal_id" in df_kuis.columns:
    soal_col_kuis = "soal_id"
elif "id_kuis" in df_kuis.columns:
    soal_col_kuis = "id_kuis"
else:
    raise Exception("Kolom id soal di kuis_struktur.csv tidak ditemukan.")

# Kolom materi
if "materi" in df_kuis.columns:
    materi_col = "materi"
elif "topik" in df_kuis.columns:
    materi_col = "topik"
elif "konsep" in df_kuis.columns:
    materi_col = "konsep"
else:
    raise Exception("Kolom materi/topik/konsep di kuis_struktur.csv tidak ditemukan.")

# Kolom skor / benar salah
if "skor" in df_log.columns:
    skor_col = "skor"
elif "skor_biner" in df_log.columns:
    skor_col = "skor_biner"
elif "nilai" in df_log.columns:
    skor_col = "nilai"
elif "benar" in df_log.columns:
    skor_col = "benar"
elif "is_correct" in df_log.columns:
    skor_col = "is_correct"
else:
    raise Exception("Kolom skor/nilai/benar/skor_biner di mahasiswa_log_jawaban.csv tidak ditemukan.")


# =========================
# 4. Gabungkan log jawaban dengan struktur kuis
# =========================

df_join = df_log.merge(
    df_kuis[[soal_col_kuis, materi_col]],
    left_on=soal_col_log,
    right_on=soal_col_kuis,
    how="left"
)

print("\nData setelah log digabung dengan materi:")
print(df_join.head())


# =========================
# 5. Buat mastery vector
# =========================
# Rata-rata skor tiap mahasiswa pada tiap materi

mastery = df_join.pivot_table(
    index=nim_col,
    columns=materi_col,
    values=skor_col,
    aggfunc="mean",
    fill_value=0.2
)

mastery = mastery.reset_index()

# Gabungkan nama mahasiswa
df_mastery = df_mahasiswa[[nim_col, nama_col]].merge(
    mastery,
    on=nim_col,
    how="inner"
)

print("\nMastery Vector:")
print(df_mastery)


# =========================
# 6. Siapkan data untuk K-Means
# =========================

materi_list = [col for col in df_mastery.columns if col not in [nim_col, nama_col]]

X = df_mastery[materi_list].values

print("\nFeature Matrix:")
print(X)


# =========================
# 7. Jalankan K-Means
# =========================

cluster_engine = ClusteringEngine()

labels = cluster_engine.fit(X, k=3)

df_mastery["cluster"] = labels


# =========================
# 8. Ubah cluster menjadi kategori
# =========================

cluster_mean = df_mastery.groupby("cluster")[materi_list].mean().mean(axis=1)

urutan_cluster = cluster_mean.sort_values().index.tolist()

mapping_kategori = {
    urutan_cluster[0]: "Kurang",
    urutan_cluster[1]: "Cukup",
    urutan_cluster[2]: "Mahir"
}

df_mastery["kategori"] = df_mastery["cluster"].map(mapping_kategori)


# =========================
# 9. Tampilkan hasil
# =========================

print("\nHasil Clustering:")
print(df_mastery[[nim_col, nama_col, "cluster", "kategori"]])

print("\nProfil Cluster:")
profile = cluster_engine.get_cluster_profile(X, labels, materi_list)
print(profile)


# =========================
# 10. Simpan hasil
# =========================

output_path = "dataset/hasil_cluster_mahasiswa.csv"
df_mastery.to_csv(output_path, index=False)

print(f"\nFile hasil berhasil disimpan di: {output_path}")