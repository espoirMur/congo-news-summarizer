from typing import Dict, List

from jinja2 import Template

from src.llm.prompts import SUMMARIZATION_PROMPT_TEMPLATE
from src.shared.logger import setup_logger

logger = setup_logger("llm_generator")


class BaseGenerator:
	def generate_chat_input(
		self, template_values: dict, prompt_template: str = SUMMARIZATION_PROMPT_TEMPLATE
	) -> List[Dict]:
		"""generate the prompt to be used for the chat input"""

		template = Template(prompt_template)
		user_message = template.render(**template_values)

		chat_input = [
			{"role": "system", "content": self.system_prompt},
			# just try to limit the characters
			{"role": "user", "content": user_message[:2000]},
		]

		return chat_input

	def apply_chat_template(self, messages, add_generation_prompt=False):
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

	def run(
		self, template_values: dict, prompt_template: str = SUMMARIZATION_PROMPT_TEMPLATE
	) -> str:
		"""Generate response using the Llamma.cpp api"""
		chat_input = self.generate_chat_input(template_values, prompt_template)
		chat_tokens = self.apply_chat_template(messages=chat_input, add_generation_prompt=True)
		logger.info("Chat tokens generated", chat_tokens)
		raise NotImplementedError("Subclasses must implement this method")
