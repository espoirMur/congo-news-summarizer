import json
from typing import Dict, List

import requests
from jinja2 import Template

from src.shared.logger import setup_logger

SUMMARIZATION_PROMPT_TEMPLATE = """
Give a short summary 2 to 3 sentences in french of the following document:
{{content}}
 Describes it in a style of a french new paper reporters.

Don't summarize each document separately, the content in all the documents should be summarized.

The summary should be in french not in English
"""

logger = setup_logger("cluster_modeler")


class LLamaCppGeneratorComponent:
	"""
	This class is responsible for generating response using the Llamma.cpp api

	"""

	def __init__(
		self,
		api_url: str,
		prompt: str,
	) -> None:
		self.api_url = api_url
		self.prompt = prompt

	def generate_chat_input(
		self, template_values: dict, prompt_template: str = SUMMARIZATION_PROMPT_TEMPLATE
	) -> List[Dict]:
		"""generate the prompt to be used for the chat input"""

		template = Template(prompt_template)
		prompt = template.render(**template_values)

		chat_input = [
			{"role": "system", "content": self.prompt},
			{"role": "user", "content": prompt},
		]

		return chat_input

	def generate_response(self, prompt: str) -> str:
		"""
		This function generates response using the Llamma.cpp api

		Args:
		    prompt (str): The prompt to generate response from

		Returns:
		    str: The generated response
		"""
		headers = {
			"Content-Type": "application/json",
		}

		data = {
			"prompt": prompt,
			"n_predict": 768,
			"temperature": 0.3,
			"top_k": 40,
			"top_p": 0.90,
			"stopped_eos": True,
			"repeat_penalty": 1.05,
			"stop": [
				"assistant",
				"<|im_end|>",
			],
			"seed": 42,
		}

		json_data = json.dumps(data)

		# Send the POST request
		try:
			response = requests.post(
				f"{self.api_url}/completion",
				headers=headers,
				data=json_data,
				timeout=300,
			)
			return response.json()["content"]
		except requests.exceptions.RequestException as e:
			logger.error(e)
			return None

	def run(
		self, template_values: dict, prompt_template: str = SUMMARIZATION_PROMPT_TEMPLATE
	) -> str:
		"""Generate response using the Llamma.cpp api"""
		chat_input = self.generate_chat_input(template_values, prompt_template)
		chat_tokens = self.tokenizer.apply_chat_template(
			chat_input, tokenize=False, add_generation_prompt=True
		)
		response = self.generate_response(chat_tokens)
		return response

	def _ping_api(self) -> bool:
		"""Ping the Llamma.cpp api to check if it is up"""
		try:
			response = requests.get(f"{self.api_url}/health", timeout=20)
			return response.status_code == 200 and response.json()["status"] == "ok"
		except requests.exceptions.RequestException as e:
			logger.error(e)
			return False

	def generate_chat_prompt(self, messages, add_generation_prompt=False):
		"""
		Generates a structured prompt based on a list of message dictionaries.

		Args:
		messages (list): A list of dictionaries, each with 'role' and 'content' keys.
		add_generation_prompt (bool): Whether to add a final assistant prompt block.

		Returns:
		str: The formatted prompt.
		"""
		chat_template = "{%- if tools %}\n    {{- '<|im_start|>system\\n' }}\n    {%- if messages[0]['role'] == 'system' %}\n        {{- messages[0]['content'] }}\n    {%- else %}\n        {{- 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.' }}\n    {%- endif %}\n    {{- \"\\n\\n# Tools\\n\\nYou may call one or more functions to assist with the user query.\\n\\nYou are provided with function signatures within <tools></tools> XML tags:\\n<tools>\" }}\n    {%- for tool in tools %}\n        {{- \"\\n\" }}\n        {{- tool | tojson }}\n    {%- endfor %}\n    {{- \"\\n</tools>\\n\\nFor each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:\\n<tool_call>\\n{\\\"name\\\": <function-name>, \\\"arguments\\\": <args-json-object>}\\n</tool_call><|im_end|>\\n\" }}\n{%- else %}\n    {%- if messages[0]['role'] == 'system' %}\n        {{- '<|im_start|>system\\n' + messages[0]['content'] + '<|im_end|>\\n' }}\n    {%- else %}\n        {{- '<|im_start|>system\\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\\n' }}\n    {%- endif %}\n{%- endif %}\n{%- for message in messages %}\n    {%- if (message.role == \"user\") or (message.role == \"system\" and not loop.first) or (message.role == \"assistant\" and not message.tool_calls) %}\n        {{- '<|im_start|>' + message.role + '\\n' + message.content + '<|im_end|>' + '\\n' }}\n    {%- elif message.role == \"assistant\" %}\n        {{- '<|im_start|>' + message.role }}\n        {%- if message.content %}\n            {{- '\\n' + message.content }}\n        {%- endif %}\n        {%- for tool_call in message.tool_calls %}\n            {%- if tool_call.function is defined %}\n                {%- set tool_call = tool_call.function %}\n            {%- endif %}\n            {{- '\\n<tool_call>\\n{\"name\": \"' }}\n            {{- tool_call.name }}\n            {{- '\", \"arguments\": ' }}\n            {{- tool_call.arguments | tojson }}\n            {{- '}\\n</tool_call>' }}\n        {%- endfor %}\n        {{- '<|im_end|>\\n' }}\n    {%- elif message.role == \"tool\" %}\n        {%- if (loop.index0 == 0) or (messages[loop.index0 - 1].role != \"tool\") %}\n            {{- '<|im_start|>user' }}\n        {%- endif %}\n        {{- '\\n<tool_response>\\n' }}\n        {{- message.content }}\n        {{- '\\n</tool_response>' }}\n        {%- if loop.last or (messages[loop.index0 + 1].role != \"tool\") %}\n            {{- '<|im_end|>\\n' }}\n        {%- endif %}\n    {%- endif %}\n{%- endfor %}\n{%- if add_generation_prompt %}\n    {{- '<|im_start|>assistant\\n' }}\n{%- endif %}\n"
		template = Template(chat_template)
		return template.render(messages=messages, add_generation_prompt=add_generation_prompt)
