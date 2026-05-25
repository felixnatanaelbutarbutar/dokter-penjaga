import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.retrieval import retrieval_engine
from core.llm import llm_engine
from config import get_settings

cfg = get_settings()

def run_factual_eval():
    print("Memulai Evaluasi Faktual (LLM-as-Judge)...")
    
    questions = [
        "Apa tekanan darah target untuk pasien hipertensi dengan diabetes?",
        "Apakah aman memberikan paracetamol 6 gram per hari untuk orang dewasa?",
        "Jelaskan cara mendiagnosis diabetes tipe 2 menurut panduan terbaru."
    ]
    
    results = {
        "total_questions": len(questions),
        "factual_count": 0,
        "details": []
    }
    
    for q in questions:
        print(f"\nEvaluating: '{q}'")
        # 1. Retrieve context
        top_docs = retrieval_engine.hybrid_search(q, top_k=3)
        context_texts = "\n\n".join([f"[{doc['title']}] {doc['text']}" for doc in top_docs])
        
        # 2. Generate answer
        answer = llm_engine.generate_response(q, top_docs, has_conflict=False, conflict_reason="")
        print(f"Generated Answer: {answer[:100]}...")
        
        # 3. LLM as Judge
        judge_prompt = f"""
Anda adalah penilai faktual (Factual Judge) independen.
Diberikan KONTEKS medis yang asli dan JAWABAN dari sistem AI.
Tugas Anda: Periksa apakah JAWABAN sepenuhnya didukung oleh KONTEKS (tidak ada informasi/dosis yang dikarang sendiri di luar konteks).

KONTEKS ASLI:
{context_texts}

JAWABAN AI:
{answer}

Berikan penilaian akhir Anda pada baris pertama saja, dengan menulis "SCORE: 1" jika faktual (didukung konteks atau menolak menjawab karena kurang info), atau "SCORE: 0" jika berhalusinasi atau memberikan informasi di luar konteks. Kemudian Anda boleh menjelaskan alasannya di baris berikutnya.
"""
        try:
            judge_response = llm_engine.client.messages.create(
                model=cfg.llm_model,
                max_tokens=256,
                messages=[{"role": "user", "content": judge_prompt}]
            )
            judge_text = judge_response.content[0].text.strip()
            
            is_factual = "SCORE: 1" in judge_text.upper()
            if is_factual:
                results["factual_count"] += 1
                
            results["details"].append({
                "question": q,
                "answer": answer,
                "judge_score": 1 if is_factual else 0,
                "judge_reason": judge_text
            })
            print(f"Judge Score: {'1 (Faktual)' if is_factual else '0 (Halusinasi)'}")
        except Exception as e:
            print(f"Error calling LLM Judge: {e}")
            results["details"].append({
                "question": q,
                "error": str(e)
            })

    if results["total_questions"] > 0:
        accuracy = results["factual_count"] / results["total_questions"]
    else:
        accuracy = 0
        
    print("=" * 40)
    print("      FACTUAL EVALUATION RESULTS")
    print("=" * 40)
    print(f"Total Questions : {results['total_questions']}")
    print(f"Factual Answers : {results['factual_count']}")
    print(f"Factual Accuracy: {accuracy * 100:.2f}% (Target >= 75%)")
    print("=" * 40)
    
    output_path = os.path.join(PROJECT_ROOT, "eval", "factual_accuracy_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
        
    print(f"Detailed results saved to {output_path}")

if __name__ == "__main__":
    run_factual_eval()
