from datetime import datetime
from tempfile import NamedTemporaryFile

import numpy as np
import pandas as pd

from src.shared.cloud_storage.cloud_storage_base import BackBlazeCloudStorageBase
from src.shared.logger import setup_logger

logger = setup_logger("data_puller")

BUCKET_NAME = "congonews-clusters"


class BackBlazeCloudStorage(BackBlazeCloudStorageBase):
	def save_df_to_blackbaze_bucket(
		self, data: pd.DataFrame, bucket_name: str = BUCKET_NAME, **kwargs
	) -> None:
		"""Save a dataframe to a cloud bucket."""
		today = datetime.now().strftime("%Y-%m-%d")
		file_name = self.generate_file_name(date=today)
		with NamedTemporaryFile(delete=True, suffix=".csv") as temp_file:
			data.to_csv(temp_file, sep="|")
			self.upload_file(
				bucket_name=bucket_name,
				file_path=temp_file.name,
				file_name=file_name,
				metadata=kwargs,
			)
			logger.info(f"Saved {file_name} news to the cloud bucket")
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
