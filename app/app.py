from flask import Flask, render_template, jsonify
import pandas as pd
import sys
import os

# Add directory paths to system path to import modules correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pipeline import run_pipeline
except ImportError:
    # pyrefly: ignore [missing-import]
    from app.pipeline import run_pipeline

app = Flask(__name__)

# Paths to CSV
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
        return jsonify({"error": "Dataset files are missing. Please run scripts/generate_dummy_data.py first."}), 400
    
    try:
        # Load mahasiswa name mapping
        df_mhs = pd.read_csv(MAHASISWA_CSV)
        mhs_map = dict(zip(df_mhs['NIM'].astype(str), df_mhs['Nama']))
        
        # Run pipeline
        results = run_pipeline(MAHASISWA_CSV, KUIS_CSV, LOG_CSV, group_size=4)
        
        # Enrich groups with student names
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
            
        # Enrich learning paths with names
        enriched_learning_paths = {}
        for nim, path in results['learning_paths'].items():
            nim_str = str(nim)
            enriched_learning_paths[nim_str] = {
                'nama': mhs_map.get(nim_str, "Tidak Dikenal"),
                'nim': nim_str,
                'path': path
            }
            
        # Convert cluster profile (pandas DataFrame) to JSON-serializable format
        profile_df = results['cluster_profile'].reset_index()
        
        # Find semantic labels by scanning enriched groups
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
            'cluster_labels': {k: int(v) for k, v in results['cluster_labels'].items()}
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
