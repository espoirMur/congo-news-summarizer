from datetime import datetime
from os import getenv
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Iterable

import numpy as np
from sentence_transformers import SentenceTransformer

from src.shared.cloud_storage import BackBlazeCloudStorage
from src.shared.logger import setup_logger

DEFAULT_TRANSFORMER_KWARGS = {
	"trust_remote_code": True,
	"device": "cpu",
	"config_kwargs": {"use_memory_efficient_attention": False, "unpad_inputs": False},
}
logger = setup_logger("cluster_modeler")


class EmbeddingsComputer:
	"""class that compute the document embedding"""

	def __init__(self, embedding_model_id: str) -> None:
		self.embedding_model_id = embedding_model_id
		current_directory = Path.cwd()
		self.current_directory = current_directory
		self.sentence_transformer_model = self.init_sentence_transformer()

	def init_sentence_transformer(
		self, transformer_kwargs: dict = DEFAULT_TRANSFORMER_KWARGS
	) -> SentenceTransformer:
		"""Initialize the sentence transformer model"""

		embedding_model_path = self.current_directory.joinpath("models", self.embedding_model_id)
		model_path = self.current_directory.joinpath(self.embedding_model_id)
		transformer_kwargs["cache_folder"] = model_path
		transformer_kwargs["model_name_or_path"] = embedding_model_path.__str__()
		sentence_transformer_model = SentenceTransformer(**transformer_kwargs)
		return sentence_transformer_model

	def embed_documents(self, documents: Iterable[str]) -> np.array:
		"""Embed the documents using the sentence transformer model"""
		today_news_embeddings = self.sentence_transformer_model.encode(
			documents, show_progress_bar=True
		)
		return today_news_embeddings

	def run(self, data_path: str, date_to: str, environment: str) -> np.array:
		bucket_name = getenv("BUCKET_NAME")
		cloud_storage = BackBlazeCloudStorage(environment=environment)
		documents = cloud_storage.download_file_as_numpy_array(
			bucket_name=bucket_name, file_name=data_path
		)
		documents = documents[:, 1]
		today = datetime.now().strftime("%Y-%m-%d")
		today_news_embeddings = self.embed_documents(documents)
		file_name = f"embeddings/news-embeddings-{today}-to-{date_to}.npy"
		with NamedTemporaryFile(delete=True, suffix=".npy") as temp_file:
			np.save(temp_file, today_news_embeddings)
			remote_path = cloud_storage.upload_file(
				bucket_name=bucket_name,
				file_path=temp_file.name,
				file_name=file_name,
				metadata={"date": date_to},
			)
		return remote_path
