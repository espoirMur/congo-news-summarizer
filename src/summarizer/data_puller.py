from datetime import datetime
from os import getenv
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict

import pandas as pd
from dotenv import load_dotenv

from src.shared.cloud_storage import BackBlazeCloudStorage
from src.shared.database import execute_query, generate_database_connection
from src.shared.logger import setup_logger

logger = setup_logger("data_puller")


class DataPuller:
	"""This class will be responsible to read the data for the new summarizer and save the data into a local storage or into a cloud bucket."""

	def __init__(self, environment: str, date: str) -> None:
		current_directory = Path.cwd()
		env_file = current_directory.joinpath(f".env_{environment}")
		self.current_directory = current_directory
		self.environment = environment
		cloud_storage = BackBlazeCloudStorage(environment=self.environment)
		self.cloud_storage = cloud_storage
		self.date = date

		load_dotenv(dotenv_path=env_file, override=True)

	def load_database_credentials(self) -> Dict[str, str]:
		"""Load an environment variables and return them, raise a value error if one of them is empty."""
		database_user = getenv("POSTGRES_USER")
		database_password = getenv("POSTGRES_PASSWORD")
		database_host = getenv("POSTGRES_HOST")
		database_port = getenv("POSTGRES_PORT")
		database_name = getenv("POSTGRES_DB")

		if (
			not database_user
			or not database_password
			or not database_host
			or not database_port
			or not database_name
		):
			raise ValueError("Database credentials are missing")

		return {
			"user": database_user,
			"password": database_password,
			"host": database_host,
			"port": database_port,
			"database": database_name,
		}

	def read_data(self) -> pd.DataFrame:
		"""Read the data from the database and return the pnadas dataframe of the data."""

		database_credentials = self.load_database_credentials()

		connection = generate_database_connection(database_credentials)
		article_query = f"SELECT id AS database_id, content, title, posted_at, url FROM article WHERE posted_at::date BETWEEN '{self.date}' AND CURRENT_DATE"
		today_articles = execute_query(connection, article_query)
		news_df = pd.DataFrame(today_articles)
		logger.info(f"today news data is of shape: {news_df.shape[0]}")
		news_df.columns = ["database_id", "content", "title", "posted_at", "url"]
		news_df = news_df.drop_duplicates(subset="content").reset_index(drop=True)

		return news_df

	def save_data(self, data: pd.DataFrame, storage_mode="local") -> None:
		"""Save data either to the local environment or to a cloud bucket."""

		if storage_mode == "local":
			self.save_local(data)
		else:
			self.save_to_blackbaze_bucket(data)

	def save_local(self, data: pd.DataFrame) -> None:
		"""Save data to the local environment."""
		news_directory = self.current_directory.joinpath("datasets", "today_news")
		data.to_csv(news_directory.joinpath(f"{self.date}-news-clusters.csv"))

	def save_to_blackbaze_bucket(self, data: pd.DataFrame) -> None:
		"""Save data to a cloud bucket."""
		today = datetime.now().strftime("%Y-%m-%d")
		with NamedTemporaryFile(delete=True, suffix=".csv") as temp_file:
			data.to_csv(temp_file)
			self.cloud_storage.upload_file(
				bucket_name="congonews-clusters",
				file_path=temp_file.name,
				file_name=f"news-clusters-{today}-to-{self.date}.csv",
				metadata={"date": datetime.now().strftime("%Y-%m-%d")},
			)
			logger.info(f"Saved {self.date} news to the cloud bucket")
