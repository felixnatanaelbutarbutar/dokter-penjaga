import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.retrieval import retrieval_engine

def run_retrieval_eval():
    print("Memulai Evaluasi Retrieval (Recall@5)...")
    
    # Ground truth: {query: expected_document_title_substring}
    ground_truth = [
        {
            "query": "Apa pedoman terbaru untuk tekanan darah tinggi menurut WHO?",
            "expected_title": "Hypertension"
        },
        {
            "query": "Berapa dosis maksimal paracetamol sehari?",
            "expected_title": "Paracetamol"
        },
        {
            "query": "Bagaimana klasifikasi diabetes mellitus?",
            "expected_title": "Diabetes"
        },
        {
            "query": "Pengobatan farmakologis hipertensi pada orang dewasa",
            "expected_title": "Hypertension"
        },
        {
            "query": "Panduan diagnosis diabetes tipe 2",
            "expected_title": "Diabetes"
        }
    ]
    
    results = {
        "total_queries": len(ground_truth),
        "successful_retrievals": 0,
        "details": []
    }
    
    for item in ground_truth:
        query = item["query"]
        expected_substring = item["expected_title"]
        
        # Lakukan pencarian hybrid (top_k = 5)
        top_docs = retrieval_engine.hybrid_search(query, top_k=5)
        
        # Cek apakah expected document ada di hasil top 5
        found = False
        retrieved_titles = []
        for doc in top_docs:
            title = doc.get("title", "")
            retrieved_titles.append(title)
            if expected_substring.lower() in title.lower():
                found = True
                
        if found:
            results["successful_retrievals"] += 1
            
        results["details"].append({
            "query": query,
            "expected_substring": expected_substring,
            "retrieved_titles": retrieved_titles,
            "recall_at_5": 1 if found else 0
        })
        
    recall_score = results["successful_retrievals"] / results["total_queries"]
    results["recall_at_5"] = recall_score
    
    print("=" * 40)
    print("      RETRIEVAL EVALUATION RESULTS")
    print("=" * 40)
    print(f"Total Queries : {results['total_queries']}")
    print(f"Successful    : {results['successful_retrievals']}")
    print(f"Recall@5      : {recall_score * 100:.2f}% (Target >= 80%)")
    print("=" * 40)
    
    output_path = os.path.join(PROJECT_ROOT, "eval", "retrieval_eval_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Detailed results saved to {output_path}")

if __name__ == "__main__":
    run_retrieval_eval()
