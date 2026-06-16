# app/bkt_engine.py

from dataclasses import dataclass, field
from typing import List, Dict

# Parameter BKT untuk prior, learn, guess, slip
@dataclass
class BKTParams:
    p_l0: float = 0.20   # Peluang awal pemahaman (Prior)
    p_t:  float = 0.15   # Peluang belajar (Transition)
    p_g:  float = 0.20   # Peluang menebak benar (Guess)
    p_s:  float = 0.10   # Peluang salah jawab ceroboh (Slip)

# State BKT per konsep untuk setiap mahasiswa
@dataclass
class BKTState:
    materi: str
    p_ln: float          
    n_obs: int = 0       

# Engine utama pelacakan pemahaman BKT
class BKTEngine:
    
    MASTERY_THRESHOLD = 0.75  
    
    # Inisialisasi engine BKT
    def __init__(self, params_per_materi: Dict[str, BKTParams] = None):
        self.params = params_per_materi or {}
        self.student_states: Dict[str, Dict[str, BKTState]] = {}
    
    # Ambil parameter BKT untuk materi tertentu
    def _get_params(self, materi: str) -> BKTParams:
        return self.params.get(materi, BKTParams())
    
    # Ambil atau buat state pemahaman mahasiswa per materi
    def _get_state(self, nim: str, materi: str) -> BKTState:
        nim = str(nim)
        if nim not in self.student_states:
            self.student_states[nim] = {}
        if materi not in self.student_states[nim]:
            p = self._get_params(materi)
            self.student_states[nim][materi] = BKTState(
                materi=materi, p_ln=p.p_l0
            )
        return self.student_states[nim][materi]
    
    # Update nilai peluang pemahaman P(Ln) setelah menjawab soal
    def update(self, nim: str, materi: str, is_correct: int) -> float:
        state = self._get_state(nim, materi)
        p = self._get_params(materi)
        
        p_ln = state.p_ln
        
        # 1. Update posterior berdasarkan hasil observasi (benar/salah)
        if is_correct == 1:
            numerator = p_ln * (1 - p.p_s)
            denominator = numerator + (1 - p_ln) * p.p_g
        else:
            numerator = p_ln * p.p_s
            denominator = numerator + (1 - p_ln) * (1 - p.p_g)
        
        p_ln_given_obs = numerator / denominator if denominator > 0 else p_ln
        
        # 2. Update transisi peluang belajar setelah latihan
        p_ln_next = p_ln_given_obs + (1 - p_ln_given_obs) * p.p_t
        
        state.p_ln = p_ln_next
        state.n_obs += 1
        
        return p_ln_next
    
    # Proses seluruh log jawaban dari dataset CSV
    def process_log(self, log_df):
        for _, row in log_df.iterrows():
            self.update(row['NIM'], row['Materi'], row['Skor_Biner'])
    
    # Ambil vektor penguasaan pemahaman seluruh materi untuk satu mahasiswa
    def get_mastery_vector(self, nim: str) -> Dict[str, float]:
        nim = str(nim)
        if nim not in self.student_states:
            return {}
        return {
            materi: state.p_ln
            for materi, state in self.student_states[nim].items()
        }
    
    # Rekomendasi urutan belajar (Learning Path) untuk satu mahasiswa
    def get_learning_path(self, nim: str, all_materi: List[str]) -> List[Dict]:
        nim = str(nim)
        mastery = self.get_mastery_vector(nim)
        result = []
        
        for materi in all_materi:
            p_ln = mastery.get(materi, self._get_params(materi).p_l0)
            
            if p_ln >= self.MASTERY_THRESHOLD:
                status = "Dikuasai ✓"
            elif p_ln >= 0.50:
                status = "Perlu Penguatan"
            else:
                status = "Perlu Remedial !"
            
            result.append({
                'materi': materi,
                'p_ln': round(p_ln, 4),
                'status': status
            })
        
        result.sort(key=lambda x: (x['p_ln'] >= self.MASTERY_THRESHOLD, x['p_ln']))
        
        for i, item in enumerate(result):
            item['prioritas'] = i + 1
        
        return result

# Blok eksekusi mandiri untuk demo BKT
if __name__ == "__main__":
    import os
    import pandas as pd
    
    app_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(app_dir)
    mahasiswa_csv = os.path.join(base_dir, "dataset", "mahasiswa.csv")
    kuis_csv = os.path.join(base_dir, "dataset", "kuis_struktur.csv")
    log_csv = os.path.join(base_dir, "dataset", "mahasiswa_log_jawaban.csv")
    
    print("\n" + "="*70)
    print("BAYESIAN KNOWLEDGE TRACING (BKT)")
    print("="*70)
    print("BKT melacak tingkat pemahaman konsep mahasiswa secara real-time.")
    
    df_kuis = pd.read_csv(kuis_csv)
    df_log = pd.read_csv(log_csv).merge(df_kuis[['ID_Soal', 'Materi']], on='ID_Soal')
    
    bkt = BKTEngine()
    
    target_nim = "2301015"
    target_materi = "Manajemen Proses"
    df_target_log = df_log[(df_log['NIM'].astype(str) == target_nim) & (df_log['Materi'] == target_materi)].copy()
    
    print(f"\n[TRACE] Pelacakan Pemahaman Mahasiswa {target_nim} pada Materi '{target_materi}':")
    print("-" * 80)
    print(f"{'Soal ID':<10} | {'Jawaban':<10} | {'Skor Biner':<12} | {'Prior P(Ln)':<15} | {'Updated P(Ln)':<15}")
    print("-" * 80)
    
    state = bkt._get_state(target_nim, target_materi)
    p_ln = state.p_ln
    
    for _, row in df_target_log.iterrows():
        soal_id = row['ID_Soal']
        skor = int(row['Skor_Biner'])
        jawaban_status = "Benar" if skor == 1 else "Salah"
        p_ln_updated = bkt.update(target_nim, target_materi, skor)
        print(f"{soal_id:<10} | {jawaban_status:<10} | {skor:<12} | {p_ln:<15.4f} | {p_ln_updated:<15.4f}")
        p_ln = p_ln_updated
        
    print("\nMemproses sisa log mahasiswa...")
    bkt.process_log(df_log)
    print("Selesai memproses.")
    
    print("\n[OUTPUT] Vektor Penguasaan Akhir (Mastery Vectors) Sampel:")
    samples = [("2301001", "Mahir"), ("2301015", "Cukup"), ("2301035", "Remedial")]
    materi_list = df_kuis['Materi'].unique().tolist()
    
    for nim, profile in samples:
        vector = bkt.get_mastery_vector(nim)
        formatted_vec = {m: round(vector.get(m, 0.20), 3) for m in materi_list}
        print(f"\n NIM: {nim} (Profil: {profile})")
        for m, score in formatted_vec.items():
            status = "Dikuasai" if score >= 0.75 else ("Perlu Penguatan" if score >= 0.50 else "Remedial")
            print(f"  - {m:<20} : P(L) = {score:<6.3f} | Status: {status}")
