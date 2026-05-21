# MCP Server Specification

## Overview

An MCP server that provides today's Congo news, clustered and returned as JSON.

## Functionality

### Tool: `get_today_news_clustered`

**Purpose**: Fetch today's news, cluster them by topic, and return a JSON representation.

**Parameters**:
- `environment` (optional, default: `"local"`): Environment name (`"local"` or `"prod"`)
- `days_ago` (optional, default: `1`): Number of days to look back

**Returns**: JSON object with the following structure:

```json
{
  "date": "2026-05-18",
  "clusters": [
    {
      "cluster_id": 1,
      "articles": [
        {
          "database_id": "...",
          "title": "Article Title",
          "content": "Article content...",
          "posted_at": "2026-05-18T10:30:00",
          "url": "https://...",
          "label": 1
        }
      ]
    }
  ]
}
```

**Process**:
1. Pull news from database for the given date range
2. Compute embeddings using `dunzhang/stella_en_400M_v5`
3. Cluster using hierarchical clustering with silhouette score optimization
4. Filter clusters with more than one document (meaningful clusters)
5. Format as JSON

## Implementation

- **Location**: `src/mcp_server/server.py`
- **Framework**: FastMCP (already in dependencies)
- **Reuse**: Leverage existing `DataPuller`, `EmbeddingsComputer`, `HierarchicalClusterModeler`

## Configuration

Uses the same `.env_local` / `.env_prod` pattern as the existing pipeline:
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`
- Loaded via `python-dotenv` from `.env_{environment}`

## CLI

The server can be run directly:
```bash
python -m src.mcp_server.server
```