import faiss
import numpy as np

class VectorStore:

    def __init__(self, dim=384):
        self.index = faiss.IndexFlatL2(dim)
        self.text_chunks = []

    def add(self, embeddings, texts):

        self.index.add(np.array(embeddings))
        self.text_chunks.extend(texts)

    def search(self, query_embedding, k=3):

        D, I = self.index.search(
            np.array([query_embedding]), k
        )

        return [self.text_chunks[i] for i in I[0]]
