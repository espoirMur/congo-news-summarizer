import json
import os
from datetime import datetime, timedelta

from src.llm.generator import LLamaCppGeneratorComponent
from src.shared.cloud_storage.cloud_storage_non_numpy import BackBlazeCloudStorageCSV
from src.shared.logger import setup_logger

logger = setup_logger("summarizer_generative")


def run(
	environment: str = "dev",
	save_to_s3: bool = False,
	file_name: str = None,
	day_ago: int = 0,
):
	"""
	Run the generative summarizer pipeline
	"""
	prompt = "You are a french news reporter"
	cloud_storage = BackBlazeCloudStorageCSV(environment=environment)
	date = (datetime.now() - timedelta(days=day_ago)).strftime("%Y-%m-%d")
	if file_name:
		today_file_name = file_name
	else:
		today_file_name = cloud_storage.generate_file_name(date=date)
	download_bucket_name = os.getenv("DOWNLOAD_BUCKET_NAME")
	upload_bucket_name = os.getenv("UPLOAD_BUCKET_NAME")
	api_url = os.getenv("API_URL")
	data = cloud_storage.read_file_as_list(
		bucket_name=download_bucket_name, file_name=today_file_name
	)
	logger.info("done downloading the document")
	llama_cpp_generator = LLamaCppGeneratorComponent(api_url=api_url, prompt=prompt)
	assert llama_cpp_generator._ping_api(), "API is not up"
	summaries = llama_cpp_generator.summarize_documents(data)
	local_file_name = f"news-summaries-{date}.json"
	with open(local_file_name, "w") as temp_file:
		json.dump(summaries, temp_file, ensure_ascii=False, indent=4)
	if save_to_s3:
		cloud_storage.upload_file(
			bucket_name=upload_bucket_name,
			file_name=f"summaries/news-summaries-{date}.json",
			file_path=local_file_name,
			metadata={"content_type": "application/json"},
		)
		logger.info("done uploading the document")
