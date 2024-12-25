import argparse

from src.shared.logger import setup_logger
from src.summarizer.runner import run as run_clustering

logger = setup_logger("summarizer_clustering_main")

parser = argparse.ArgumentParser(prog="new summarizer", description="a news summarizer")
if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("-e", "--environment", default="dev")
	parser.add_argument("-d", "--days_ago", type=int, default=0)
	args = parser.parse_args()
	run_clustering(environment=args.environment, days_ago=args.days_ago)
