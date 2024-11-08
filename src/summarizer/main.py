# Main summarize pipeline

import argparse
from datetime import datetime, timedelta

from src.summarizer.cluster_modeler import HierarchicalClusterModeler
from src.summarizer.data_puller import DataPuller
from src.summarizer.embeddings_computer import EmbeddingsComputer

parser = argparse.ArgumentParser(prog="new summarizer", description="a news summarizer")
if __name__ == "__main__":
	# read arg named environment form the command line
	parser.add_argument("-e", "--environment", default="dev")
	parser.add_argument("-d", "--days_ago", type=int, default=1)
	parser.add_argument("-st", "--storage_mode", default="local")
	args = parser.parse_args()
	environment = args.environment
	days_ago = args.days_ago
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
	# first stage
	data_puller = DataPuller(environment=environment, date=date)
	data = data_puller.read_data()
	# second stage
	embedding_model_id = "dunzhang/stella_en_400M_v5"
	embedding_computer = EmbeddingsComputer(embedding_model_id=embedding_model_id)
	embeddings = embedding_computer.run(data)
	# third stage
	clustering = HierarchicalClusterModeler(documents=data)
	important_news_df = clustering.run(today_news_embeddings=embeddings)
	data_puller.save_data(important_news_df, storage_mode=args.storage_mode)
