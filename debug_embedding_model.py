#!/usr/bin/env python3
"""
Test if SentenceTransformer initialization is the bottleneck
"""

import time
from sentence_transformers import SentenceTransformer

def test_embedding_model():
    """Test embedding model initialization time"""
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"🔍 Testing SentenceTransformer initialization: {model_name}")
    
    start_time = time.time()
    try:
        model = SentenceTransformer(model_name)
        elapsed = time.time() - start_time
        print(f"✅ SentenceTransformer loaded in {elapsed:.2f}s")
        
        # Test encoding
        start_encode = time.time()
        embedding = model.encode("test text")
        encode_elapsed = time.time() - start_encode
        print(f"✅ Test encoding completed in {encode_elapsed:.3f}s")
        print(f"📊 Embedding dimensions: {len(embedding)}")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ SentenceTransformer failed in {elapsed:.2f}s - {e}")

if __name__ == "__main__":
    test_embedding_model()