from csv import DictReader as csv_reader
from tempfile import NamedTemporaryFile

from src.shared.cloud_storage.cloud_storage_base import BackBlazeCloudStorageBase


class BackBlazeCloudStorageCSV(BackBlazeCloudStorageBase):
	"""this cloud storage  to use without  using numpy just plain csv reader"""

	def read_file_as_list(self, bucket_name: str, file_name: str) -> list:
		"""Given the filename, download the file and return it as a numpy array"""
		documents = self.download_by_name(bucket_name=bucket_name, file_name=file_name)
		with NamedTemporaryFile(
			delete=True, suffix=".csv", mode="r", encoding="utf-8"
		) as temp_file:
			documents.save_to(temp_file.name)
			reader = csv_reader(temp_file, delimiter=",")
			return list(reader)
