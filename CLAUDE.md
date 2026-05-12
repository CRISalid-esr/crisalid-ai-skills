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
| `crisalid-restricted` | `get-crisalid-schema`, `list-person-publications`, `list-person-concepts`, `search-person-by-name` |
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

## Linting

Run ruff before every commit:

```bash
uv run ruff check .
```

## Running tests

Tests require running processes outside the IDE:
1. Neo4j on port 7688 (Docker: `neo4j:5-community`, APOC enabled, `NEO4J_AUTH=none`)
2. Toolbox running against `.env.test`: `set -a && source .env.test && set +a && ./toolbox --config tools.yaml`
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

The graph loosely follows the **CERIF-2** data model (an emerging RDF model), but without neosemantics or any strict RDF-compliant approach.

### Data provenance and internal entities

Our institution created **ResearchUnit** and **Institution** nodes from its internal databases, and **Person** nodes (`external: false`) from its people registry. Internal persons are linked:
- `(p:Person)-[:MEMBER_OF]->(ru:ResearchUnit)`
- `(p:Person)-[:EMPLOYED_AT]->(inst:Institution)`
- `(p:Person)-[:HAS_IDENTIFIER]->(id:AgentIdentifier)`

**AgentIdentifier** nodes were used to harvest publications from external bibliographic databases (HAL, OpenAlex, ScanR, IdRef). The harvesting process created **SourceRecord** nodes linked to persons via `(sr:SourceRecord)-[:HARVESTED_FOR]->(p:Person)`.

### Source layer

SourceRecords are connected to a source layer representing bibliographic references exactly as they appear in external databases: **SourceContribution**, **SourceIdentifier**, **SourceIssue**, **SourceJournal**, etc. The `Source` prefix is a local convention — it does NOT map to the CERIF-2 `Source` concept.

### Documents

**Document** nodes — with more specific labels such as `Book`, `BookChapter`, `Article`, `JournalArticle`, etc. — are created by a merging algorithm from SourceRecords. Key document relations:
- `(doc:Document)-[:HAS_TITLE]->(l:Literal {type: 'document_title'})`
- `(doc:Document)-[:HAS_ABSTRACT]->(l:Literal {type: 'document_abstract'})`
- `(doc:Document)-[:PUBLISHED_IN]->(j:Journal)` — for `JournalArticle` nodes; the relation carries `issue`, `page`, `volume` attributes

### Concepts

`Concept` nodes are linked to documents via `(doc:Document)-[:HAS_SUBJECT]->(concept:Concept)`. Two kinds:
- **Genuine SKOS concepts**: have a `uri` (identical to `uid`) and label relations: `(concept)-[:HAS_PREF_LABEL]->(l:Literal {type: 'concept_pref_label'})`, `(concept)-[:HAS_ALT_LABEL]->(l:Literal {type: 'concept_alt_label'})`
- **Free-text keywords** (legacy): no `uri`, carry only a `prefLabel` property directly on the node

**Distinction from taxonomy terms**: Domains, Fields, Sub-fields and Topics (OpenAlex taxonomy) are also typed as `Concept`. Topics are linked to publications via `HAS_TOPICS` (not `HAS_SUBJECT`); higher levels are not yet linked.

### Contributions and co-authors

Co-authors are identified through `(doc:Document)-[:HAS_CONTRIBUTION]->(c:Contribution)` and `(p:Person)-[:HAS_CONTRIBUTION]->(c:Contribution)`. A **Contribution** carries:
- **roles**: one or more strings using the Library of Congress relators vocabulary, e.g. `http://id.loc.gov/vocabulary/relators/aut` (author), `http://id.loc.gov/vocabulary/relators/edt` (editor)
- The contributing **Person** — often `external: true`. External persons carry `display_name` and optionally `display_name_variants`, but have no `MEMBER_OF` or `EMPLOYED_AT` relations

Co-author affiliations with external research structures are found **at the Contribution level** via `(c:Contribution)-[:HAS_AFFILIATION_STATEMENT]->(org:AuthorityOrganization)`. These are derived from co-author signatures in external databases — accuracy cannot be verified, but they are the only available data on inter-institutional collaborations.

### External organizations (AuthorityOrganization)

**HAS_AFFILIATION_STATEMENT** points to **AuthorityOrganization** nodes (not to `Institution` or `ResearchUnit`). External organizations are reconstructed from registries such as RoR and represented in two subtypes:
- **AuthorityOrganizationState**: an organization at a given point in time, with identifiers (RoR, IdRef, HAL)
- **AuthorityOrganizationRoot**: groups multiple `AuthorityOrganizationState` nodes via `HAS_STATE` relations, for organizations that changed names, merged, or split

When an affiliation cannot be precisely matched to a specific `AuthorityOrganizationState`, it links to an `AuthorityOrganizationRoot` instead. `AuthorityOrganization` nodes carry `display_name` values **directly** (no intermediate `Literal` node).

### Person name properties

`Person` nodes carry `display_name` (canonical string) and `display_name_variants` (list). A full-text index `person_fulltext_name` covers both with the `standard-no-stop-words` analyzer — use `CALL db.index.fulltext.queryNodes('person_fulltext_name', ...)` for fuzzy name search.

### ResearchUnit name storage

`ResearchUnit` nodes carry only `uid` and `acronym` directly. The human-readable name is a `Literal` node reached via `(ru:ResearchUnit)-[:HAS_NAME]->(name:Literal)`. This differs from `AuthorityOrganization`, which stores `display_name` as a property directly on the node.

### Journal nodes

`Journal` nodes carry a `titles` attribute (list of strings), a `publisher` attribute, and an `issn_l` attribute (the linking ISSN that groups its various ISSNs). Individual ISSNs are **JournalIdentifier** nodes linked via `(j:Journal)-[:HAS_IDENTIFIER]->(ji:JournalIdentifier)`.

### Literals

Almost all strings in the graph are represented as **Literal** nodes with:
- `value`: the string content
- `language`: 2-letter ISO 639-1 code, or `"ul"` for undetermined language
- `type`: the label type (e.g. `"concept_pref_label"`, `"concept_alt_label"`, `"document_title"`, `"document_abstract"`)
