# app/knowledge_graph.py

# Prerequisite mapping for Materi
# Key is the Materi, Value is a list of prerequisite Materi
PREREQUISITE_GRAPH = {
    "Penjadwalan CPU": ["Manajemen Proses"],
    "Manajemen Memori": ["Manajemen Proses"],
    "I/O Management": ["Manajemen Proses"],
    "Virtual Memory": ["Manajemen Memori"],
    "File System": ["I/O Management"]
}

def get_prerequisites(materi: str) -> list:
    """Mengembalikan daftar materi prasyarat untuk materi tertentu."""
    return PREREQUISITE_GRAPH.get(materi, [])
