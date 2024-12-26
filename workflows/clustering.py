from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from flytekit import task, workflow
from flytekit.core.pod_template import PodTemplate
from kubernetes.client.models import V1Container, V1EnvVar, V1PodSpec

clustering_container_name = "espymur/summarization-clustering:flyte-latest-2"


pod_specification = V1PodSpec(
	containers=[
		V1Container(
			name="primary",
			image=clustering_container_name,
			image_pull_policy="Always",
			env=[
				V1EnvVar(
					name="FLYTE_AWS_ENDPOINT", value="http://minio.flyte.svc.cluster.local:9000"
				),
				V1EnvVar(name="FLYTE_AWS_ACCESS_KEY_ID", value="minio"),
				V1EnvVar(name="FLYTE_AWS_SECRET_ACCESS_KEY", value="miniostorage"),
			],
		)
	]
)

pod_template = PodTemplate(primary_container_name="primary", pod_spec=pod_specification)


@task(pod_template=pod_template)
def generate_date(days_ago: int) -> str:
	"""generate the date for the data pull"""
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
	return date


@task(pod_template=pod_template)
def pull_data(environment: str, date: str) -> pd.DataFrame:
	"""load data from the database and save it  as local file"""
	from src.summarizer.data_puller import DataPuller

	data_puller = DataPuller(environment=environment, date=date)
	today_news_data = data_puller.run()
	return today_news_data


@task(pod_template=pod_template)
def compute_embeddings(embedding_model_id: str, new_data: pd.DataFrame) -> np.array:
	"""compute embeddings for the data and save it as local file"""
	from src.summarizer.embeddings_computer import EmbeddingsComputer

	embedding_modeller = EmbeddingsComputer(embedding_model_id=embedding_model_id)
	# maybe create a datatype and make sure it has content in the field
	embedded_documents = embedding_modeller.run(documents=new_data["content"])
	return embedded_documents


@task(pod_template=pod_template)
def cluster_data(embedded_documents: np.array, new_data: pd.DataFrame) -> pd.DataFrame:
	"""cluster the data and save it as local file"""
	from src.summarizer.cluster_modeler import HierarchicalClusterModeler

	cluster_modeler = HierarchicalClusterModeler()
	important_news_df = cluster_modeler.run(
		today_news_embeddings=embedded_documents, documents=new_data
	)
	return important_news_df


@task(pod_template=pod_template)
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
		embedding_model_id=embedding_model_id, new_data=new_data
	)
	important_news_df = cluster_data(embedded_documents=embedded_documents, new_data=new_data)
	data_path = save_data(environment=environment, important_news_df=important_news_df, date=date)
	return data_path


if __name__ == "__main__":
	clustering_pipeline("local", 0, "dunzhang/stella_en_400M_v5")
