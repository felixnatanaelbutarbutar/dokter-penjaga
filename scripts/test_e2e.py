import asyncio
from api.routes.chat import ask_question
from api.schemas import AskRequest
import json

async def run_test():
    req = AskRequest(query="Apa pedoman terbaru untuk tekanan darah tinggi?", session_id="test-e2e")
    res = await ask_question(req)
    
    print("\n--- RESPONSE ---")
    print(res.answer)
    print("\n--- SOURCES ---")
    for s in res.sources:
        print(f"- {s.title} ({s.year})")

if __name__ == "__main__":
    asyncio.run(run_test())
