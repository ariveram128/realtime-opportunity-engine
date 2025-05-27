from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Load a pre-trained sentence transformer model
# 'all-MiniLM-L6-v2' is a good starting point: fast and decent quality.
# For higher accuracy (but slower), consider models like 'all-mpnet-base-v2'
MODEL_NAME = 'all-MiniLM-L6-v2'
try:
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Successfully loaded SentenceTransformer model: {MODEL_NAME}")
except Exception as e:
    logger.error(f"Error loading SentenceTransformer model '{MODEL_NAME}': {e}")
    logger.error("NLP features will be unavailable. Ensure the model is downloaded or an alternative is configured.")
    model = None

def get_embedding(text: str):
    """Generates a sentence embedding for the given text."""
    if not model:
        # Fallback if model loading failed, or return None/raise error
        logger.warning("SentenceTransformer model not loaded. Returning zero vector.")
        # The dimensionality depends on the model, MiniLM-L6-v2 has 384 dimensions.
        # This needs to match the expected dimension if a real model was used.
        # A more robust solution would be to know the model's expected dimension.
        # For 'all-MiniLM-L6-v2', it's 384. If using another model, adjust this.
        # A zero vector will result in zero similarity unless both vectors are zero.
        return np.zeros(384) 
    if not text or not isinstance(text, str):
        logger.warning("Invalid text input for embedding. Returning zero vector.")
        return np.zeros(model.get_sentence_embedding_dimension() if model else 384)
    try:
        embedding = model.encode(text, convert_to_tensor=False) # convert_to_tensor=False for numpy array
        return embedding
    except Exception as e:
        logger.error(f"Error generating embedding for text '{text[:50]}...': {e}")
        return np.zeros(model.get_sentence_embedding_dimension() if model else 384)

def calculate_cosine_similarity(vec1, vec2):
    """Calculates cosine similarity between two vectors."""
    if vec1 is None or vec2 is None or vec1.shape != vec2.shape:
        logger.warning("Invalid vectors for cosine similarity calculation. Returning 0.")
        return 0.0
    # Reshape to 2D arrays if they are 1D
    vec1_2d = vec1.reshape(1, -1)
    vec2_2d = vec2.reshape(1, -1)
    try:
        similarity_matrix = cosine_similarity(vec1_2d, vec2_2d)
        return similarity_matrix[0][0] # Extract the single similarity value
    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0

# Example Usage (can be removed or kept for testing)
if __name__ == '__main__':
    query = "software engineering internship in san francisco"
    job_desc_relevant = "We are looking for a software engineering intern to join our SF team. You will work with Python and JavaScript."
    job_desc_less_relevant = "Marketing intern position available in New York for a sales driven individual."

    query_embedding = get_embedding(query)
    relevant_job_embedding = get_embedding(job_desc_relevant)
    less_relevant_job_embedding = get_embedding(job_desc_less_relevant)

    if query_embedding is not None and relevant_job_embedding is not None:
        similarity_relevant = calculate_cosine_similarity(query_embedding, relevant_job_embedding)
        print(f"Similarity (Relevant): {similarity_relevant:.4f}")

    if query_embedding is not None and less_relevant_job_embedding is not None:
        similarity_less_relevant = calculate_cosine_similarity(query_embedding, less_relevant_job_embedding)
        print(f"Similarity (Less Relevant): {similarity_less_relevant:.4f}")

    # Test with empty or invalid text
    empty_embedding = get_embedding("")
    similarity_empty = calculate_cosine_similarity(query_embedding, empty_embedding)
    print(f"Similarity (Empty Description): {similarity_empty:.4f}") 