from openai import OpenAI
import os

"""
UNBEDINGT SPAETER API KEY ENTFERNEN
"""

client = OpenAI(api_key="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")

def embed_text(text: str) -> list[float]:
    """
    Erzeugt ein Embedding aus einem text mit openai embedding
    """

    response = client.embeddings.create(
        model = "text-embedding-3-small",
        input = text
    )

    return response.data[0].embedding