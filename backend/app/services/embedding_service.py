from sentence_transformers import SentenceTransformer

class EmbeddingService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            # Load model on first use
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> list[float]:
        model = cls.get_model()
        # Encode returns a numpy array, convert to list
        embedding = model.encode(text)
        return embedding.tolist()
