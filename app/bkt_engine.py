# app/bkt_engine.py

from dataclasses import dataclass, field
from typing import List, Dict

try:
    from knowledge_graph import get_prerequisites
except ImportError:
    from app.knowledge_graph import get_prerequisites

@dataclass
class BKTParams:
    """Parameter BKT per materi/submateri."""
    p_l0: float = 0.20   # Pengetahuan awal (prior knowledge)
    p_t:  float = 0.15   # Transisi / tingkat pembelajaran (learn rate)
    p_g:  float = 0.20   # Probabilitas menebak (guess probability)
    p_s:  float = 0.10   # Probabilitas kesalahan (slip probability)

@dataclass
class BKTState:
    """State BKT untuk satu mahasiswa pada satu materi."""
    materi: str
    p_ln: float          # P(Ln) saat ini
    n_obs: int = 0       # Jumlah observasi

class BKTEngine:
    """
    Engine BKT untuk melacak penguasaan materi mahasiswa.
    
    Setiap materi memiliki parameter BKT independen.
    State per mahasiswa disimpan dalam dictionary.
    """
    
    MASTERY_THRESHOLD = 0.75  # Ambang batas "sudah dikuasai"
    
    def __init__(self, params_per_materi: Dict[str, BKTParams] = None):
        """
        params_per_materi: dict {nama_materi: BKTParams}
        Jika None, pakai default params untuk semua materi.
        """
        self.params = params_per_materi or {}
        # {nim: {materi: BKTState}}
        self.student_states: Dict[str, Dict[str, BKTState]] = {}
    
    def _get_params(self, materi: str) -> BKTParams:
        return self.params.get(materi, BKTParams())
    
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
    
    def update(self, nim: str, materi: str, is_correct: int) -> float:
        """
        Update P(Ln) berdasarkan satu observasi jawaban.
        
        Args:
            nim: NIM mahasiswa
            materi: Nama materi/submateri
            is_correct: 1 jika benar, 0 jika salah
        
        Returns:
            P(Ln) yang sudah diupdate
        """
        state = self._get_state(nim, materi)
        p = self._get_params(materi)
        
        p_ln = state.p_ln
        
        # Langkah 1: Update posterior berdasarkan observasi
        if is_correct == 1:
            numerator = p_ln * (1 - p.p_s)
            denominator = numerator + (1 - p_ln) * p.p_g
        else:
            numerator = p_ln * p.p_s
            denominator = numerator + (1 - p_ln) * (1 - p.p_g)
        
        p_ln_given_obs = numerator / denominator if denominator > 0 else p_ln
        
        # Langkah 2: Update transisi (probabilitas belajar setelah observasi)
        p_ln_next = p_ln_given_obs + (1 - p_ln_given_obs) * p.p_t
        
        # Simpan state yang baru
        state.p_ln = p_ln_next
        state.n_obs += 1
        
        return p_ln_next
    
    def process_log(self, log_df):
        """
        Proses seluruh log jawaban mahasiswa (DataFrame).
        Kolom yang dibutuhkan: NIM, Materi, Skor_Biner
        (join kuis_struktur untuk mendapatkan Materi)
        """
        for _, row in log_df.iterrows():
            self.update(row['NIM'], row['Materi'], row['Skor_Biner'])
    
    def get_mastery_vector(self, nim: str) -> Dict[str, float]:
        """
        Mengembalikan vektor penguasaan {materi: P(Ln)} untuk satu mahasiswa.
        Ini yang akan menjadi vektor fitur (feature vector) untuk K-Means.
        """
        nim = str(nim)
        if nim not in self.student_states:
            return {}
        return {
            materi: state.p_ln
            for materi, state in self.student_states[nim].items()
        }
    
    def get_learning_path(self, nim: str, all_materi: List[str]) -> List[Dict]:
        """
        Menghasilkan Learning Path personal berdasarkan P(Ln).
        Urutan: Materi dengan P(Ln) TERENDAH diprioritaskan, namun mempertimbangkan prasyarat.
        
        Mengembalikan:
            List of dict: [{'materi': ..., 'p_ln': ..., 'status': ..., 'rekomendasi_backtrack': ...}]
        """
        nim = str(nim)
        mastery = self.get_mastery_vector(nim)
        result = []
        
        for materi in all_materi:
            p_ln = mastery.get(materi, self._get_params(materi).p_l0)
            is_mastered = p_ln >= self.MASTERY_THRESHOLD
            
            if is_mastered:
                status = "Dikuasai"
            elif p_ln >= 0.50:
                status = "Perlu Penguatan"
            else:
                status = "Perlu Remedial !"
                
            # Cek prasyarat
            prereqs = get_prerequisites(materi)
            unmastered_prereqs = [
                p for p in prereqs 
                if mastery.get(p, self._get_params(p).p_l0) < self.MASTERY_THRESHOLD
            ]
            
            rekomendasi_backtrack = None
            if not is_mastered and unmastered_prereqs:
                rekomendasi_backtrack = f"Prasyarat belum dikuasai: {', '.join(unmastered_prereqs)}"
            
            result.append({
                'materi': materi,
                'p_ln': round(p_ln, 4),
                'status': status,
                'unmastered_prereqs_count': len(unmastered_prereqs),
                'rekomendasi_backtrack': rekomendasi_backtrack
            })
        
        # Sort: belum dikuasai dulu, lalu yang prasyaratnya sudah beres (count=0), lalu P(Ln) terkecil
        result.sort(key=lambda x: (
            x['p_ln'] >= self.MASTERY_THRESHOLD, 
            x['unmastered_prereqs_count'], 
            x['p_ln']
        ))
        
        for i, item in enumerate(result):
            item['prioritas'] = i + 1
            # Hapus key helper yang tidak perlu diekspos
            del item['unmastered_prereqs_count']
        
        return result