import argparse
import json
import os
from datetime import datetime
from itertools import groupby
from tempfile import NamedTemporaryFile
from typing import List
from unicodedata import normalize

from src.llm.generator import LLamaCppGeneratorComponent
from src.shared.cloud_storage.cloud_storage_non_numpy import BackBlazeCloudStorageCSV
from src.shared.logger import setup_logger

logger = setup_logger("data_puller")


def summarize_documents(data: List, generator: LLamaCppGeneratorComponent):
	summaries = []

	def sort_function(x):
		return x["labels"]

	sorted_data = sorted(data, key=sort_function)
	grouped_data = groupby(sorted_data, key=sort_function)
	for label, group in grouped_data:
		news_data = list(group)
		titles = [news["title"] for news in news_data]
		urls = [news["url"] for news in news_data]
		content = "\n".join([news["content"] for news in news_data])
		content = normalize("NFKD", content)
		summary = generator.run(template_values={"content": content})
		logger.info(f"Done summarizing the documents  {label}")
		if summary:
			news_data = {"titles": titles, "urls": urls, "summary": summary}
			summaries.append(news_data)
	return summaries


parser = argparse.ArgumentParser()

# this file should run only today
if __name__ == "__main__":
	prompt = "You are a french news reporter"
	parser.add_argument("-e", "--environment", default="dev")
	args = parser.parse_args()
	cloud_storage = BackBlazeCloudStorageCSV(environment=args.environment)
	today = datetime.now().strftime("%Y-%m-%d")
	today_file_name = cloud_storage.generate_file_name(date=today)
	bucket_name = os.getenv("BUCKET_NAME")
	api_url = os.getenv("API_URL")
	data = cloud_storage.read_file_as_list(bucket_name=bucket_name, file_name=today_file_name)
	llama_cpp_generator = LLamaCppGeneratorComponent(api_url=api_url, prompt=prompt)
	assert llama_cpp_generator._ping_api()
	summaries = summarize_documents(data, llama_cpp_generator)
	with NamedTemporaryFile(delete=True, suffix=".json", mode="w+") as temp_file:
		json.dump(summaries, temp_file, ensure_ascii=False)
		cloud_storage.upload_file(
			bucket_name=bucket_name,
			file_name=f"summaries/news-summaries-{today}.json",
			file_path=temp_file.name,
			metadata={"dates": today},
		)
