# CLAUDE.md

@~/.claude/AGENT.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

CRISalid manages data through a Neo4j knowledge graph (Cypher + Apollo GraphQL).  
In the current repository crisalid-ai-skills, the mcp-toolbox module provides two levels of access:
- `crisalid-unrestricted` toolset with a generic `execute-cypher-readonly` tool for ad-hoc queries
- `crisalid-restricted` toolset with curated tools like `list-person-publications` 

## Repository overview

MCP Toolbox tools and sample clients for the CRISalid institutional knowledge graph (Neo4j). Key areas:

- `mcp-toolbox/` — toolbox config files (`tools.yaml` no-auth, `tools-auth.yaml` with Keycloak OIDC), `Dockerfile`, `.env.sample`
- `samples/` — Python client scripts using `toolbox-langchain` (no LLM, direct tool invocation)
- `tests/` — pytest integration tests against a dedicated test Neo4j instance (port 7688)
- `.github/workflows/` — CI (lint + tests on PRs), CD (Docker push to DockerHub on dev-main)

## Toolsets

| Toolset | Tools |
|---|---|
| `crisalid-restricted` | `get-crisalid-schema`, `list-person-publications` |
| `crisalid-unrestricted` | above + `execute-cypher-readonly` |

## Authentication

- `tools.yaml` — no auth, used for local dev and tests
- `tools-auth.yaml` — Keycloak OIDC (`type: generic`), `authRequired` on curated tools
- Auth service name: `crisalid-keycloak`, audience: `crisalid-graph-mcp` (hardcoded in yaml)
- **Server-side env var**: `KEYCLOAK_ISSUER` only — the toolbox never needs client credentials
- **Client-side env vars**: `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`, `KEYCLOAK_SSL_VERIFY` — used by sample scripts only
- Clients use `client_credentials` grant; token getter passed via `auth_token_getters` to `aload_toolset()`

## Docker

- Image name on DockerHub: `crisalidesr/crisalid-neo4j-mcp-toolbox`
- Toolbox listens on `0.0.0.0:5000` (required for Docker port mapping — default is `127.0.0.1`)
- No entrypoint — plain `CMD`. For self-signed KC cert in local dev, override entrypoint with `update-ca-certificates && toolbox ...`

## Running tests

Tests require running processes outside the IDE:
1. Neo4j on port 7688 (Docker: `neo4j:5-community`, APOC enabled, `NEO4J_AUTH=none`)
2. Toolbox running against `.env.test`: `set -a && source mcp-toolbox/.env.test && set +a && ./toolbox --config tools.yaml`
Don't try to start these from the IDE — just check connectivity before running tests and ask the user to start them if they are not running.

```bash
uv run pytest tests/ -v
```

Fixtures are auto-loaded from `tests/fixtures/graph.cypher` on each run.

## MCP protocol version

All sample clients must use `Protocol.MCP_LATEST` (toolbox v1.1.0+ requires it):

```python
from toolbox_core.protocol import Protocol
ToolboxClient(TOOLBOX_URL, protocol=Protocol.MCP_LATEST)
```

## Neo4j graph model notes

The graph loosely follows the **CERIF-2** data model (an emerging RDF model), but without neosemantics or any strict RDF-compliant approach. Several important conventions:

- **External organisations** are modelled as `AuthorityOrganization` nodes with a current `AuthorityOrganizationState`. When an external organisation has several historical states, they are grouped under an `AuthorityOrganizationRoot`.
- **External people** (not belonging to our university) are `Person` nodes tagged with `external=true`.
- **Documents** (publications) are assembled from `SourceRecord` nodes harvested from various bibliographic platforms (HAL, ScanR, etc.).
- The **source layer** uses a `Source` prefix for convenience nodes: `SourceJournal`, `SourcePersonIdentifier`, `SourceContribution`, etc. This prefix is a local convention — it does NOT map to the CERIF-2 `Source` concept.
