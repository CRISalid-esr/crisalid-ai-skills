# crisalid-ai-skills

Tooling and skills for AI-powered access to the CRISalid institutional knowledge graph. This repository provides MCP-compatible tools that wrap curated queries against the CRISalid Neo4j graph, making it easy to integrate structured academic data (researchers, publications, topics, organisations) into LLM-based agents and workflows.

---

## MCP Toolbox

Tools are served via [MCP Toolbox for Databases](https://github.com/googleapis/mcp-toolbox), a lightweight server that exposes named Cypher queries as MCP tools. Two toolsets are available:

| Toolset | Tools | Use case |
|---|---|---|
| `crisalid-restricted` | `get-crisalid-schema`, `list-person-publications` | Clients needing curated domain tools |
| `crisalid-unrestricted` | `get-crisalid-schema`, `list-person-publications`, `execute-cypher-readonly` | Advanced agents with ad-hoc Cypher access |

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
docker build --build-arg TOOLBOX_VERSION=v1.1.0 -t crisalid-graph-mcp mcp-toolbox/
```

**Run:**

```bash
docker run -p 5000:5000 \
  -e NEO4J_URI=bolt://<host>:7687 \
  -e NEO4J_USER=neo4j \
  -e NEO4J_PASSWORD=<password> \
  -e KEYCLOAK_ISSUER=https://<keycloak-host>/realms/<realm> \
  -e KEYCLOAK_CLIENT_ID=<client-id> \
  -e KEYCLOAK_CLIENT_SECRET=<secret> \
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
  -e KEYCLOAK_CLIENT_ID=<client-id> \
  -e KEYCLOAK_CLIENT_SECRET=<secret> \
  -e KEYCLOAK_SSL_VERIFY=false \
  --add-host=host.docker.internal:host-gateway \
  --add-host=keycloak.local:<host-ip> \
  -v /tmp/keycloak-local.crt:/usr/local/share/ca-certificates/custom-ca.crt \
  crisalid-graph-mcp
```

- `--add-host=host.docker.internal:host-gateway` — lets the container reach services on the host (Neo4j)
- `--add-host=keycloak.local:<host-ip>` — resolves the Keycloak hostname inside the container
- `-v /tmp/keycloak-local.crt:...` — mounts the self-signed CA cert so the toolbox can validate Keycloak's TLS
- `KEYCLOAK_SSL_VERIFY=false` — disables TLS verification in the Python client when fetching tokens

</details>

### Authentication (Keycloak OIDC)

`tools-auth.yaml` adds a Keycloak OIDC auth layer. Tools marked `authRequired` reject calls without a valid JWT. Clients obtain a token via the `client_credentials` grant (service account) and pass it to the toolbox SDK.

#### Required environment variables (add to `mcp-toolbox/.env`)

```
KEYCLOAK_ISSUER=https://<keycloak-host>/realms/<realm>
KEYCLOAK_CLIENT_ID=<your-client-id>
KEYCLOAK_CLIENT_SECRET=<your-client-secret>
```

#### Keycloak service account setup

**1. Create a client**

In Keycloak admin → Clients → Create client:
- Client type: OpenID Connect
- Client ID: e.g. `example-mcp-client`
- Enable *Client authentication* (confidential)
- Enable *Service accounts roles*
- Disable *Standard flow* and *Direct access grants*

**2. Add an Audience mapper**

The toolbox validates the JWT `aud` claim against `KEYCLOAK_CLIENT_ID`. By default Keycloak does not include the client ID in `aud`, so this mapper is required.

In the client's page → Client scopes → click the dedicated scope (`<client-id>-dedicated`) → Add mapper → Configure a new mapper → **Audience**:
- Name: `mcp-example-client-audience`
- Included Custom Audience: `crisalid-graph-mcp`
- Add to access token: On

**3. Note the client secret**

Clients → `<your-client-id>` → Credentials → copy the secret into `KEYCLOAK_CLIENT_SECRET`.

#### SSL certificates in local environments

If your Keycloak instance uses a self-signed certificate:

- **Client side** (`samples/load_restricted_toolset_authenticated.py`): set `KEYCLOAK_SSL_VERIFY=false` in `.env` to skip verification when fetching tokens.
- **Toolbox server side**: the toolbox (Go binary) validates the JWT by fetching Keycloak's JWKS endpoint and uses the system CA trust store. Add the cert to the system trust store:

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

# Load the restricted toolset with Keycloak authentication
# Requires toolbox running with tools-auth.yaml and KEYCLOAK_* env vars set
uv run python samples/load_restricted_toolset_authenticated.py
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
