import logging
from typing import Any, Dict, List, Literal

from haystack.dataclasses.document import Document
from haystack.document_stores.errors import DocumentStoreError, DuplicateDocumentError
from haystack.document_stores.types import DuplicatePolicy
from haystack.utils.auth import Secret
from haystack_integrations.document_stores.pgvector import PgvectorDocumentStore
from psycopg import Error, IntegrityError, connect
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier
from psycopg.sql import Literal as SQLLiteral

logger = logging.getLogger(__name__)


class MyPgVectorDocumentStore(PgvectorDocumentStore):
	"""
	This is a  custom pg document stores that extends the PgvectorDocumentStore.
	I will reimplement the write document method to use my custom insert statement.
	"""

	def __init__(
		self,
		*,
		connection_string: Secret,
		table_name: str = "haystack_documents",
		language: str = "english",
		embedding_dimension: int = 768,
		vector_function: Literal["cosine_similarity"]
		| Literal["inner_product"]
		| Literal["l2_distance"] = "cosine_similarity",
		recreate_table: bool = False,
		search_strategy: Literal["exact_nearest_neighbor"]
		| Literal["hnsw"] = "exact_nearest_neighbor",
		hnsw_recreate_index_if_exists: bool = False,
		hnsw_index_creation_kwargs: Dict[str, int] | None = None,
		hnsw_index_name: str = "haystack_hnsw_index",
		hnsw_ef_search: int | None = None,
		keyword_index_name: str = "haystack_keyword_index",
		sql_insert_string: str = None,
		sql_update_string: str = None,
	):
		super().__init__(
			connection_string=connection_string,
			table_name=table_name,
			language=language,
			embedding_dimension=embedding_dimension,
			vector_function=vector_function,
			recreate_table=recreate_table,
			search_strategy=search_strategy,
			hnsw_recreate_index_if_exists=hnsw_recreate_index_if_exists,
			hnsw_index_creation_kwargs=hnsw_index_creation_kwargs,
			hnsw_index_name=hnsw_index_name,
			hnsw_ef_search=hnsw_ef_search,
			keyword_index_name=keyword_index_name,
		)

		self.sql_insert_string = sql_insert_string
		self.update_string = sql_update_string

	def write_documents(
		self,
		documents: List[Document],
		policy: DuplicatePolicy = DuplicatePolicy.OVERWRITE,
	) -> int:
		"""
		Writes documents to the document store.

		:param documents: A list of Documents to write to the document store.
		:param policy: The duplicate policy to use when writing documents.
		:raises DuplicateDocumentError: If a document with the same id already exists in the document store
		     and the policy is set to `DuplicatePolicy.FAIL` (or not specified).
		:returns: The number of documents written to the document store.
		"""

		if len(documents) > 0:
			if not isinstance(documents[0], Document):
				msg = "param 'documents' must contain a list of objects of type Document"
				raise ValueError(msg)

		if policy == DuplicatePolicy.NONE:
			policy = DuplicatePolicy.FAIL

		db_documents = self._from_haystack_to_pg_documents(documents)

		sql_insert = SQL(self.sql_insert_string).format(table_name=Identifier(self.table_name))
		logger.info("Inserting documents into table %s", sql_insert)

		if policy == DuplicatePolicy.OVERWRITE:
			sql_insert += SQL(self.update_string)
		elif policy == DuplicatePolicy.SKIP:
			sql_insert += SQL("ON CONFLICT DO NOTHING")

		sql_insert += SQL(" RETURNING id")
		try:
			self.cursor.executemany(sql_insert, db_documents, returning=True)
		except IntegrityError as ie:
			self.connection.rollback()
			raise DuplicateDocumentError from ie
		except Error as e:
			self.connection.rollback()
			error_msg = (
				"Could not write documents to PgvectorDocumentStore. \n"
				"You can find the SQL query and the parameters in the debug logs."
			)
			raise DocumentStoreError(error_msg) from e

		# get the number of the inserted documents, inspired by psycopg3 docs
		# https://www.psycopg.org/psycopg3/docs/api/cursors.html#psycopg.Cursor.executemany
		written_docs = 0
		while True:
			if self.cursor.fetchone():
				written_docs += 1
			if not self.cursor.nextset():
				break

		return written_docs

	@staticmethod
	def _from_haystack_to_pg_documents(documents: List[Document]) -> List[Dict[str, Any]]:
		"""
		Internal method to convert a list of Haystack Documents to a list of dictionaries that can be used to insert
		documents into the PgvectorDocumentStore.

		article_id INTEGER,
		chunk TEXT,
		chunk_vector VECTOR(768),
		"""

		db_documents = []
		for document in documents:
			db_document = {
				"article_id": document.meta["article_id"],
				"chunk": document.content,
				"chunk_vector": document.embedding,
			}
			db_documents.append(db_document)

		return db_documents

	def _create_keyword_index_if_not_exists(self):
		"""
		Internal method to create the keyword index if not exists.
		"""
		index_exists = bool(
			self._execute_sql(
				"SELECT 1 FROM pg_indexes WHERE tablename = %s AND indexname = %s",
				(self.table_name, self.keyword_index_name),
				"Could not check if keyword index exists",
			).fetchone()
		)

		sql_create_index = SQL(
			"CREATE INDEX {index_name} ON {table_name} USING GIN (to_tsvector({language}, chunk))"
		).format(
			index_name=Identifier(self.keyword_index_name),
			table_name=Identifier(self.table_name),
			language=SQLLiteral(self.language),
		)

		if not index_exists:
			self._execute_sql(sql_create_index, error_msg="Could not create keyword index on table")

	def _create_connection(self):
		conn_str = self.connection_string.resolve_value() or ""
		connection = connect(conn_str)
		connection.autocommit = True

		self._connection = connection
		self._cursor = self._connection.cursor()
		self._dict_cursor = self._connection.cursor(row_factory=dict_row)

		# Init schema
		if self.recreate_table:
			self.delete_table()
		self._create_table_if_not_exists()
		self._create_keyword_index_if_not_exists()

		if self.search_strategy == "hnsw":
			self._handle_hnsw()

		return self._connection

	def _create_table_if_not_exists(self):
		"""
		Creates the table to store Haystack documents if it doesn't exist yet.
		"""

		TABLE_CREATION_STRING = """
        CREATE TABLE IF NOT EXISTS article_embeddings (
            id SERIAL PRIMARY KEY,
            article_id INTEGER,
            chunk TEXT,
            chunk_vector VECTOR(768),
            CONSTRAINT fk_article_id FOREIGN KEY (article_id) REFERENCES article(id)
        );
        """

		create_sql = SQL(TABLE_CREATION_STRING)

		self._execute_sql(create_sql, error_msg="Could not create table in PgvectorDocumentStore")
