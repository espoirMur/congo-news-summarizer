from pathlib import Path
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from src.shared.logger import setup_logger

DEFAULT_TRANSFORMER_KWARGS = {
	"trust_remote_code": True,  # this is a risky argument!
	"device": "cpu",
	"config_kwargs": {"use_memory_efficient_attention": False, "unpad_inputs": False},
}
logger = setup_logger("cluster_modeler")


class EmbeddingsComputer:
	"""class that compute the document embedding"""

	def __init__(self, embedding_model_path: str | Path) -> None:
		self.embedding_model_path = embedding_model_path
		self.sentence_transformer_model = self.init_sentence_transformer()

	def init_sentence_transformer(
		self, transformer_kwargs: dict = DEFAULT_TRANSFORMER_KWARGS
	) -> SentenceTransformer:
		"""Initialize the sentence transformer model"""
		transformer_kwargs["cache_folder"] = self.embedding_model_path
		transformer_kwargs["model_name_or_path"] = self.embedding_model_path
		sentence_transformer_model = SentenceTransformer(**transformer_kwargs)
		return sentence_transformer_model

	def embed_documents(self, documents: Iterable[str]) -> np.array:
		"""Embed the documents using the sentence transformer model"""
		today_news_embeddings = self.sentence_transformer_model.encode(
			documents, show_progress_bar=True
		)
		return today_news_embeddings

	def run(self, documents: Iterable[str]) -> np.array:
		today_news_embeddings = self.embed_documents(documents)
		return today_news_embeddings
