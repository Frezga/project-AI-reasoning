# scripts/generate_dummy_data.py

import pandas as pd
import numpy as np
from pathlib import Path

# Atur seed untuk reproduksibilitas
np.random.seed(42)

# Definisikan direktori
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset"
DATASET_DIR.mkdir(exist_ok=True)

# 1. Hasilkan mahasiswa.csv (40 Mahasiswa)
nama_depan = ["Andi", "Budi", "Citra", "Dian", "Eko", "Farah", "Gilang", "Hana", "Irfan", "Joko",
              "Kiki", "Lukman", "Maya", "Nanda", "Oscar", "Putri", "Qori", "Rafi", "Sari", "Taufik",
              "Ulfa", "Vino", "Wulan", "Xander", "Yuni", "Zaki", "Arini", "Bagus", "Clara", "Doni",
              "Elvira", "Farhan", "Gita", "Hendra", "Ika", "Jihan", "Kevin", "Lina", "Miko", "Nina"]

nama_belakang = ["Prasetyo", "Santoso", "Lestari", "Rahayu", "Wahyudi", "Nadia", "Ramadan", "Pertiwi",
                 "Maulana", "Susilo", "Amalia", "Hakim", "Sari", "Kurnia", "Firmansyah", "Wulandari",
                 "Handayani", "Hidayat", "Dewi", "Pratama", "Nurjanah", "Saputra", "Agustina", "Mandala",
                 "Puspita", "Gunawan", "Fitriani", "Marliana", "Permana", "Indah", "Setiawan", "Putri",
                 "Akbar", "Sulistyawati", "Utami", "Wijaya", "Kusuma", "Harahap", "Siregar", "Lubis"]

mahasiswa_rows = []
for i in range(1, 41):
    nim = f"23010{str(i).zfill(2)}"
    nama = f"{nama_depan[i-1]} {nama_belakang[i-1]}"
    mahasiswa_rows.append({"NIM": nim, "Nama": nama})

df_mahasiswa = pd.DataFrame(mahasiswa_rows)
df_mahasiswa.to_csv(DATASET_DIR / "mahasiswa.csv", index=False)
print("mahasiswa.csv generated successfully.")

# 2. Hasilkan kuis_struktur.csv (60 Soal di 6 topik OS)
materi_topics = [
    ("Manajemen Proses", ["Konsep Proses", "Thread dan Konkurensi", "Sinkronisasi", "Deadlock"]),
    ("Penjadwalan CPU", ["Konsep Penjadwalan", "Algoritma FCFS dan SJF", "Round Robin dan Priority", "Multilevel Queue"]),
    ("Manajemen Memori", ["Konsep Memori", "Paging", "Segmentasi"]),
    ("Virtual Memory", ["Konsep Virtual Memory", "Page Replacement", "Thrashing"]),
    ("File System", ["Konsep File System", "Implementasi File System", "Journaling dan Reliability"]),
    ("I/O Management", ["Konsep I/O", "Disk Scheduling", "DMA dan Buffering"])
]

kuis_rows = []
soal_counter = 1

# mendefinisikan jawaban
options_pool = [
    ("Program yang sedang dieksekusi", "File yang tersimpan di disk", "Instruksi dalam memori ROM", "Unit penyimpanan data", "A"),
    ("Ready -> Running -> Blocked", "New -> Ready -> Running -> Waiting -> Terminated", "Running -> Ready -> New", "Blocked -> Running -> Terminated", "B"),
    ("Process Control Block (PCB)", "Memory Allocation Table", "File Descriptor Table", "Interrupt Vector Table", "A"),
    ("Thread berbagi address space; Process tidak", "Process berbagi address space; Thread tidak", "Keduanya berbagi address space", "Keduanya tidak berbagi address space", "A"),
    ("Race condition", "Deadlock", "Starvation", "Thrashing", "A"),
    ("Mutex", "Semaphore", "Monitor", "Spinlock", "B"),
    ("Mutual Exclusion", "Progress", "Bounded Waiting", "Semua benar", "D"),
    ("wait() dan signal()", "lock() dan unlock()", "P() dan V() saja", "acquire() dan release()", "C"),
    ("Deadlock", "Starvation", "Livelock", "Race Condition", "A"),
    ("Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait", "Mutual Exclusion, Preemption, Hold and Wait", "No Preemption, Circular Wait saja", "Hold and Wait, Starvation", "A"),
]

for topic_name, subtopics in materi_topics:
    # 10 soal per topik
    for j in range(10):
        soal_id = f"Q{str(soal_counter).zfill(3)}"
        subtopic = subtopics[j % len(subtopics)]
        # Bobot berkisar dari 1 sampai 3
        bobot = 1 if j < 4 else (2 if j < 8 else 3)
        
        # Pilih opsi dari kumpulan opsi atau buat opsi dummy
        pool_idx = (soal_counter - 1) % len(options_pool)
        opt_a, opt_b, opt_c, opt_d, kunci = options_pool[pool_idx]
        
        kuis_rows.append({
            "ID_Soal": soal_id,
            "Materi": topic_name,
            "Submateri": subtopic,
            "Bobot": bobot,
            "Opsi_A": opt_a,
            "Opsi_B": opt_b,
            "Opsi_C": opt_c,
            "Opsi_D": opt_d,
            "Kunci": kunci
        })
        soal_counter += 1

df_kuis = pd.DataFrame(kuis_rows)
df_kuis.to_csv(DATASET_DIR / "kuis_struktur.csv", index=False)
print("kuis_struktur.csv generated successfully.")

# 3. Hasilkan mahasiswa_log_jawaban.csv (Log Kuis untuk 40 mahasiswa * 60 soal = 2400 baris)
# Definisikan profil untuk mahasiswa
# Kita ingin: 10 Mahir (penguasaan tinggi), 20 Cukup (penguasaan sedang), 10 Remedial (penguasaan rendah)
profiles = {}
for idx, row in df_mahasiswa.iterrows():
    nim = row["NIM"]
    if idx < 10:
        profiles[nim] = "mahir"
    elif idx < 30:
        profiles[nim] = "cukup"
    else:
        profiles[nim] = "remedial"

# Tambahkan beberapa kekuatan dan kelemahan spesifik agar klaster lebih menarik
# Contoh: mahasiswa 2301015 (cukup) mungkin sangat baik di "Manajemen Proses" tetapi lemah di "Virtual Memory"
accuracy_modifiers = {}
for idx, row in df_mahasiswa.iterrows():
    nim = row["NIM"]
    accuracy_modifiers[nim] = {}
    if profiles[nim] == "cukup":
        # Masukkan variasi: beberapa baik di Proses/Penjadwalan, yang lain di Memori/VM, yang lain di FS/IO
        if idx % 3 == 0:
            accuracy_modifiers[nim] = {"Manajemen Proses": 0.25, "Penjadwalan CPU": 0.25, "Virtual Memory": -0.25}
        elif idx % 3 == 1:
            accuracy_modifiers[nim] = {"Manajemen Memori": 0.25, "Virtual Memory": 0.25, "File System": -0.25}
        else:
            accuracy_modifiers[nim] = {"File System": 0.25, "I/O Management": 0.25, "Manajemen Proses": -0.25}

base_accuracies = {
    "mahir": 0.88,
    "cukup": 0.60,
    "remedial": 0.28
}

log_rows = []
for idx, row in df_mahasiswa.iterrows():
    nim = row["NIM"]
    profile = profiles[nim]
    base_acc = base_accuracies[profile]
    
    # Kita akan menghasilkan jawaban untuk semua 60 soal
    for _, kuis_row in df_kuis.iterrows():
        soal_id = kuis_row["ID_Soal"]
        materi = kuis_row["Materi"]
        kunci = kuis_row["Kunci"]
        
        # Hitung probabilitas akhir menjawab dengan benar
        acc = base_acc + accuracy_modifiers[nim].get(materi, 0.0)
        # Batasi antara 0.05 dan 0.95
        acc = max(0.05, min(0.95, acc))
        
        is_correct = np.random.random() < acc
        
        # Tentukan jawaban
        opsi_lain = [o for o in ["A", "B", "C", "D"] if o != kunci]
        if is_correct:
            jawaban = kunci
            skor = 1
        else:
            jawaban = np.random.choice(opsi_lain)
            skor = 0
            
        log_rows.append({
            "NIM": nim,
            "ID_Soal": soal_id,
            "Jawaban_Mahasiswa": jawaban,
            "Skor_Biner": skor
        })

df_log = pd.DataFrame(log_rows)
df_log.to_csv(DATASET_DIR / "mahasiswa_log_jawaban.csv", index=False)
print(f"mahasiswa_log_jawaban.csv generated successfully with {len(df_log)} rows.")
print("All dummy datasets are ready!")
