from datetime import datetime, timedelta

from src.shared.cloud_storage.cloud_storage import BackBlazeCloudStorage
from src.shared.logger import setup_logger
from src.summarizer.cluster_modeler import HierarchicalClusterModeler
from src.summarizer.data_puller import DataPuller
from src.summarizer.embeddings_computer import EmbeddingsComputer

logger = setup_logger("summarizer_clustering_main")


def run_summarizer(
	environment: str = "dev",
	days_ago: str = 0,
	embedding_model_id: str = "dunzhang/stella_en_400M_v5",
):
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

	data_puller = DataPuller(environment=environment, date=date)
	today_news_data = data_puller.run()

	embedding_modeller = EmbeddingsComputer(embedding_model_id=embedding_model_id)
	embedding_documents = embedding_modeller.run(documents=today_news_data["content"])

	cluster_modeler = HierarchicalClusterModeler()
	important_news_df = cluster_modeler.run(
		today_news_embeddings=embedding_documents, documents=today_news_data
	)

	cloud_storage = BackBlazeCloudStorage(environment=environment)
	file_name = cloud_storage.save_df_to_blackbaze_bucket(important_news_df, date=date)
	logger.info(f"this is the filename {file_name}")
