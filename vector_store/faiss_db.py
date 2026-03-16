import faiss
import numpy as np
import pickle
import os
from rank_bm25 import BM25Okapi

class VectorStore:

    def __init__(self, dim=384, index_path="faiss_index.bin", meta_path="meta.pkl"):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path
        
        self.index = None
        self.text_chunks = []      # Will now store dicts: {"text": chunk, "source": source_id}
        self.bm25 = None
        
        self.load()

    def add(self, embeddings, texts_with_metadata):
        """
        texts_with_metadata: list of dicts [{"text": "...", "source": "..."}]
        """
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.dim)
            
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.text_chunks.extend(texts_with_metadata)
        
        self._update_bm25()
        self.save()

    def _update_bm25(self):
        if len(self.text_chunks) > 0:
            tokenized_corpus = [doc["text"].lower().split() for doc in self.text_chunks]
            self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query, query_embedding, k=5):
        if len(self.text_chunks) == 0 or self.index is None:
            return []

        # Vector Search (semantic)
        D, I = self.index.search(np.array(query_embedding, dtype=np.float32), k=k*2)
        vector_results_indices = I[0].tolist()

        # BM25 Search (keyword)
        tokenized_query = query.lower().split()
        if self.bm25:
            bm25_scores = self.bm25.get_scores(tokenized_query)
            bm25_top_indices = np.argsort(bm25_scores)[::-1][:k*2].tolist()
        else:
            bm25_top_indices = []

        # Hybrid Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        for rank, idx in enumerate(vector_results_indices):
            if idx != -1 and idx < len(self.text_chunks):
                rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (60 + rank)
                
        for rank, idx in enumerate(bm25_top_indices):
            if idx != -1 and idx < len(self.text_chunks):
                rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (60 + rank)
                
        # Sort by RRF score
        sorted_indices = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        top_k_indices = sorted_indices[:k]
        
        results = [self.text_chunks[i] for i in top_k_indices]
        return results

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.text_chunks, f)

    def load(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.text_chunks = pickle.load(f)
            self._update_bm25()
        else:
            self.index = faiss.IndexFlatL2(self.dim)
            self.text_chunks = []
