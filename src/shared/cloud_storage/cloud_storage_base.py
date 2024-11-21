import os
from pathlib import Path

import b2sdk.v2 as back_blaze
from b2sdk._internal.transfer.inbound.downloaded_file import DownloadedFile
from dotenv import load_dotenv


class BackBlazeCloudStorageBase:
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
