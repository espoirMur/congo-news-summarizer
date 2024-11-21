import os
from itertools import groupby
from typing import List
from unicodedata import normalize

from shared.cloud_storage.cloud_storage_non_numpy import BackBlazeCloudStorageCSV
from src.llm.generator import LLamaCppGeneratorComponent


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
		news_data = {"titles": titles, "urls": urls, "summary": summary}
		summaries.append(news_data)
		print(f" This is the summary for label {label}")
		print(summary)
		print(f"Here are the titles for label {label}")
		print(10 * "*")
		for title in titles:
			print(title)
		print(10 * "*")
		return summaries


if __name__ == "__main__":
	bucket_name = os.getenv("BUCKET_NAME")
	api_url = os.getenv("API_URL")
	prompt = "You are a french news reporter"
	cloud_storage = BackBlazeCloudStorageCSV(environment="local")
	data = cloud_storage.read_file_as_list(
		bucket_name="congonews-clusters", file_name="news-clusters-2023-08-18-to-2023-08-19.csv"
	)
	llama_cpp_generator = LLamaCppGeneratorComponent(api_url=api_url, prompt=prompt)
	assert llama_cpp_generator._ping_api()
	summaries = summarize_documents(data, llama_cpp_generator)
	cloud_storage.upload_file(bucket_name=bucket_name, file_name="tnesn", file_path="test")
