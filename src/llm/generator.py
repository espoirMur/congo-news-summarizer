import json

import requests
from tenacity import retry, stop_after_attempt, wait_fixed

from src.llm.base import BaseGenerator
from src.schemas import SummarySchemas
from src.shared.logger import setup_logger

logger = setup_logger("llm_generator")


class LLamaCppGeneratorComponent(BaseGenerator):
	"""
	This class is responsible for generating response using the Llamma.cpp api
	"""

	def __init__(
		self,
		api_url: str,
		api_key: str = None,
		temperature: float = 0.3,
		n_predict: int = 768,
	) -> None:
		self.api_url = api_url
		self.system_prompt = " Vous etes un journaliste d'acutualité congolaise."
		self.api_key = api_key
		self.temperature = temperature
		self.n_predict = n_predict
		self.headers = {
			"Content-Type": "application/json",
			"Authorization": f"Bearer {self.api_key}" if self.api_key else "",
		}

	@retry(wait=wait_fixed(30), stop=stop_after_attempt(5), reraise=True)
	def generate_response(self, chat_content: str) -> str:
		"""
		This function generates response using the Llamma.cpp api
		"""
		data = {
			"prompt": chat_content,
			"n_predict": self.n_predict,
			"temperature": self.temperature,
			"top_k": 40,
			"top_p": 0.90,
			"stopped_eos": True,
			"repeat_penalty": 1.05,
			"cache_prompt": False,
			"stop": [
				"assistant",
				"<|im_end|>",
			],
			"seed": 42,
			"json_schema": SummarySchemas.model_json_schema(),
		}

		json_data = json.dumps(data)
		try:
			response = requests.post(
				f"{self.api_url}/completion",
				headers=self.headers,
				data=json_data,
				timeout=300,
			)
			response.raise_for_status()
		except requests.exceptions.RequestException as err:
			logger.error(f"Llama.cpp API request failed: {err}")
			raise err

		return response.json()["content"]

	def run(self, template_values: dict, prompt_template: str) -> str:
		"""Generate response using the Llama.cpp api"""
		chat_input = self.generate_chat_input(template_values, prompt_template)
		chat_tokens = self.apply_chat_template(messages=chat_input, add_generation_prompt=True)
		response = self.generate_response(chat_tokens)
		return response

	@retry(wait=wait_fixed(60), stop=stop_after_attempt(10), reraise=True)
	def _ping_api(self) -> bool:
		"""Ping the Llama.cpp api to check if it is up"""
		try:
			response = requests.get(f"{self.api_url}/ping", timeout=300, headers=self.headers)  #
			response.raise_for_status()
			return response.status_code == 200 and response.json().get("status") == "ok"
		except requests.exceptions.RequestException as e:
			logger.error(f"Llama.cpp ping failed: {e}")
			return False
