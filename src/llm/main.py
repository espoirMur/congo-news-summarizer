import argparse
import json
import os
from datetime import datetime, timedelta
from itertools import groupby
from typing import List
from unicodedata import normalize

from src.llm.generator import LLamaCppGeneratorComponent
from src.shared.cloud_storage.cloud_storage_non_numpy import BackBlazeCloudStorageCSV
from src.shared.logger import setup_logger

logger = setup_logger("summarizer_generative")


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
		try:
			summary = generator.run(template_values={"content": content})
			logger.info(f"Done summarizing the documents  {label}")
			if summary:
				news_data = {"titles": titles, "urls": urls, "summary": summary}
				summaries.append(news_data)
			else:
				logger.warning(f"No summary generated for documents with label {label}")
				continue
		except Exception as e:
			logger.error(f"Error summarizing documents for label {label}: {e}")
			continue
	logger.info("Done summarizing all the documents")
	return summaries


parser = argparse.ArgumentParser()

# this file should run only today
if __name__ == "__main__":
	prompt = "Vous êtes un journaliste congolais"
	parser.add_argument("-e", "--environment", default="dev", help="the environment to use")
	parser.add_argument(
		"-s",
		"--save_to_s3",
		default=False,
		help="where or not to save the file to the cloud storage",
	)
	parser.add_argument(
		"-f", "--file_name", default=None, help="the file name containing to summary"
	)
	parser.add_argument(
		"-d",
		"--day_ago",
		default=0,
		type=int,
		help="the number of days ago when to save the file, if we run on 23/01/2013 and this is 2 the file will be saved with date 21/01/2013",
	)
	args = parser.parse_args()
	cloud_storage = BackBlazeCloudStorageCSV(environment=args.environment)
	date = (datetime.now() - timedelta(days=args.day_ago)).strftime("%Y-%m-%d")
	if args.file_name:
		today_file_name = args.file_name
	else:
		today_file_name = cloud_storage.generate_file_name(date=date)
	download_bucket_name = os.getenv("DOWNLOAD_BUCKET_NAME")
	upload_bucket_name = os.getenv("UPLOAD_BUCKET_NAME")
	logger.info(f"downloading form {today_file_name}")
	api_url = os.getenv("API_URL")
	api_key = os.getenv("RUN_POD_API_KEY")
	assert api_url is not None, "API_URL is not set"
	assert api_key is not None, "RUN_POD_API_KEY is not set"
	data = cloud_storage.read_file_as_list(
		bucket_name=download_bucket_name, file_name=today_file_name
	)
	logger.info("done downloading the document")
	llama_cpp_generator = LLamaCppGeneratorComponent(api_url=api_url, api_key=api_key)
	assert llama_cpp_generator._ping_api(), "API is n ot up"
	summaries = summarize_documents(data, llama_cpp_generator)
	local_file_name = f"news-summaries-{date}.json"
	with open(local_file_name, "w") as temp_file:
		json.dump(summaries, temp_file, ensure_ascii=False, indent=4)
	logger.info(f"summaries saved at {local_file_name}")
	if args.save_to_s3:
		cloud_storage.upload_file(
			bucket_name=upload_bucket_name,
			file_name=f"summaries/news-summaries-{date}.json",
			file_path=local_file_name,
			metadata={"content_type": "application/json"},
		)
		logger.info("done uploading the document")
