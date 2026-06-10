```markdown
# Dokumentasi Progress Week 1

## Bagian 1: Inisialisasi Workspace Bersama
Untuk memfasilitasi kolaborasi secara asynchronous dan menghindari konflik saat menulis kode, tim memanfaatkan environment **Google Colab** yang diintegrasikan dengan penyimpanan bersama (**Google Drive**) serta version control **GitHub**.

### Manajemen Berkas & Dataset di Google Drive
- Membuat folder induk di Google Drive dan membagikan akses kepada seluruh anggota tim.  
- Di dalam folder induk, dibuat sub-folder bernama `dataset/` untuk menyimpan berkas data `studentVle.csv` yang diunduh dari Kaggle.

### Inisialisasi Environment Google Colab
Setiap notebook wajib menyertakan blok kode inisialisasi untuk mounting drive secara otomatis:

```python
from google.colab import drive
import os

drive.mount('/content/drive')

SHARED_FOLDER_PATH = '/content/drive/MyDrive/Proyek_AI_Path_Learning'
os.chdir(SHARED_FOLDER_PATH)

print("Workspace berhasil diinisialisasi. Direktori saat ini:", os.getcwd())
```

### Alur Kerja Sinkronisasi dengan GitHub
- Membuat repository GitHub untuk menyimpan progress langsung dari Colab.  
- Membagi pengerjaan ke dalam file notebook terpisah berdasarkan modul {1, 2, 3} sebelum digabungkan di fase akhir.

---

## Bagian 2: Tech Stack
- **Bahasa Pemrograman:** Python, JavaScript  
- **Library Manipulasi & Analisis Data:**  
  - `pandas`, `numpy` → memproses log aktivitas siswa, membersihkan data interaksi, menyiapkan matriks input.  
- **Library Kecerdasan Buatan & Pemodelan:**  
  - `pyBKT` → implementasi Bayesian Knowledge Tracing berbasis HMM.  
  - `scikit-learn` → implementasi K-Means Clustering.  
  - `PyTorch` / `TensorFlow` (opsional) → eksperimen Deep Knowledge Tracing.  

---

## Bagian 3: Struktur Pengembangan Modul
Proyek dibagi menjadi 3 pilar utama:

### Modul 1: Diagnostik & Pelacakan Kemampuan (Bayesian Knowledge Tracing)
- **Tujuan:** Mengidentifikasi kesenjangan pemahaman mahasiswa.  
- **Implementasi Teknis:**  
  - Menggunakan log interaksi dari `studentVle.csv` sebagai data time-series.  
  - Inferensi probabilitas penguasaan konsep dengan HMM.  

### Modul 2: Segmentasi Karakteristik Siswa (K-Means Clustering)
- **Tujuan:** Mengelompokkan siswa berdasarkan profil penguasaan materi.  
- **Implementasi Teknis:**  
  - Mengambil vektor probabilitas penguasaan materi dari Modul 1.  
  - Menerapkan K-Means Clustering untuk membentuk klaster (Mahir, Cukup, Kurang).  

### Modul 3: Pembentukan Kelompok Belajar Adaptif (Greedy Algorithm)
- **Tujuan:** Memasangkan mahasiswa kesulitan dengan mahasiswa ahli untuk peer tutoring.  
- **Implementasi Teknis:**  
  - **Fungsi Seleksi:** memilih tutor terbaik dari klaster tinggi.  
  - **Fungsi Kelayakan:** memastikan tidak ada konflik personal/blacklist.  
  - **Fungsi Objektif:** membentuk tim dengan komposisi kompetensi maksimal dan proporsional.  

---

## Bagian 4: Rencana Aksi & Pembagian Tugas
1. **Jauhar Mufid Tamir** (Modul 1 & Data Preprocessing)  
   - Ekstraksi dataset dengan Pandas.  
   - Implementasi Bayesian Knowledge Tracing menggunakan `pyBKT`.  

2. **Muhamad Afif Aji Putra** (Modul 2 & Evaluasi Model)  
   - Mengolah keluaran Modul 1 ke dalam K-Means Clustering.  
   - Menentukan jumlah klaster optimal (Elbow Method).  

3. **Muhammad Akbar Kurniawan** (Modul 3 & Sistem Aturan)  
   - Menyusun algoritma Greedy untuk pembentukan kelompok belajar.  
   - Integrasi fungsi kelayakan berbasis kompetensi dan relasi antar-mahasiswa.  

---

## Catatan Kelompok
Setiap anggota wajib melakukan **unit testing** dengan data dummy setiap kali menambahkan fungsi/metode baru di Colab, untuk memastikan keluaran matriks/array sesuai sebelum integrasi menyeluruh.
```

---