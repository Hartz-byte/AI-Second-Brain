import os
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

class VectorStore:

    def __init__(self, dim=384):
        self.dim = dim
        self.index_name = "ai-second-brain"
        
        # Initialize Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY environment variable is missing!")
            
        self.pc = Pinecone(api_key=api_key)
        
        # Check if index exists, map it to Serverless instance if new
        if self.index_name not in [index.name for index in self.pc.list_indexes()]:
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            
        self.index = self.pc.Index(self.index_name)

    def add(self, embeddings, texts_with_metadata):
        """
        texts_with_metadata: list of dicts [{"text": "...", "source": "..."}]
        """
        
        vectors = []
        for i, (embedding, meta) in enumerate(zip(embeddings, texts_with_metadata)):
            # Pinecone needs unique string IDs for every chunk
            # By standard, we hash the text or use an increment, here we use random uuid for simplicity
            import uuid
            chunk_id = str(uuid.uuid4())
            
            # Pinecone accepts: (id, vector, metadata)
            vectors.append({
                "id": chunk_id,
                "values": embedding.tolist(),
                "metadata": {
                    "text": meta["text"], 
                    "source": meta["source"]
                }
            })
            
        # Batch upload to Pinecone
        self.index.upsert(vectors=vectors)


    def search(self, query, query_embedding, k=5):
        # We query the exact same index using vectors
        response = self.index.query(
            vector=query_embedding[0].tolist(),
            top_k=k,
            include_metadata=True
        )

        results = []
        for match in response.matches:
            # Reconstruct the metadata dict formatted exactly how the retriever likes it
            results.append({
                "text": match.metadata["text"],
                "source": match.metadata["source"]
            })

        return results
