from flask import Flask, render_template, jsonify, request
import pandas as pd
import sys
import os
import subprocess

# Tambahkan path direktori ke system path agar modul dapat diimpor dengan benar
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pipeline import run_pipeline
except ImportError:
    # pyrefly: ignore [missing-import]
    from app.pipeline import run_pipeline

app = Flask(__name__)

# Path ke CSV
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAHASISWA_CSV = os.path.join(BASE_DIR, "dataset", "mahasiswa.csv")
KUIS_CSV = os.path.join(BASE_DIR, "dataset", "kuis_struktur.csv")
LOG_CSV = os.path.join(BASE_DIR, "dataset", "mahasiswa_log_jawaban.csv")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/results")
def get_results():
    if not (os.path.exists(MAHASISWA_CSV) and os.path.exists(KUIS_CSV) and os.path.exists(LOG_CSV)):
        return jsonify({"error": "File dataset tidak ditemukan. Silakan jalankan scripts/generate_dummy_data.py terlebih dahulu."}), 400
    
    try:
        # Muat pemetaan nama mahasiswa
        df_mhs = pd.read_csv(MAHASISWA_CSV)
        mhs_map = dict(zip(df_mhs['NIM'].astype(str), df_mhs['Nama']))
        
        # Jalankan pipeline
        results = run_pipeline(MAHASISWA_CSV, KUIS_CSV, LOG_CSV, group_size=4)
        
        # Perkaya kelompok dengan nama mahasiswa
        enriched_groups = []
        for group in results['groups']:
            enriched_members = []
            for member in group['anggota']:
                nim_str = str(member['nim'])
                enriched_members.append({
                    **member,
                    'nama': mhs_map.get(nim_str, "Tidak Dikenal")
                })
            enriched_groups.append({
                **group,
                'anggota': enriched_members
            })
            
        # Perkaya learning path dengan nama
        enriched_learning_paths = {}
        for nim, path in results['learning_paths'].items():
            nim_str = str(nim)
            enriched_learning_paths[nim_str] = {
                'nama': mhs_map.get(nim_str, "Tidak Dikenal"),
                'nim': nim_str,
                'path': path
            }
            
        # Konversi profil klaster (pandas DataFrame) ke format yang dapat diserialisasi ke JSON
        profile_df = results['cluster_profile'].reset_index()
        
        # Cari label semantik dengan memindai kelompok yang telah diperkaya
        cluster_semantic = {}
        for g in enriched_groups:
            for m in g['anggota']:
                cluster_semantic[int(m['cluster_id'])] = m['cluster_label']
                
        profile_list = []
        for idx, row in profile_df.iterrows():
            c_id = int(row['cluster'])
            profile_list.append({
                'cluster_id': c_id,
                'cluster_label': cluster_semantic.get(c_id, f"Cluster {c_id}"),
                'scores': {col: float(row[col]) for col in profile_df.columns if col != 'cluster'}
            })
            
        return jsonify({
            'groups': enriched_groups,
            'learning_paths': enriched_learning_paths,
            'cluster_profile': profile_list,
            'cluster_labels': {k: int(v) for k, v in results['cluster_labels'].items()},
            'prerequisite_graph': results.get('prerequisite_graph', {})
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_datasets():
    if 'mahasiswa' not in request.files or 'kuis' not in request.files or 'log' not in request.files:
        return jsonify({"error": "Ketiga berkas dataset wajib diunggah."}), 400

    mahasiswa_file = request.files['mahasiswa']
    kuis_file = request.files['kuis']
    log_file = request.files['log']

    if mahasiswa_file.filename == '' or kuis_file.filename == '' or log_file.filename == '':
        return jsonify({"error": "Salah satu berkas tidak terpilih."}), 400

    def read_uploaded_file(uploaded_file):
        filename = uploaded_file.filename.lower()
        if filename.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif filename.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)
        else:
            raise ValueError(f"Format file '{uploaded_file.filename}' tidak didukung. Gunakan CSV atau Excel (.xlsx/.xls).")

    try:
        df_mhs = read_uploaded_file(mahasiswa_file)
        df_kuis = read_uploaded_file(kuis_file)
        df_log = read_uploaded_file(log_file)

        # 1. Validasi Kolom Mahasiswa
        req_mhs = {'NIM', 'Nama'}
        if not req_mhs.issubset(df_mhs.columns):
            missing = req_mhs - set(df_mhs.columns)
            return jsonify({"error": f"Kolom pada data mahasiswa tidak sesuai. Kolom kurang: {', '.join(missing)}"}), 400

        # 2. Validasi Kolom Kuis Struktur
        req_kuis = {'ID_Soal', 'Materi', 'Submateri', 'Bobot', 'Opsi_A', 'Opsi_B', 'Opsi_C', 'Opsi_D', 'Kunci'}
        if not req_kuis.issubset(df_kuis.columns):
            missing = req_kuis - set(df_kuis.columns)
            return jsonify({"error": f"Kolom pada data kuis tidak sesuai. Kolom kurang: {', '.join(missing)}"}), 400

        # 3. Validasi Kolom Log Jawaban
        req_log = {'NIM', 'ID_Soal', 'Jawaban_Mahasiswa', 'Skor_Biner'}
        if not req_log.issubset(df_log.columns):
            missing = req_log - set(df_log.columns)
            return jsonify({"error": f"Kolom pada log jawaban tidak sesuai. Kolom kurang: {', '.join(missing)}"}), 400

        # 4. Validasi Integritas Relasional Sederhana
        df_mhs['NIM'] = df_mhs['NIM'].astype(str).str.strip()
        df_log['NIM'] = df_log['NIM'].astype(str).str.strip()
        df_kuis['ID_Soal'] = df_kuis['ID_Soal'].astype(str).str.strip()
        df_log['ID_Soal'] = df_log['ID_Soal'].astype(str).str.strip()

        mhs_nims = set(df_mhs['NIM'])
        log_nims = set(df_log['NIM'])
        invalid_nims = log_nims - mhs_nims
        if invalid_nims:
            sample_invalid = list(invalid_nims)[:5]
            return jsonify({"error": f"NIM pada log jawaban tidak terdaftar di data mahasiswa: {', '.join(sample_invalid)}"}), 400

        kuis_soal_ids = set(df_kuis['ID_Soal'])
        log_soal_ids = set(df_log['ID_Soal'])
        invalid_soals = log_soal_ids - kuis_soal_ids
        if invalid_soals:
            sample_invalid_soal = list(invalid_soals)[:5]
            return jsonify({"error": f"ID_Soal pada log jawaban tidak ditemukan di data kuis: {', '.join(sample_invalid_soal)}"}), 400

        # 5. Simpan file sebagai CSV di folder dataset/ (menimpa berkas yang lama)
        os.makedirs(os.path.dirname(MAHASISWA_CSV), exist_ok=True)
        df_mhs.to_csv(MAHASISWA_CSV, index=False)
        df_kuis.to_csv(KUIS_CSV, index=False)
        df_log.to_csv(LOG_CSV, index=False)

        return jsonify({"message": "Dataset berhasil diunggah dan diperbarui!"})

    except Exception as e:
        return jsonify({"error": f"Gagal membaca atau memproses dataset: {str(e)}"}), 400

@app.route("/api/reset", methods=["POST"])
def reset_datasets():
    try:
        script_path = os.path.join(BASE_DIR, "scripts", "generate_dummy_data.py")
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)
        return jsonify({"message": "Dataset berhasil direset ke data dummy bawaan!", "details": result.stdout})
    except Exception as e:
        return jsonify({"error": f"Gagal mereset dataset: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
