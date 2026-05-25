import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.retrieval import retrieval_engine

def compare_strategies(query: str):
    print(f"\n========================================================")
    print(f"QUERY: '{query}'")
    print(f"========================================================")
    
    # 1. BM25 (Sparse) Only
    print("\n[ STRATEGI 1: BM25 (Keyword Exact Match) ]")
    bm25_docs = retrieval_engine.bm25_search(query, top_k=2)
    for i, doc in enumerate(bm25_docs):
        print(f"{i+1}. {doc['title']} (Score: {doc['score']:.4f})")
        
    # 2. Dense (Vector/Semantic) Only
    print("\n[ STRATEGI 2: DENSE (Semantic Vector Search) ]")
    dense_docs = retrieval_engine.semantic_search(query, top_k=2)
    for i, doc in enumerate(dense_docs):
        print(f"{i+1}. {doc['title']} (Score: {doc['score']:.4f})")
        
    # 3. Hybrid (Dense + BM25)
    print("\n[ STRATEGI 3: HYBRID SEARCH (Kombinasi) ]")
    hybrid_docs = retrieval_engine.hybrid_search(query, top_k=2)
    for i, doc in enumerate(hybrid_docs):
        print(f"{i+1}. {doc['title']} (Score: {doc['hybrid_score']:.4f})")
        
    print("\nKesimpulan: Hybrid Search menggabungkan keunggulan BM25 (penemuan keyword langka/nama obat spesifik) dengan pemahaman semantik Dense Vector.\n")

if __name__ == "__main__":
    # Test case 1: Query medis umum (Semantic Dense biasanya bagus di sini)
    compare_strategies("Bagaimana cara menurunkan tekanan darah tinggi?")
    
    # Test case 2: Query dengan nama obat spesifik (BM25 biasanya unggul di sini karena keyword exact match)
    compare_strategies("Berapa batas maksimal paracetamol per hari?")
