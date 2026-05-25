import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
import os

from config import get_settings
from core.temporal import temporal_boost
from data.ingest import get_qdrant_client, get_embedder, _simple_tokenize

cfg = get_settings()

class RetrievalEngine:
    def __init__(self):
        self.qdrant = get_qdrant_client(cfg.qdrant_host, cfg.qdrant_port, cfg.qdrant_api_key)
        self.embedder = get_embedder(cfg.embedding_model)
        
        # Load BM25 Index
        bm25_path = Path(cfg.bm25_index_path)
        if bm25_path.exists():
            with open(bm25_path, "rb") as f:
                payload = pickle.load(f)
                self.bm25 = payload["bm25"]
                self.chunks_meta = payload["chunks_meta"]
        else:
            self.bm25 = None
            self.chunks_meta = []
            print(f"Warning: BM25 index not found at {bm25_path}")

    def semantic_search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Qdrant Dense Vector Search."""
        query_vector = self.embedder.encode(query, convert_to_numpy=True, normalize_embeddings=True).tolist()
        
        try:
            results = self.qdrant.query_points(
                collection_name=cfg.qdrant_collection,
                query=query_vector,
                limit=top_k
            )
            
            # Format results
            docs = []
            for res in results.points:
                payload = res.payload or {}
                docs.append({
                    "id": res.id,
                    "score": res.score, # Cosine similarity (0 to 1 ideally)
                    "text": payload.get("text", ""),
                    "title": payload.get("title", ""),
                    "year": payload.get("year", 0),
                    "source": payload.get("source", ""),
                    "url": payload.get("url", "")
                })
            return docs
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []

    def bm25_search(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """Sparse Keyword Search using BM25Okapi."""
        if not self.bm25:
            return []
            
        tokenized_query = _simple_tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores (Min-Max normalization to 0-1)
        if len(scores) > 0 and max(scores) > 0:
            max_score = max(scores)
            min_score = min(scores)
            if max_score != min_score:
                norm_scores = (scores - min_score) / (max_score - min_score)
            else:
                norm_scores = scores / max_score
        else:
            norm_scores = scores
            
        # Get top K indices
        top_indices = np.argsort(norm_scores)[::-1][:top_k]
        
        docs = []
        for idx in top_indices:
            score = float(norm_scores[idx])
            if score == 0.0:
                continue # Skip 0 scores
                
            meta = self.chunks_meta[idx]
            doc_meta = meta["metadata"]
            docs.append({
                "id": meta["chunk_id"],
                "score": score,
                "text": meta["text"],
                "title": doc_meta.get("title", ""),
                "year": doc_meta.get("year", 0),
                "source": doc_meta.get("source", ""),
                "url": doc_meta.get("url", "")
            })
            
        return docs

    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Combines Semantic and BM25 scores with Temporal Boost.
        score_final = α · score_semantic + (1−α) · score_BM25 + λ · f(year)
        """
        semantic_docs = self.semantic_search(query, top_k=top_k*2)
        bm25_docs = self.bm25_search(query, top_k=top_k*2)
        
        # Combine results into a dictionary keyed by chunk ID
        combined: Dict[str, Dict[str, Any]] = {}
        
        for doc in semantic_docs:
            combined[doc["id"]] = doc
            combined[doc["id"]]["semantic_score"] = doc["score"]
            combined[doc["id"]]["bm25_score"] = 0.0
            
        for doc in bm25_docs:
            if doc["id"] not in combined:
                combined[doc["id"]] = doc
                combined[doc["id"]]["semantic_score"] = 0.0
            combined[doc["id"]]["bm25_score"] = doc["score"]
            
        # Calculate Hybrid Score
        alpha = cfg.alpha_hybrid
        lambda_t = cfg.lambda_temporal
        
        for doc_id, doc in combined.items():
            sem = doc.get("semantic_score", 0.0)
            bm25 = doc.get("bm25_score", 0.0)
            t_boost = temporal_boost(doc.get("year", 0))
            
            final_score = (alpha * sem) + ((1 - alpha) * bm25) + (lambda_t * t_boost)
            doc["hybrid_score"] = final_score
            
        # Sort by hybrid score
        sorted_docs = sorted(combined.values(), key=lambda x: x["hybrid_score"], reverse=True)
        
        return sorted_docs[:top_k]

retrieval_engine = RetrievalEngine()
