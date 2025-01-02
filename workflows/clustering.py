from datetime import datetime, timedelta
from typing import List, Optional

import numpy as np
import pandas as pd
from flytekit import FlyteDirectory, Resources, task, workflow
from flytekit.core.pod_template import PodTemplate
from kubernetes.client.models import (
	V1Container,
	V1EnvVar,
	V1EnvVarSource,
	V1PodSpec,
	V1SecretKeySelector,
)

clustering_container_name = "espymur/summarization-clustering:flyte-latest-2"
generator_container_name = "espymur/summarization-generator:dev"

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

cloud_storage_env_variables = [
	V1EnvVar(
		name="BACK_BLAZE_APPLICATION_KEY",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(
				name="cloud-storage-credentials", key="BACK_BLAZE_APPLICATION_KEY"
			)
		),
	),
	V1EnvVar(
		name="BACK_BLAZE_KEYNAME",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(
				name="cloud-storage-credentials", key="BACK_BLAZE_KEYNAME"
			)
		),
	),
	V1EnvVar(
		name="BACK_BLAZE_KEY_ID",
		value_from=V1EnvVarSource(
			secret_key_ref=V1SecretKeySelector(
				name="cloud-storage-credentials", key="BACK_BLAZE_KEY_ID"
			)
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
	primary_container_name="data-puller",
	pod_spec=build_pod_spec(
		pod_name="data-puller",
		container_name="data-puller",
		container_image=clustering_container_name,
		env_variables=database_env_variables,
	),
)

embedding_model_pod_template = PodTemplate(
	primary_container_name="embedding-model",
	pod_spec=build_pod_spec(
		pod_name="embedding-model",
		container_image=clustering_container_name,
		container_name="embedding-model",
		env_variables=None,
	),
)

save_data_pod_template = PodTemplate(
	primary_container_name="save-data",
	pod_spec=build_pod_spec(
		pod_name="save-data",
		container_image=clustering_container_name,
		container_name="save-data",
		env_variables=cloud_storage_env_variables,
	),
)

generator_pod_template = PodTemplate(
	primary_container_name="generator",
	pod_spec=build_pod_spec(
		pod_name="generator",
		container_image=generator_container_name,
		container_name="generator",
		env_variables=None,
	),
)


@task(container_image=clustering_container_name, cache=True, cache_version="1.0")
def generate_date(days_ago: int) -> str:
	"""generate the date for the data pull"""
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
	return date


@task(pod_template=data_puller_pod_template, cache=True, cache_version="1.0")
def pull_data(environment: str, date: str) -> pd.DataFrame:
	"""load data from the database and save it  as local file"""
	from src.summarizer.data_puller import DataPuller

	data_puller = DataPuller(environment=environment, date=date)
	today_news_data = data_puller.run()
	return today_news_data


@task(
	pod_template=embedding_model_pod_template,
	requests=Resources(cpu="1", mem="2Gi"),
	limits=Resources(cpu="1", mem="2Gi"),
	cache=True,
	cache_version="1.0",
)
def compute_embeddings(embedding_model_path: FlyteDirectory, new_data: pd.DataFrame) -> np.array:
	"""compute embeddings for the data and save it as local file"""
	from src.summarizer.embeddings_computer import EmbeddingsComputer

	embedding_model_path.download()

	embedding_modeller = EmbeddingsComputer(embedding_model_path=embedding_model_path.path)
	# maybe create a datatype and make sure it has content in the field
	embedded_documents = embedding_modeller.run(documents=new_data["content"])
	return embedded_documents


@task(container_image=clustering_container_name, cache=True, cache_version="1.0")
def cluster_data(embedded_documents: np.array, new_data: pd.DataFrame) -> pd.DataFrame:
	"""cluster the data and save it as local file"""
	from src.summarizer.cluster_modeler import HierarchicalClusterModeler

	cluster_modeler = HierarchicalClusterModeler()
	important_news_df = cluster_modeler.run(
		today_news_embeddings=embedded_documents, documents=new_data
	)
	return important_news_df


@task(pod_template=save_data_pod_template, cache=True, cache_version="1.0")
def save_data(environment: str, important_news_df: pd.DataFrame, date: str) -> str:
	"""save the data to a cloud storage"""
	from src.shared.cloud_storage.cloud_storage import BackBlazeCloudStorage

	cloud_storage = BackBlazeCloudStorage(environment=environment)
	file_name = cloud_storage.save_df_to_blackbaze_bucket(important_news_df, date=date)
	return file_name


# TODO: this should go to the generator file


@task(pod_template=generator_pod_template, cache=True, cache_version="1.0")
def generate_summary(news_data: pd.DataFrame, api_url: str) -> List[dict]:
	"""generate a summary of the news"""
	from src.llm.generator import LLamaCppGeneratorComponent

	prompt = "You are a french news reporter"
	llama_cpp_generator = LLamaCppGeneratorComponent(api_url=api_url, prompt=prompt)
	summaries = llama_cpp_generator.summarize_documents(news_data)
	return summaries


@task(pod_template=save_data_pod_template, cache=True, cache_version="1.0")
def save_summaries(environment: str, summaries: List[dict], date: str) -> str:
	"""save the summaries to a cloud storage"""
	import json

	from src.shared.cloud_storage.cloud_storage import BackBlazeCloudStorage

	cloud_storage = BackBlazeCloudStorage(environment=environment)
	upload_bucket_name = "congo-news-summaries"
	local_file_name = f"news-summaries-{date}.json"
	with open(local_file_name, "w") as temp_file:
		json.dump(summaries, temp_file, ensure_ascii=False, indent=4)
	file_name = cloud_storage.upload_file(
		bucket_name=upload_bucket_name,
		file_name=f"summaries/news-summaries-{date}.json",
		file_path=local_file_name,
		metadata={"content_type": "application/json"},
	)

	return file_name


@workflow
def clustering_pipeline(
	environment: str,
	days_ago: int = 0,
	api_url: str = "http://host.docker.internal:8001",
) -> str:
	"""This is the end to end clustering pipeline"""
	date = generate_date(days_ago=days_ago)
	new_data = pull_data(environment=environment, date=date)
	input_directory = FlyteDirectory("s3://flyte/stella_en_400M_v5")
	embedded_documents = compute_embeddings(embedding_model_path=input_directory, new_data=new_data)
	important_news_df = cluster_data(embedded_documents=embedded_documents, new_data=new_data)
	summaries = generate_summary(news_data=important_news_df, api_url=api_url)
	summary_file_name = save_summaries(environment=environment, summaries=summaries, date=date)
	return summary_file_name


if __name__ == "__main__":
	clustering_pipeline("local", 0, "dunzhang/stella_en_400M_v5")
