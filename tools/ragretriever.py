import os
import re
import math
from typing import List, Dict, Tuple

# A simple list of English stop words to filter out noise
STOP_WORDS = {
    'the', 'is', 'at', 'which', 'on', 'for', 'of', 'and', 'a', 'to', 'in', 'it', 
    'is', 'what', 'how', 'why', 'where', 'can', 'your', 'my', 'about', 'with', 
    'an', 'this', 'that', 'these', 'those', 'are', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'but', 'if', 'or', 'because',
    'as', 'until', 'while', 'by', 'about', 'into', 'through', 'during', 'before',
    'after', 'above', 'below', 'from', 'up', 'down', 'out', 'off', 'over', 'under'
}

def clean_and_tokenize(text: str) -> List[str]:
    """Cleans text by removing punctuation, lowercasing, and filtering out stop words."""
    if not text:
        return []
    # Lowercase and replace non-alphanumeric characters with spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    # Tokenize by whitespace
    tokens = cleaned.split()
    # Filter out stop words
    return [token for token in tokens if token not in STOP_WORDS]

class TFIDFRetriever:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.chunks: List[str] = []
        self.chunk_tokens: List[List[str]] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.chunk_vectors: List[Dict[str, float]] = []
        self.load_and_index()

    def load_and_index(self):
        """Loads knowledge base and indexes chunks using TF-IDF."""
        if not os.path.exists(self.file_path):
            # Fallback to an empty index if knowledge base is missing
            return

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return

        # Paragraph chunking (split by double newlines or similar boundaries)
        raw_chunks = re.split(r'\n\s*\n', content)
        
        # Clean chunks: filter out empty paragraphs and header titles
        self.chunks = []
        for chunk in raw_chunks:
            chunk_stripped = chunk.strip()
            # Ignore divider headers (e.g. === CROPS ... ===)
            if chunk_stripped and not chunk_stripped.startswith('==='):
                self.chunks.append(chunk_stripped)

        if not self.chunks:
            return

        # Tokenize all chunks
        self.chunk_tokens = [clean_and_tokenize(chunk) for chunk in self.chunks]
        
        # Compute Document Frequency (DF) for each unique term
        df: Dict[str, int] = {}
        for tokens in self.chunk_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1

        num_chunks = len(self.chunks)
        # Compute Inverse Document Frequency (IDF) for each term
        # Using smooth IDF formula: idf = log(1 + N / (1 + df))
        for term, term_df in df.items():
            self.idf[term] = math.log(1.0 + (float(num_chunks) / (1.0 + float(term_df))))

        # Build TF-IDF vectors for all chunks
        self.chunk_vectors = []
        for tokens in self.chunk_tokens:
            if not tokens:
                self.chunk_vectors.append({})
                continue
                
            # Term Frequency (TF) = count / total_tokens_in_chunk
            tf: Dict[str, float] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0.0) + 1.0
            
            total_tokens = len(tokens)
            vector: Dict[str, float] = {}
            for term, count in tf.items():
                term_tf = count / total_tokens
                vector[term] = term_tf * self.idf.get(term, 0.0)
            self.chunk_vectors.append(vector)

    def retrieve(self, query: str, top_k: int = 3) -> List[str]:
        """Retrieves top K chunks matching the query using cosine similarity."""
        if not self.chunks or not query:
            return []

        query_tokens = clean_and_tokenize(query)
        if not query_tokens:
            return self.chunks[:top_k]  # Return first K if query tokenization yields nothing

        # Compute TF-IDF vector for the query
        query_tf: Dict[str, float] = {}
        for token in query_tokens:
            query_tf[token] = query_tf.get(token, 0.0) + 1.0
            
        total_query_tokens = len(query_tokens)
        query_vector: Dict[str, float] = {}
        for term, count in query_tf.items():
            if term in self.idf:  # Only terms in vocabulary matter
                term_tf = count / total_query_tokens
                query_vector[term] = term_tf * self.idf[term]

        if not query_vector:
            return self.chunks[:top_k]

        # Calculate cosine similarities
        similarities: List[Tuple[float, int]] = []
        
        # Norm of query vector: sqrt(sum(w^2))
        query_norm = math.sqrt(sum(val ** 2 for val in query_vector.values()))
        if query_norm == 0:
            return self.chunks[:top_k]

        for idx, doc_vector in enumerate(self.chunk_vectors):
            if not doc_vector:
                similarities.append((0.0, idx))
                continue
                
            # Dot product: sum(A_i * B_i)
            dot_product = 0.0
            for term, q_val in query_vector.items():
                if term in doc_vector:
                    dot_product += q_val * doc_vector[term]
            
            # Norm of document vector
            doc_norm = math.sqrt(sum(val ** 2 for val in doc_vector.values()))
            
            if doc_norm > 0:
                similarity = dot_product / (query_norm * doc_norm)
            else:
                similarity = 0.0
                
            similarities.append((similarity, idx))

        # Sort similarities in descending order
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return the actual top K text chunks
        top_indices = [idx for sim, idx in similarities[:top_k]]
        return [self.chunks[idx] for idx in top_indices]

# Singleton instance of RAG retriever using default data path
KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "data", 
    "farming_knowledge.txt"
)

retriever = TFIDFRetriever(KNOWLEDGE_BASE_PATH)

def retrieve_relevant_chunks(query: str, top_k: int = 3) -> List[str]:
    """Global convenience function to retrieve relevant agricultural knowledge chunks."""
    return retriever.retrieve(query, top_k=top_k)
