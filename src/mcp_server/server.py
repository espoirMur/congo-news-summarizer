# MCP Server for Congo News Summarizer

from datetime import datetime, timedelta

from fastmcp import FastMCP

from src.summarizer.cluster_modeler import HierarchicalClusterModeler
from src.summarizer.data_puller import DataPuller
from src.summarizer.embeddings_computer import EmbeddingsComputer

# Initialize FastMCP server
mcp = FastMCP("congo-news-summarizer")

EMBEDDING_MODEL_ID = "dunzhang/stella_en_400M_v5"


def _run_pipeline(environment: str, days_ago: int) -> dict:
	"""Run the news clustering pipeline and return structured data."""
	date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

	# Pull data
	data_puller = DataPuller(environment=environment, date=date)
	today_news_data = data_puller.run()

	# Compute embeddings
	embedding_modeller = EmbeddingsComputer(embedding_model_id=EMBEDDING_MODEL_ID)
	embedding_documents = embedding_modeller.run(documents=today_news_data["content"])

	# Cluster
	cluster_modeler = HierarchicalClusterModeler()
	important_news_df = cluster_modeler.run(
		today_news_embeddings=embedding_documents, documents=today_news_data
	)

	json_data = important_news_df.to_json(orient="records")

	return {"from_date": date, "news_clusters": json_data}


@mcp.tool()
def get_today_news_clustered(environment: str = "local", days_ago: int = 1) -> dict:
	"""
	Fetch today's news, cluster by topic, and return as JSON.

	Args:
	    environment: Environment name ('local' or 'prod')
	    days_ago: Number of days to look back for news

	Returns:
	    JSON object with date and clusters of news articles
	"""
	return _run_pipeline(environment=environment, days_ago=days_ago)


if __name__ == "__main__":
	# read host and port from cmd args
	import argparse

	parser = argparse.ArgumentParser(description="Run the MCP server.")
	parser.add_argument("--host", type=str, default="localhost")
	parser.add_argument("--port", type=int, default=9090)
	args = parser.parse_args()
	host = args.host
	port = args.port
	mcp.run(transport="streamable-http", host=host, port=port)
