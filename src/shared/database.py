from collections.abc import Generator
from typing import Dict, List

from psycopg2 import connect
from psycopg2.extras import NamedTupleCursor
from sqlalchemy.engine import Connection


def generate_database_connection(
	database_credentials: Dict,
) -> Connection:
	database_connection = connect(**database_credentials)
	return database_connection


def execute_query(database_connection, query, params=None) -> Generator[List[NamedTupleCursor]]:
	"""
	Execute a database query using the provided database connection.

	Args:
	    database_connection: A connection to the database.
	    query: The SQL query to execute.
	    params: Optional parameters to pass to the query.

	Returns:
	    A list of query results, or None if an error occurs.
	"""
	with database_connection.cursor(cursor_factory=NamedTupleCursor) as cursor:
		try:
			cursor.execute(query, params)
			return cursor.fetchall()
		except Exception as e:
			raise ValueError(
				f"an execution error occurred for query {query!r} with params {params!r}"
			) from e
