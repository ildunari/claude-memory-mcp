"""
Utilities for generating and managing embeddings.
"""

import os
from typing import Dict, List, Optional, Union

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer


class EmbeddingManager:
    """
    Manages the generation and caching of text embeddings.
    
    This class provides utilities for generating, storing, and retrieving
    embeddings for text content. It uses the sentence-transformers library
    for embedding generation and supports caching for improved performance.
    """
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None,
        dimensions: int = 384
    ) -> None:
        """
        Initialize the embedding manager.
        
        Args:
            model_name: Name of the sentence transformer model
            cache_dir: Directory for caching embeddings
            dimensions: Embedding dimensions
        """
        self.model_name = model_name
        self.dimensions = dimensions
        self.cache_dir = cache_dir
        self.model = None
        
        # Cache for embeddings
        self.embedding_cache = {}
        
        logger.info(f"Initializing embedding manager with model {model_name}")
    
    async def initialize(self) -> None:
        """Initialize the embedding model."""
        logger.info(f"Loading embedding model: {self.model_name}")
        
        # Create cache directory if specified
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load the model
        self.model = SentenceTransformer(self.model_name)
        
        # Verify dimensions
        sample_text = "Sample text for dimension verification"
        sample_embedding = self.model.encode(sample_text)
        actual_dimensions = len(sample_embedding)
        
        if actual_dimensions != self.dimensions:
            logger.warning(
                f"Model dimensions ({actual_dimensions}) don't match expected dimensions ({self.dimensions})"
            )
            self.dimensions = actual_dimensions
        
        logger.info(f"Embedding model loaded with dimensions: {self.dimensions}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text, using cache if available.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        if not self.model:
            await self.initialize()
        
        # Check cache
        if text in self.embedding_cache:
            return self.embedding_cache[text]
        
        # Generate embedding
        embedding = self.model.encode(text)
        
        # Convert to list of floats for JSON serialization
        embedding_list = embedding.tolist()
        
        # Cache the embedding
        self.embedding_cache[text] = embedding_list
        
        return embedding_list
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts, using batch processing.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self.model:
            await self.initialize()
        
        # Filter out texts that are not in cache
        texts_to_embed = []
        cached_indices = {}
        
        for i, text in enumerate(texts):
            if text in self.embedding_cache:
                cached_indices[i] = text
            else:
                texts_to_embed.append(text)
        
        # Generate embeddings for new texts
        if texts_to_embed:
            new_embeddings = self.model.encode(texts_to_embed)
            
            # Update cache with new embeddings
            for i, text in enumerate(texts_to_embed):
                embedding_list = new_embeddings[i].tolist()
                self.embedding_cache[text] = embedding_list
        
        # Combine cached and new embeddings
        result = []
        cached_count = 0
        new_count = 0
        
        for i in range(len(texts)):
            if i in cached_indices:
                # Use cached embedding
                result.append(self.embedding_cache[cached_indices[i]])
                cached_count += 1
            else:
                # Use new embedding
                text = texts[i - cached_count]
                result.append(self.embedding_cache[text])
                new_count += 1
        
        return result
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity (0.0-1.0)
        """
        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Calculate cosine similarity
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(np.dot(vec1, vec2) / (norm1 * norm2))
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: Dict[str, List[float]],
        top_k: int = 5,
        threshold: float = 0.0
    ) -> List[Dict[str, Union[str, float]]]:
        """
        Find the most similar embeddings to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: Dictionary of candidate IDs to embeddings
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of matches with IDs and similarity scores
        """
        results = []
        
        for candidate_id, candidate_embedding in candidate_embeddings.items():
            similarity = self.cosine_similarity(query_embedding, candidate_embedding)
            
            if similarity >= threshold:
                results.append({
                    "id": candidate_id,
                    "similarity": similarity
                })
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Limit to top_k results
        return results[:top_k]
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.embedding_cache = {}
        logger.info("Embedding cache cleared")
