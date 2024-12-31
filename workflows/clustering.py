from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from flytekit import FlyteDirectory, task, workflow
from flytekit.core.pod_template import PodTemplate
from kubernetes.client.models import (
	V1Container,
	V1EnvVar,
	V1EnvVarSource,
	V1PodSpec,
	V1SecretKeySelector,
)

clustering_container_name = "espymur/summarization-clustering:flyte-latest-2"

database_env_variables = [
	V1EnvVar(
		name="POSTGRES_USER",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(name="database-credentials", key="POSTGRES_USER")
		),
	),
	V1EnvVar(
		name="POSTGRES_PASSWORD",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(name="database-credentials", key="POSTGRES_PASSWORD")
		),
	),
	V1EnvVar(
		name="POSTGRES_HOST",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(name="database-credentials", key="POSTGRES_HOST")
		),
	),
	V1EnvVar(
		name="POSTGRES_PORT",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(name="database-credentials", key="POSTGRES_PORT")
		),
	),
	V1EnvVar(
		name="POSTGRES_DB",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(name="database-credentials", key="POSTGRES_DB")
		),
	),
]

# Create a function to create this with needed environment variables


def build_pod_spec(
	pod_name: str,
	container_name: str,
	container_image: str,
	env_variables: Optional[List[V1EnvVar]],
) -> V1PodSpec:
	return V1PodSpec(
		containers=[
			V1Container(
				name=container_name,
				image=container_image,
				image_pull_policy="Always",
				env=env_variables,
			)
		]
	)


data_puller_pod_template = PodTemplate(
	primary_container_name="primary",
	pod_spec=build_pod_spec(
		pod_name="data-puller",
		container_name="data-puller",
		container_image=clustering_container_name,
		env_variables=database_env_variables,
	),
)

embedding_model_pod_template = PodTemplate(
	primary_container_name="primary",
	pod_spec=build_pod_spec(
		pod_name="embedding-model",
		container_image=clustering_container_name,
		container_name="embedding-model",
		env_variables=None,
	),
)


@task(container_image=clustering_container_name)
def generate_date(days_ago: int) -> str:
	"""generate the date for the data pull"""
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
	return date


@task(pod_template=data_puller_pod_template)
def pull_data(environment: str, date: str) -> pd.DataFrame:
	"""load data from the database and save it  as local file"""
	from src.summarizer.data_puller import DataPuller

	data_puller = DataPuller(environment=environment, date=date)
	today_news_data = data_puller.run()
	return today_news_data


@task(pod_template=embedding_model_pod_template)
def compute_embeddings(embedding_model_path: FlyteDirectory, new_data: pd.DataFrame) -> np.array:
	"""compute embeddings for the data and save it as local file"""
	from src.summarizer.embeddings_computer import EmbeddingsComputer

	embedding_model_path.download()

	embedding_modeller = EmbeddingsComputer(embedding_model_path=embedding_model_path.path)
	# maybe create a datatype and make sure it has content in the field
	embedded_documents = embedding_modeller.run(documents=new_data["content"])
	return embedded_documents


@task(container_image=clustering_container_name)
def cluster_data(embedded_documents: np.array, new_data: pd.DataFrame) -> pd.DataFrame:
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
	environment: str, days_ago: int = 0, embedding_model_path: str = "dunzhang/stella_en_400M_v5"
) -> str:
	"""This is the end to end clustering pipeline"""
	date = generate_date(days_ago=days_ago)
	new_data = pull_data(environment=environment, date=date)
	input_directory = FlyteDirectory("s3://flyte/models/{embedding_model_path}")
	embedded_documents = compute_embeddings(embedding_model_path=input_directory, new_data=new_data)
	important_news_df = cluster_data(embedded_documents=embedded_documents, new_data=new_data)
	data_path = save_data(environment=environment, important_news_df=important_news_df, date=date)
	return data_path


if __name__ == "__main__":
	clustering_pipeline("local", 0, "dunzhang/stella_en_400M_v5")
