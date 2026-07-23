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

The MCP toolbox provides multiple **named toolsets** to control which tools are available in different contexts:

| Toolset | Purpose | Tools |
|---|---|---|
| `crisalid-restricted` | Curated CRISalid tools, no raw Cypher | `get-crisalid-schema`, `list-person-publications`, `list-person-concepts`, `search-person-by-name` |
| `crisalid-unrestricted` | Unrestricted CRISalid access | above + `execute-cypher-readonly` |
| `sorbobot-restricted` | SorboBot domain analysis tools, no raw Cypher | `sorbobot-search-domains`, `sorbobot-get-domain-authors`, `sorbobot-get-parent-domains`, `sorbobot-get-person-expertise` |
| `sorbobot-full` | Unrestricted SorboBot access | above + `sorbobot-execute-cypher-readonly` |

**Why multiple toolsets?**
- **Separation of concerns**: CRISalid tools (persons, publications, concepts) vs. SorboBot tools (domain/expertise hierarchy)
- **Access control**: Clients can load `restricted` toolsets without access to raw Cypher (`execute-cypher-readonly`), limiting to curated queries only
- **Flexibility**: Applications can choose which domain (CRISalid or SorboBot) and which access level they need

## SorboBot Domain Analysis Tools

SorboBot provides specialized tools for navigating domain and expertise hierarchies in the knowledge graph. Designed for domain analysis, researcher discovery, and expertise mapping.

### Available Tools

| Tool | Purpose | Parameters |
|---|---|---|
| `sorbobot-search-domains` | Find domains by keyword with semantic similarity | `keyword` (str), `limit` (int), `similarity_threshold` (float, 0.0–1.0) |
| `sorbobot-get-domain-authors` | List researchers working in a domain | `domain` (str), `limit` (int) |
| `sorbobot-get-parent-domains` | Navigate domain hierarchy upward | `domain` (str) |
| `sorbobot-get-person-expertise` | List domains where a person has published | `person_name` (str), `limit` (int) |
| `sorbobot-execute-cypher-readonly` | Direct Cypher query access (unrestricted only) | `query` (str), `params` (dict) |

### Use Cases

- **Domain discovery**: Search domains by keyword, find researchers working in a domain
- **Expertise mapping**: Identify where a researcher has published, navigate domain hierarchies
- **Knowledge graph navigation**: Use restricted toolsets for curated domain analysis, or unrestricted for ad-hoc queries

### Sample Client Usage

```python
from toolbox_langchain import aload_toolset

# Load the restricted SorboBot toolset (no raw Cypher)
toolset = await aload_toolset('sorbobot-restricted', client=toolbox_client)

# Invoke tools
domains = await toolset.tools['sorbobot-search-domains'].ainvoke({
    'keyword': 'machine learning',
    'limit': 5,
    'similarity_threshold': 0.7
})

# Or load the full toolset to access execute-cypher-readonly
full_toolset = await aload_toolset('sorbobot-full', client=toolbox_client)
```

See `samples/` for complete examples.

## Authentication

- `tools.yaml` — no auth, used for local dev and tests
- `tools-auth.yaml` — Keycloak OIDC (`type: generic`), `authRequired` on curated tools
- Auth service name: `crisalid-keycloak`, audience: `crisalid-graph-mcp` (hardcoded in yaml)
- **Server-side env var**: `KEYCLOAK_ISSUER` only — the toolbox never needs client credentials
- **Client-side env vars**: `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_CLIENT_SECRET`, `KEYCLOAK_SSL_VERIFY` — used by sample scripts only
- Clients use `client_credentials` grant; token getter passed via `auth_token_getters` to `aload_toolset()`

### Configuration Synchronization (Important)

**MCP limitation**: The toolbox server can only load a single configuration file (`tools.yaml` OR `tools-auth.yaml`). Therefore, **both files must be kept in sync**:

1. **Any tool added to `tools.yaml`** must also be added to `tools-auth.yaml`
2. **All toolsets must be identical** in both files (names, tools lists, order)
3. **Only difference**: In `tools-auth.yaml`, add `authRequired: [crisalid-keycloak]` to curated tools
4. **Recommended workflow**:
   - Maintain `tools.yaml` as the canonical version (all tools + toolsets)
   - Mirror all content to `tools-auth.yaml`, adding auth annotations only
   - Run tests against `tools.yaml` locally, then switch to `tools-auth.yaml` on the deployed server

**Why duplication?** The MCP SDK does not support YAML factorization (includes, anchors, references). Complete duplication is necessary to avoid inconsistencies between environments.

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

### OrganizationUnit hierarchy

Our institution built a hierarchy of **OrganizationUnit** nodes from its internal databases and national registries. Every `OrganizationUnit` node carries the `OrganizationUnit` label plus one or more specific labels indicating its position in the taxonomy:

| Specific labels | `generic_type` | Typical `national_type` | Description |
|---|---|---|---|
| `Institution` | `institution` | `UNIV`, `EPE`, `COMUE`, `EPST`, `GE` | University, EPE, COMUE, EPST, or grand établissement |
| `InstitutionSubdivision` | `institution_subdivision` | `UFR`, `FAC`, `DEP` | A component of an institution (faculty, department…) |
| `Unit` + `ResearchUnit` | `unit` | `UMR`, `UAR`, `UR`, `IRL` | A research unit |
| `Unit` + `SupportUnit` | `unit` | — | A support unit |
| `Unit` + `AdministrativeUnit` | `unit` | — | An administrative unit |
| `Unit` + `TeachingUnit` | `unit` | — | A teaching unit |
| `UnitSubdivision` | `unit_subdivision` | — | A subdivision of a unit (research axis…) |
| `Team` | `team` | `TEAM`, `THEME` | A research team inside a unit |

Each `OrganizationUnit` node has a `uid` (e.g. `local-U123`, `uai-02345`, `ror-xxx`), a `generic_type`, and optionally a `national_type`. It also has an `external` attribute:
- `external: false` — created from the institution's own directory (authoritative data)
- `external: true` — auto-created from a national registry to satisfy a relationship target; not directly managed by our institution

**Three-tier typing**: `generic_type` (broad classification per the French *cadre de références des structures de recherche*), `national_type` (officially validated, e.g. `UMR`, `UNIV`, `UFR`), and **local types** (institution-specific labels stored as Literal nodes via `HAS_LOCAL_TYPE`, type `"organization_local_type"`).

**Name/label storage** on `OrganizationUnit` nodes — via Literal or TextLiteral nodes, not direct properties:
- `HAS_LONG_LABEL` → Literal of type `"organization_long_label"` (full name)
- `HAS_SHORT_LABEL` → Literal of type `"organization_short_label"` (acronym)
- `HAS_DESCRIPTION` → TextLiteral (free-text description)

**Relations between OrganizationUnit nodes**:
- `PART_OF` — structural inclusion (e.g. faculty inside a university, team inside a unit); carries optional `start_date` / `end_date`
- `MEMBER_OF` — used for two purposes:
  - **French supervision** (*tutelle*): research unit → supervising institution; carries optional `position` (`main_supervision`, `associated_supervision`, `participating_supervision`) plus `start_date` / `end_date`
  - **Structural membership without supervision**: e.g. team inside an axis; carries `start_date` / `end_date` but no `position`

### Data provenance and internal entities

**Person** nodes (`external: false`) were created from the institution's people registry. Internal persons are linked:
- `(p:Person)-[:MEMBER_OF]->(ru:ResearchUnit)` — ResearchUnit is a subtype of OrganizationUnit
- `(p:Person)-[:EMPLOYED_AT]->(inst:Institution)` — Institution is a subtype of OrganizationUnit
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

**HAS_AFFILIATION_STATEMENT** points to **AuthorityOrganization** nodes (not to `OrganizationUnit` subtypes). External organizations are reconstructed from registries such as RoR and represented in two subtypes:
- **AuthorityOrganizationState**: an organization at a given point in time, with identifiers (RoR, IdRef, HAL)
- **AuthorityOrganizationRoot**: groups multiple `AuthorityOrganizationState` nodes via `HAS_STATE` relations, for organizations that changed names, merged, or split

When an affiliation cannot be precisely matched to a specific `AuthorityOrganizationState`, it links to an `AuthorityOrganizationRoot` instead. `AuthorityOrganization` nodes carry `display_name` values **directly** (no intermediate `Literal` node).

### Person name properties

`Person` nodes carry `display_name` (canonical string) and `display_name_variants` (list). A full-text index `person_fulltext_name` covers both with the `standard-no-stop-words` analyzer — use `CALL db.index.fulltext.queryNodes('person_fulltext_name', ...)` for fuzzy name search.

### Journal nodes

`Journal` nodes carry a `titles` attribute (list of strings), a `publisher` attribute, and an `issn_l` attribute (the linking ISSN that groups its various ISSNs). Individual ISSNs are **JournalIdentifier** nodes linked via `(j:Journal)-[:HAS_IDENTIFIER]->(ji:JournalIdentifier)`.

### Literals

Almost all strings in the graph are represented as **Literal** nodes with:
- `value`: the string content
- `language`: 2-letter ISO 639-1 code, or `"ul"` for undetermined language
- `type`: the label type (e.g. `"concept_pref_label"`, `"concept_alt_label"`, `"document_title"`, `"document_abstract"`)

## Embeddings and vector search

### Vector index

A single Neo4j vector index named **`embeddable_embedding`** is maintained on the `Embeddable` label:

```cypher
CREATE VECTOR INDEX embeddable_embedding IF NOT EXISTS
FOR (n:Embeddable) ON n.embedding
OPTIONS {indexConfig: {`vector.dimensions`: <configured>, `vector.similarity_function`: 'cosine'}}
```

It covers both `Literal:Embeddable` and `TextLiteral:Embeddable` nodes uniformly.

### Querying the index

Always filter `embedding_status = 'success'` — nodes may carry the `:Embeddable` label before a vector has been computed:

```cypher
CALL db.index.vector.queryNodes('embeddable_embedding', $k, $query_embedding)
YIELD node, score
WHERE node.embedding_status = 'success'
```

`$query_embedding` is a `list<float>` that must have been produced by the same model used to build the index. `$k` is the number of candidate nodes to retrieve before post-filtering.

### Embeddable types and their graph anchors

Use this table to know which relationship and direction connects an `:Embeddable` node back to the entity that owns it:

| `type` property | Node label | Incoming relationship | Owner node |
|---|---|---|---|
| `document_title` | `Literal` | `(doc:Document)-[:HAS_TITLE]->(l)` | `Document` |
| `document_abstract` | `TextLiteral` | `(doc:Document)-[:HAS_ABSTRACT]->(l)` | `Document` |
| `concept_pref_label` | `Literal` | `(c:Concept)-[:HAS_PREF_LABEL]->(l)` | `Concept` |
| `concept_alt_label` | `Literal` | `(c:Concept)-[:HAS_ALT_LABEL]->(l)` | `Concept` |
| `concept_definition` | `TextLiteral` | `(c:Concept)-[:HAS_DEFINITION]->(l)` | `Concept` |
| `research_unit_name` | `Literal` | `(u:OrganizationUnit)-[:HAS_LONG_LABEL]->(l)` | `OrganizationUnit` |
| `research_unit_description` | `TextLiteral` | `(u:OrganizationUnit)-[:HAS_DESCRIPTION]->(l)` | `OrganizationUnit` |
| `organization_long_label` | `Literal` | `(o:OrganizationUnit)-[:HAS_LONG_LABEL]->(l)` | `OrganizationUnit` |
| `organization_description` | `TextLiteral` | `(o:OrganizationUnit)-[:HAS_DESCRIPTION]->(l)` | `OrganizationUnit` |
| `institution_name` | `Literal` | `(i:Institution)-[:HAS_LONG_LABEL]->(l)` | `Institution` |
| `institution_country_name` | `Literal` | via `HAS_ADDRESS` / `HAS_COUNTRY` chain | `StructuredPhysicalAddress` |
| `institution_state_name` | `Literal` | via `HAS_ADDRESS` / `HAS_STATE` chain | `StructuredPhysicalAddress` |
| `institution_continent_name` | `Literal` | via `HAS_ADDRESS` / `HAS_CONTINENT` chain | `StructuredPhysicalAddress` |
| `authority_organization_state_name` | `Literal` | `(a:AuthorityOrganizationState)-[:HAS_NAME]->(l)` | `AuthorityOrganizationState` |

### Typical Cypher pattern

Vector search → retrieve candidate literals → traverse back to owner entities → return results ranked by score:

```cypher
CALL db.index.vector.queryNodes('embeddable_embedding', $k, $query_embedding)
YIELD node AS literal, score
WHERE literal.embedding_status = 'success'
  AND literal.type IN ['document_title', 'document_abstract']
MATCH (doc:Document)-[:HAS_TITLE|HAS_ABSTRACT]->(literal)
RETURN doc.uid AS uid, literal.value AS matched_text, score
ORDER BY score DESC
LIMIT $limit
```

Post-filter with `WHERE literal.type IN [...]` to restrict results to a specific semantic domain; do not rely on `$k` alone because the index covers all types.

### Embedding properties on Embeddable nodes

| Property | Type | Meaning |
|---|---|---|
| `embedding_status` | string | `'pending'` / `'success'` / `'failed'` — always filter `= 'success'` before vector queries |
| `embedding` | `list<float>` | The vector, present only when status is `'success'` |
| `embedding_model` | string | Model name used to produce this vector |
| `embedding_hash` | string | SHA-256 of `value` at embedding time — used to detect stale vectors |

### Important caveats

- The embedding dimension depends on the deployed model (e.g. 384 for `multilingual-e5-small`, 1024 for `bge-m3`). Tools must not hardcode a dimension.
- Embeddings may be absent on a freshly populated graph until `compute-embeddings` is run. Always guard with `embedding_status = 'success'`.
- The index is on `Embeddable.embedding`, not on `Literal.embedding` or `TextLiteral.embedding` — always use the `:Embeddable` label in vector calls.

## Neo4j / Cypher Reference

Authoritative Cypher queries for the CRISalid graph are at `~/PycharmProjects/crisalid-ikg/app/graph/neo4j/queries`. Test fixture data (Cypher) is at `~/WebstormProjects/crisalid-apollo/tests/data/graph.cypher`.