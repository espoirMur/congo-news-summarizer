import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import b2sdk.v2 as back_blaze
import numpy as np
import pandas as pd
from b2sdk._internal.transfer.inbound.downloaded_file import DownloadedFile
from dotenv import load_dotenv

from src.shared.logger import setup_logger

logger = setup_logger("data_puller")

BUCKET_NAME = "congonews-clusters"


class BackBlazeCloudStorage:
	"""
	This class is responsible for interacting with backblaze cloud storage.

	It will instantiate the cloud storage client and provide methods for uploading and downloading files
	"""

	def load_environment_variables(self, environment: str = "local") -> tuple[str, str]:
		"""Load an environment variables and return them, raise a value error if one of them is empty."""
		current_directory = Path.cwd()
		env_file = current_directory.joinpath(f"env_{environment}")
		load_dotenv(env_file)
		application_key_id = os.getenv("BACK_BLAZE_KEY_ID")
		application_key = os.getenv("BACK_BLAZE_APPLICATION_KEY")

		if not application_key_id or not application_key:
			raise ValueError("Application key id or application key is empty")

		return application_key_id, application_key

	def __init__(self, environment: str = "local") -> None:
		application_key_id, application_key = self.load_environment_variables(
			environment=environment
		)
		info = back_blaze.InMemoryAccountInfo()
		self.back_blaze_api = back_blaze.B2Api(info)
		self.back_blaze_api.authorize_account("production", application_key_id, application_key)

	def get_bucket(self, bucket_name: str) -> back_blaze.Bucket:
		"""get the bucket with the given name"""
		return self.back_blaze_api.get_bucket_by_name(bucket_name)

	def upload_file(self, bucket_name: str, file_path: str, file_name: str, metadata: dict) -> str:
		"""upload the file to the bucket with the given name"""
		bucket = self.get_bucket(bucket_name)
		uploaded_file = bucket.upload_local_file(
			local_file=file_path, file_name=file_name, file_infos=metadata
		)
		return self.back_blaze_api.get_download_url_for_fileid(uploaded_file.id_)

	def download_by_name(self, bucket_name: str, file_name: str) -> DownloadedFile:
		"""download the file from the bucket with the given name"""
		bucket = self.get_bucket(bucket_name)
		return bucket.download_file_by_name(file_name)

	def save_df_to_blackbaze_bucket(
		self, data: pd.DataFrame, bucket_name: str = BUCKET_NAME, **kwargs
	) -> None:
		"""Save a dataframe to a cloud bucket."""
		today = datetime.now().strftime("%Y-%m-%d")
		date = kwargs.get("date", today)
		file_name = f"news-clusters-{today}-to-{date}.csv"
		with NamedTemporaryFile(delete=True, suffix=".csv") as temp_file:
			data.to_csv(temp_file, sep="|")
			self.upload_file(
				bucket_name=bucket_name,
				file_path=temp_file.name,
				file_name=file_name,
				metadata=kwargs,
			)
			logger.info(f"Saved {date} news to the cloud bucket")
			return file_name

	def download_file_as_numpy_array(self, bucket_name: str, file_name: str) -> np.array:
		"""Given the filename, download the file and return it as a numpy array"""
		documents = self.download_by_name(bucket_name=bucket_name, file_name=file_name)
		with NamedTemporaryFile(delete=True, suffix=".csv") as temp_file:
			documents.save_to(temp_file.name)
			csv_data = np.loadtxt(
				temp_file.name,
				delimiter="|",
				skiprows=1,
				dtype=[("index", "i8"), ("content", "U10000")],
				encoding="utf-8",
			)
			csv_data = np.array(csv_data.tolist())
		return csv_data

	def download_npy_file(self, bucket_name: str, file_name: str) -> np.array:
		"""Given the filename, download the file and return it as a numpy array"""
		documents = self.download_by_name(bucket_name=bucket_name, file_name=file_name)
		with NamedTemporaryFile(delete=True, suffix=".npy") as temp_file:
			documents.save_to(temp_file.name)
			return np.load(temp_file.name)
