import faiss
import numpy as np

class VectorStore:

    def __init__(self, dim=384):
        self.index = faiss.IndexFlatL2(dim)
        self.text_chunks = []

    def add(self, embeddings, texts):

        self.index.add(np.array(embeddings))
        self.text_chunks.extend(texts)

    def search(self, query_embedding, k=5):

        if len(self.text_chunks) == 0:
            return []

        D, I = self.index.search(query_embedding, k)

        results = []

        for i in I[0]:
            if i < len(self.text_chunks):
                results.append(self.text_chunks[i])

        return results
