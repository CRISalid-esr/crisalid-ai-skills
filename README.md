# crisalid-ai-skills

Tooling and skills for AI-powered access to the CRISalid institutional knowledge graph. This repository provides MCP-compatible tools that wrap curated queries against the CRISalid Neo4j graph, making it easy to integrate structured academic data (researchers, publications, topics, organisations) into LLM-based agents and workflows.

---

## MCP Toolbox

Tools are served via [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox), a lightweight server that exposes named Cypher queries as MCP tools. Two toolsets are available:

| Toolset | Tools | Use case |
|---|---|---|
| `crisalid-restricted` | `get-crisalid-schema` | Clients needing schema discovery only |
| `crisalid-unrestricted` | `get-crisalid-schema`, `execute-cypher-readonly` | Advanced agents with ad-hoc Cypher access |

### Run the MCP server

First, install the toolbox. Two options:

**Via npx (no installation required):**
```bash
npx @toolbox-sdk/server --config tools.yaml
```

**Via binary (Linux):** download from [mcp-toolbox.dev](https://mcp-toolbox.dev/documentation/introduction/) and place the binary in `mcp-toolbox/`.

Then set your environment variables and start the server:

```bash
cd mcp-toolbox
set -a && source .env && set +a   # set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
./toolbox --config tools.yaml
```

The server listens on `http://127.0.0.1:5000` by default.

Add `--ui` to also launch a web interface for browsing and manually invoking tools:

```bash
./toolbox --config tools.yaml --ui
# UI available at http://127.0.0.1:5000/ui
```

### Run a client

Sample scripts using [toolbox-langchain](https://pypi.org/project/toolbox-langchain/) are in `samples/`. They connect to the running server and invoke tools directly, without an LLM.

```bash
# Load the restricted toolset and call get-crisalid-schema
uv run python samples/load_restricted_toolset.py

# Load the unrestricted toolset and run a sample Cypher query
uv run python samples/load_unrestricted_toolset.py
```

### Run the tests

Tests require a dedicated Neo4j instance on port 7688 (separate from the production database) and the toolbox server running against it.

**1. Start the test Neo4j container**

```bash
docker run --publish=7475:7474 --publish=7688:7687 \
  --env=NEO4J_AUTH=none \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -e NEO4J_apoc_import_file_use__neo4j__config=true \
  -e NEO4JLABS_PLUGINS='["apoc"]' \
  neo4j:5-community
```

**2. Start the toolbox server against the test database**

```bash
cd mcp-toolbox
set -a && source .env.test && set +a   # points to bolt://localhost:7688, no real credentials
npx @toolbox-sdk/server --config tools.yaml
# or: ./toolbox --config tools.yaml  (if using the downloaded binary)
```

**3. Run the test suite**

```bash
uv run pytest tests/ -v
```

The test session automatically wipes and reloads fixture data (`tests/fixtures/graph.cypher`) into the test Neo4j instance on each run.

### Lint

Python code is linted with [ruff](https://docs.astral.sh/ruff/). Run it locally before pushing:

```bash
uv run ruff check .      # check for issues
uv run ruff check --fix . # auto-fix where possible
```

The same check runs automatically on every pull request via GitHub Actions.
