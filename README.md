# crisalid-ai-skills

Tooling and skills for AI-powered access to the CRISalid institutional knowledge graph. This repository provides MCP-compatible tools that wrap curated queries against the CRISalid Neo4j graph, making it easy to integrate structured academic data (researchers, publications, topics, organisations) into LLM-based agents and workflows.

---

## MCP Toolbox

Tools are served via [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox), a lightweight server that exposes named Cypher queries as MCP tools. Two toolsets are available:

| Toolset | Tools | Use case |
|---|---|---|
| `crisalid-restricted` | the curated tools: `get-crisalid-schema`, `get-current-person`, `search-person-by-name`, `list-person-publications`, `get-person-memberships`, the concept and expertise tools… | Clients needing curated domain tools |
| `crisalid-unrestricted` | the curated tools plus `execute-cypher-readonly` | Advanced agents with ad-hoc Cypher access |
| `sorbobot` | the concept and expertise tools, `search-person-by-name`, `get-current-person` | The SorboBot agent |

The exact tool lists are the `kind: toolset` documents at the end of `mcp-toolbox/tools.yaml`.

### Run the MCP server

First, install the toolbox. Two options:

**Via npx (no installation required):**
```bash
npx @toolbox-sdk/server --config tools.yaml
```

**Via binary (Linux):** 

Either download from [mcp-toolbox.dev](https://mcp-toolbox.dev/documentation/introduction/) and place the binary in `mcp-toolbox/`.
Or directly run this from folder "mcp-toolbox":
```bash
export VERSION=1.16.0
curl -L -o toolbox https://storage.googleapis.com/mcp-toolbox-for-databases/v$VERSION/linux/amd64/toolbox
chmod +x toolbox
```

Then set your environment variables in a .env file, by copying and filling the .env.sample.

Finally, start the server:

```bash
cd mcp-toolbox
set -a && source .env && set +a
./toolbox --config tools.yaml            # without authentication
./toolbox --config tools-auth.yaml      # with Keycloak authentication
```

The server listens on `http://127.0.0.1:5000` by default.

Add `--ui` to also launch a web interface for browsing and manually invoking tools:

```bash
./toolbox --config tools.yaml --ui
# UI available at http://127.0.0.1:5000/ui
```

### Run with Docker

A `Dockerfile` is provided in `mcp-toolbox/`. It downloads the official toolbox binary and runs the authenticated configuration (`tools-auth.yaml`).

**Build:**

```bash
docker build -t crisalid-graph-mcp mcp-toolbox/
# Pin a specific toolbox version:
docker build --build-arg TOOLBOX_VERSION=v1.16.0 -t crisalid-graph-mcp mcp-toolbox/
```

**Run:**

```bash
docker run -p 5000:5000 \
  -e NEO4J_URI=bolt://<host>:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=<password> \
  -e KEYCLOAK_ISSUER=https://<keycloak-host>/realms/<realm> \
  -e MCP_AUDIENCE=crisalid-graph-mcp \
  crisalid-graph-mcp
```

Or pass an env file:

```bash
docker run -p 5000:5000 --env-file mcp-toolbox/.env crisalid-graph-mcp
```

The server listens on `0.0.0.0:5000` inside the container, exposed on port 5000.

<details>
<summary>Local dev example (Neo4j and Keycloak running on host, self-signed cert)</summary>

```bash
docker run -p 5000:5000 \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=<password> \
  -e KEYCLOAK_ISSUER=https://keycloak.local:8443/realms/<realm> \
  -e MCP_AUDIENCE=crisalid-graph-mcp \
  --add-host=host.docker.internal:host-gateway \
  --add-host=keycloak.local:<host-ip> \
  crisalid-graph-mcp
```

- `--add-host=host.docker.internal:host-gateway` — lets the container reach services on the host (Neo4j)
- `--add-host=keycloak.local:<host-ip>` — resolves the Keycloak hostname inside the container
The toolbox (a Go binary) validates Keycloak's TLS certificate with the system CA store. To trust a private CA
(mkcert, institutional CA), mount its PEM file and point `SSL_CERT_FILE` at it:

```bash
docker run ... \
  -v "$(mkcert -CAROOT)/rootCA.pem:/etc/ssl/certs/mkcert-rootCA.pem:ro" \
  -e SSL_CERT_FILE=/etc/ssl/certs/mkcert-rootCA.pem \
  crisalid-graph-mcp
```

</details>

### Authentication (Keycloak OIDC)

`tools-auth.yaml` declares a `generic` OIDC auth service named `crisalid-keycloak` and marks every served tool
`authRequired`. For each tool call, the client sends a Keycloak access token in the `crisalid-keycloak_token` header
(the header name is `<auth service name>_token`; the toolbox SDKs build it from the `auth_token_getters` mapping). The
toolbox fetches the realm's OpenID configuration and JWKS from `KEYCLOAK_ISSUER` and checks the token signature, `exp`,
`iss` (must equal the issuer advertised by the discovery document, hence a single public issuer URL for every service)
and `aud` (must contain `MCP_AUDIENCE`). A call without a valid token is rejected.

#### Environment variables

**Toolbox server** (`tools-auth.yaml` / Docker):
```
KEYCLOAK_ISSUER=https://<keycloak-host>/realms/<realm>   # public issuer URL
MCP_AUDIENCE=crisalid-graph-mcp                                 # expected `aud` claim
```

**Sample clients only** (not needed by the server):
```
KEYCLOAK_CLIENT_ID=<client-id>
KEYCLOAK_CLIENT_SECRET=<client-secret>
KEYCLOAK_SSL_VERIFY=true   # set to false for self-signed certs in local dev
USER_ACCESS_TOKEN=<token>  # delegated sample only
```

#### Token sources

Two kinds of tokens reach the toolbox; both carry `aud: crisalid-graph-mcp` and are validated the same way.

| Token | Obtained by | Grant | Used for |
|---|---|---|---|
| Service-account token | the calling service with `KEYCLOAK_CLIENT_ID` / `KEYCLOAK_CLIENT_SECRET` | `client_credentials` | batch jobs and non-interactive clients (`samples/load_restricted_toolset_authenticated.py`) |
| Exchanged user token | the `crisalid-agents` chat API, from the access token of the signed-in person | RFC 8693 token exchange (`grant_type=urn:ietf:params:oauth:grant-type:token-exchange`, `subject_token_type=urn:ietf:params:oauth:token-type:access_token`, `audience=crisalid-graph-mcp`) | the chat agents, so that the toolbox knows who is asking (`samples/load_restricted_toolset_delegated.py`) |

The exchanged token keeps the claims of the person (`sub`, `preferred_username`, `email`) and expires with the
original token.

#### Authenticated parameters and `get-current-person`

A tool parameter bound to a token claim with `authServices` is an *authenticated parameter*: the toolbox fills it from
the verified token and hides it from the tool manifest, so the LLM can neither see nor supply it.

```yaml
parameters:
  - name: username
    type: string
    description: Username of the signed-in person, taken from the preferred_username claim of the token
    authServices:
      - name: crisalid-keycloak
        field: preferred_username
authRequired:
  - crisalid-keycloak
```

`get-current-person` (toolsets `crisalid-restricted`, `crisalid-unrestricted` and `sorbobot`) is the only tool that
uses one. It takes no LLM-visible input and returns the signed-in person in the shape of a `search-person-by-name`
candidate (`uid`, `display_name`, `external`, `identifiers`, `laboratories`), or an empty list when nobody matches. The
person is resolved through the `local` agent identifier:

```cypher
WITH $username AS raw_username, split($username, '@')[0] AS local_identifier
MATCH (person:Person)-[:HAS_IDENTIFIER]->(local_id:AgentIdentifier {type: 'local'})
WHERE local_id.value IN [local_identifier, raw_username]
```

When `preferred_username` is an eppn (`login@domain`), the domain is dropped before the lookup, the same rule as
`stripDomainFromEppn` in SoVisu+ (`src/app/auth/auth_options.ts`), which registers the stripped login as the person's
`local` identifier. A `local` identifier that stores the full eppn still matches. Agents call `get-current-person`
first for "me / my …" questions and pass the returned `uid` to the other person tools, which keep their explicit
`person_uid` parameter.

In `tools.yaml` (no authentication, local development and tests), `username` is an ordinary parameter supplied by the
caller; the statement is the same.

#### Keycloak configuration (realm `crisalid-inst`)

- Client `crisalid-graph-mcp`: confidential, every flow off. It is the resource client the toolbox stands for: the value of
  `MCP_AUDIENCE`. It never authenticates.
- Client scope `crisalid-graph-mcp-audience` (default type) with an *Audience* mapper → included client audience
  `crisalid-graph-mcp`, added to the access token. Without it Keycloak does not put `crisalid-graph-mcp` in `aud`.
- Client `crisalid-agents`: confidential, *Service accounts roles* on (batch), *Standard token exchange* on, standard
  and direct flows off; `crisalid-graph-mcp-audience` as default scope. It is the requester of the token exchange and the
  owner of the service account. The `audience` parameter of a token exchange can only keep audiences the requester's
  scopes already grant, which is why the scope is assigned to this client.
- The user-facing clients (`sovisuplus`, `open-webui`) do not need the scope: their tokens are issued for the chat API
  and exchanged by it.

For a batch-only client, the same recipe applies: confidential client, service accounts on, the
`crisalid-graph-mcp-audience` scope (or a dedicated Audience mapper with included custom audience `crisalid-graph-mcp`), and the
secret copied into `KEYCLOAK_CLIENT_SECRET`.

#### SSL certificates in local environments

If your Keycloak instance uses a self-signed certificate:

- **Client side** (`samples/load_restricted_toolset_authenticated.py`, `samples/load_restricted_toolset_delegated.py`): set `KEYCLOAK_SSL_VERIFY=false` in `.env` to skip verification when fetching tokens.
- **Toolbox server side**: the toolbox (Go binary) validates the JWT by fetching Keycloak's JWKS endpoint and uses the system CA trust store (in Docker, see `SSL_CERT_FILE` above). On a host, add the cert to the system trust store:

```bash
# Export the cert
openssl s_client -connect <keycloak-host>:<port> -showcerts </dev/null 2>/dev/null \
  | openssl x509 -outform PEM > /tmp/keycloak-local.crt

# Ubuntu/Debian
sudo cp /tmp/keycloak-local.crt /usr/local/share/ca-certificates/keycloak-local.crt
sudo update-ca-certificates
```

Then restart the toolbox for the change to take effect.

### Run a client

Sample scripts using [toolbox-langchain](https://pypi.org/project/toolbox-langchain/) are in `samples/`. They connect to the running server and invoke tools directly, without an LLM.

```bash
# Load the restricted toolset and call get-crisalid-schema (no auth)
uv run python samples/load_restricted_toolset.py

# Load the unrestricted toolset and run a sample Cypher query (no auth)
uv run python samples/load_unrestricted_toolset.py

# Load the restricted toolset with a service-account token
# Requires toolbox running with tools-auth.yaml and KEYCLOAK_* env vars set
uv run python samples/load_restricted_toolset_authenticated.py

# Load the restricted toolset with the token of a signed-in person and call get-current-person
# USER_ACCESS_TOKEN: a user access token; with KEYCLOAK_CLIENT_ID/SECRET set, it is exchanged
# for the toolbox audience (MCP_AUDIENCE, default crisalid-graph-mcp) before being sent
uv run python samples/load_restricted_toolset_delegated.py
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
