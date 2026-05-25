import json
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from core.triage import triage_classifier

def run_triage_eval():
    print("Memulai Evaluasi Triage Classifier...")
    
    # Dataset Triage (Ground Truth)
    # 1: Emergency, 0: Non-Emergency
    dataset = [
        {"text": "Saya merasa nyeri dada kiri yang menjalar ke lengan", "is_emergency": 1},
        {"text": "Anak saya pingsan dan tidak sadarkan diri", "is_emergency": 1},
        {"text": "Ada darah segar yang keluar banyak setelah kecelakaan", "is_emergency": 1},
        {"text": "Teman saya kejang-kejang di lantai", "is_emergency": 1},
        {"text": "Bapak saya tiba-tiba lumpuh sebelah badan dan bicara pelo", "is_emergency": 1},
        {"text": "Seseorang tersedak dan wajahnya mulai membiru", "is_emergency": 1},
        {"text": "Adik saya minum obat serangga 1 botol", "is_emergency": 1},
        {"text": "Napas saya sesak banget sampai mau mati rasanya", "is_emergency": 1},
        {"text": "Jantung berdebar sangat kencang dan pandangan gelap", "is_emergency": 1},
        {"text": "Luka sayatan pisau terus mengeluarkan darah", "is_emergency": 1},
        
        {"text": "Apa obat untuk demam ringan pada balita?", "is_emergency": 0},
        {"text": "Tolong jelaskan apa itu diabetes melitus", "is_emergency": 0},
        {"text": "Apakah paracetamol aman untuk ibu hamil?", "is_emergency": 0},
        {"text": "Gigi saya ngilu kalau minum air dingin", "is_emergency": 0},
        {"text": "Cara mencegah penyakit jantung bawaan", "is_emergency": 0},
        {"text": "Saya pilek dan batuk berdahak sudah 2 hari", "is_emergency": 0},
        {"text": "Berapa tekanan darah normal untuk lansia?", "is_emergency": 0},
        {"text": "Kepala saya pusing setelah kehujanan kemarin", "is_emergency": 0},
        {"text": "Di mana saya bisa membeli vitamin C?", "is_emergency": 0},
        {"text": "Kulit saya agak gatal dan kemerahan", "is_emergency": 0},
    ]
    
    tp = 0  # True Positive
    fp = 0  # False Positive
    tn = 0  # True Negative
    fn = 0  # False Negative
    
    results = []
    
    for item in dataset:
        text = item["text"]
        expected = item["is_emergency"] == 1
        
        is_emergency, confidence, reason = triage_classifier.classify(text)
        
        if is_emergency and expected:
            tp += 1
        elif is_emergency and not expected:
            fp += 1
        elif not is_emergency and not expected:
            tn += 1
        elif not is_emergency and expected:
            fn += 1
            
        results.append({
            "text": text,
            "expected": expected,
            "predicted": is_emergency,
            "reason": reason
        })
        
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print("=" * 40)
    print("      TRIAGE EVALUATION RESULTS")
    print("=" * 40)
    print(f"Total Test Cases : {len(dataset)}")
    print(f"True Positives   : {tp}")
    print(f"True Negatives   : {tn}")
    print(f"False Positives  : {fp}")
    print(f"False Negatives  : {fn}")
    print("-" * 40)
    print(f"Precision        : {precision:.4f}")
    print(f"Recall           : {recall:.4f}")
    print(f"F1 Score         : {f1_score:.4f} (Target >= 0.90)")
    print("=" * 40)
    
    output_data = {
        "metrics": {
            "total": len(dataset),
            "tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        },
        "details": results
    }
    
    output_path = os.path.join(PROJECT_ROOT, "eval", "triage_eval_results.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Detailed results saved to {output_path}")

if __name__ == "__main__":
    run_triage_eval()
