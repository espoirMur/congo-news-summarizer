from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from flytekit import task, workflow

clustering_container_name = "espymur/summarization-clustering:latest"


@task
def generate_date(days_ago: int) -> str:
	"""generate the date for the data pull"""
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
	return date


@task(container_image=clustering_container_name)
def pull_data(environment: str, date: str) -> pd.DataFrame:
	"""load data from the database and save it  as local file"""
	from src.summarizer.data_puller import DataPuller

	data_puller = DataPuller(environment=environment, date=date)
	today_news_data = data_puller.run()
	return today_news_data


@task(container_image=clustering_container_name)
def compute_embeddings(
	environment: str, embedding_model_id: str, new_data: pd.DataFrame
) -> np.array:
	"""compute embeddings for the data and save it as local file"""
	from src.summarizer.embeddings_computer import EmbeddingsComputer

	embedding_modeller = EmbeddingsComputer(embedding_model_id=embedding_model_id)
	# maybe create a datatype and make sure it has content in the field
	embedded_documents = embedding_modeller.run(documents=new_data["content"])
	return embedded_documents


@task(container_image=clustering_container_name)
def cluster_data(
	environment: str, embedded_documents: np.array, new_data: pd.DataFrame
) -> pd.DataFrame:
	"""cluster the data and save it as local file"""
	from src.summarizer.cluster_modeler import HierarchicalClusterModeler

	cluster_modeler = HierarchicalClusterModeler()
	important_news_df = cluster_modeler.run(
		today_news_embeddings=embedded_documents, documents=new_data
	)
	return important_news_df


@task(container_image=clustering_container_name)
def save_data(environment: str, important_news_df: pd.DataFrame, date: str) -> str:
	"""save the data to a cloud storage"""
	from src.shared.cloud_storage.cloud_storage import BackBlazeCloudStorage

	cloud_storage = BackBlazeCloudStorage(environment=environment)
	file_name = cloud_storage.save_df_to_blackbaze_bucket(important_news_df, date=date)
	return file_name


@workflow
def clustering_pipeline(
	environment: str, days_ago: int = 0, embedding_model_id: str = "dunzhang/stella_en_400M_v5"
) -> str:
	"""This is the end to end clustering pipeline"""
	date = generate_date(days_ago=days_ago)
	new_data = pull_data(environment=environment, date=date)
	embedded_documents = compute_embeddings(
		environment=environment, embedding_model_id=embedding_model_id, new_data=new_data
	)
	important_news_df = cluster_data(
		environment=environment, embedded_documents=embedded_documents, new_data=new_data
	)
	data_path = save_data(environment=environment, important_news_df=important_news_df, date=date)
	return data_path


if __name__ == "__main__":
	clustering_pipeline("local", 0, "dunzhang/stella_en_400M_v5")
