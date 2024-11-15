# Main summarize pipeline

import argparse
from datetime import datetime, timedelta

from src.summarizer.embeddings_computer import EmbeddingsComputer

parser = argparse.ArgumentParser(prog="new summarizer", description="a news summarizer")
if __name__ == "__main__":
	# read arg named environment form the command line
	parser.add_argument("-e", "--environment", default="dev")
	parser.add_argument("-d", "--days_ago", type=int, default=1)
	parser.add_argument("-f", "--filename")
	args = parser.parse_args()
	environment = args.environment
	days_ago = args.days_ago
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
	# first stage
	embedding_model_id = "dunzhang/stella_en_400M_v5"
	embedding_modeller = EmbeddingsComputer(embedding_model_id=embedding_model_id)
	embeddings_path = embedding_modeller.run(
		data_path=args.filename, date_to=date, environment=environment
	)
