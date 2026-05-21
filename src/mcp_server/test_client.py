import asyncio

from fastmcp import Client

client = Client("http://localhost:9091/mcp")


async def call_tool(days_ago: int):
	async with client:
		result = await client.call_tool("get_today_news_clustered", {"days_ago": days_ago})
		print(result)


asyncio.run(call_tool(1))
