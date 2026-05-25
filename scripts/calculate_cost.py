import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from anthropic import Anthropic
from config import get_settings
from core.retrieval import retrieval_engine
from core.llm import llm_engine

def calculate_cost_per_query(query: str):
    print(f"\nMenghitung Biaya Kueri Medis (Simulasi Live)")
    print(f"Query: '{query}'")
    print("-" * 50)
    
    cfg = get_settings()
    client = Anthropic(api_key=cfg.anthropic_api_key)
    
    # 1. Ambil Dokumen Referensi (Mewakili Payload Konteks RAG)
    docs = retrieval_engine.hybrid_search(query, top_k=3)
    
    # 2. Bangun Prompt Persis Seperti Produksi
    system_prompt = llm_engine._build_system_prompt()
    user_prompt = llm_engine._build_context_prompt(query, docs, False, "")
    
    print("Memanggil Anthropic API untuk mengekstrak metadata token usage...")
    
    # 3. Panggil API untuk mendapatkan Usage Data
    response = client.messages.create(
        model=cfg.llm_model,
        max_tokens=cfg.llm_max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    
    # Harga Claude 3.5 Sonnet (estimasi): 
    # Input: $3 per 1 Juta token ($0.000003 per token)
    # Output: $15 per 1 Juta token ($0.000015 per token)
    PRICE_PER_INPUT_TOKEN = 3 / 1_000_000
    PRICE_PER_OUTPUT_TOKEN = 15 / 1_000_000
    
    cost_input = input_tokens * PRICE_PER_INPUT_TOKEN
    cost_output = output_tokens * PRICE_PER_OUTPUT_TOKEN
    total_cost = cost_input + cost_output
    
    print(f"\n[ STATISTIK TOKEN ]")
    print(f"- Input Tokens (Termasuk konteks Qdrant): {input_tokens:,}")
    print(f"- Output Tokens (Jawaban LLM)           : {output_tokens:,}")
    
    print(f"\n[ KALKULASI BIAYA (Claude 3.5 Sonnet) ]")
    print(f"- Biaya Input : ${cost_input:.5f}")
    print(f"- Biaya Output: ${cost_output:.5f}")
    print(f"- TOTAL BIAYA 1 KUERI: ${total_cost:.5f}")
    
    # Estimasi 1000 Kueri
    cost_1000 = total_cost * 1000
    print(f"\n=> ESTIMASI BIAYA UNTUK 1000 KUERI: ${cost_1000:.2f} (Sekitar Rp {cost_1000 * 15500:,.0f})\n")

if __name__ == "__main__":
    calculate_cost_per_query("Jelaskan gejala diabetes dan bagaimana cara menanganinya menurut panduan medis terbaru")
