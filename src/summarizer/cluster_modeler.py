from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sentence_transformers import SentenceTransformer
from sklearn.metrics import silhouette_score

from src.shared.logger import setup_logger

DEFAULT_TRANSFORMER_KWARGS = {
	"trust_remote_code": True,
	"device": "cpu",
	"config_kwargs": {"use_memory_efficient_attention": False, "unpad_inputs": False},
}
logger = setup_logger("cluster_modeler")


class HierarchicalClusterModeler:
	"""
	This class is responsible for clustering the documents
	"""

	def __init__(
		self,
	) -> None:
		current_directory = Path.cwd()
		self.current_directory = current_directory

	def compute_linkage(
		self,
		today_news_embeddings: np.array,
		method: str = "complete",
		metric: str = "cosine",
	) -> np.array:
		"""Compute the sklearn linkage"""
		mergings = linkage(today_news_embeddings, method=method, metric=metric)
		return mergings

	def select_best_distance(self, X: np.array, merging: np.array) -> tuple[np.array, float]:
		"""start with the document embedding x, and the hierarchical clustering, find the k that maximize the shilouette score"""
		max_shilouette = float("-inf")
		return_labels = np.zeros(X.shape[0])
		best_k = 0
		for k in np.arange(0.1, 0.4, 0.01):
			labels = fcluster(merging, k, criterion="distance")
			score = silhouette_score(X, labels)
			if score > max_shilouette:
				max_shilouette = score
				return_labels = labels
				best_k = k
		return return_labels, best_k

	@staticmethod
	def analyse_embeddings(
		documents: pd.DataFrame,
		embeddings: np.array,
		index: int,
		embedding_model: SentenceTransformer,
		label_column: str = "labels",
	) -> np.array:
		"""take a matrix of embeddings and the labels.
		for each label compute the cosine similarity of the document with that label.
		"""
		document_in_index = documents.query(f"{label_column} == {index}")
		with pd.option_context("display.max_colwidth", None):
			print(document_in_index.title)
		document_index = document_in_index.index
		vectors = embeddings[document_index]
		return embedding_model.similarity(vectors, vectors)

	def select_top_clusters(self, news_df: pd.DataFrame) -> pd.DataFrame:
		"""select the clusters with the more than two documents"""
		cluster_counts = news_df["labels"].value_counts()
		labels_with_more_than_one = cluster_counts[cluster_counts > 1].index
		important_news_df = news_df.loc[news_df.labels.isin(labels_with_more_than_one)]
		return important_news_df

	def run(self, today_news_embeddings: np.array, documents: pd.DataFrame) -> str:
		"""start the clustering process"""
		mergings = self.compute_linkage(today_news_embeddings)
		return_labels, best_k = self.select_best_distance(today_news_embeddings, mergings)
		logger.info(
			f"finished clustering with best_k = {best_k:3f} with and number_of_clusters = {np.unique(return_labels).shape[0]}"
		)
		documents["labels"] = return_labels
		important_news_df = self.select_top_clusters(documents)
		logger.info(f"the important news data is of shape: {important_news_df.shape[0]}")
		logger.info(f"the number of labels are {np.unique(important_news_df.labels).shape[0]}")

		return important_news_df
