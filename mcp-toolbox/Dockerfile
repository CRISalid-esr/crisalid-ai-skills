FROM debian:bookworm-slim

ARG TOOLBOX_VERSION=v1.1.0

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
    && curl -fsSL \
       "https://storage.googleapis.com/mcp-toolbox-for-databases/${TOOLBOX_VERSION}/linux/amd64/toolbox" \
       -o /usr/local/bin/toolbox \
    && chmod +x /usr/local/bin/toolbox \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY tools-auth.yaml .

# Neo4j connection
ENV NEO4J_URI=
ENV NEO4J_USER=
ENV NEO4J_PASSWORD=

# Keycloak OIDC (issuer only — client credentials belong to the calling client, not the server)
ENV KEYCLOAK_ISSUER=

EXPOSE 5000

CMD ["toolbox", "--address", "0.0.0.0", "--config", "tools-auth.yaml"]
