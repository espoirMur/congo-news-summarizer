from pydantic import BaseModel
from pydantic.v1.schema import schema


class SummarySchemas(BaseModel):
	title: str
	summary: str

	def to_json_schema(self) -> dict:
		model_schema = schema([self.__class__], ref_template="#/definitions/{model}")
		return model_schema
