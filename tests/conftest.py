import os
import socket  # noqa: F401 used in toolbox_url fixture

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from neo4j import GraphDatabase
from toolbox_langchain import ToolboxClient

load_dotenv("mcp-toolbox/.env.test", override=True)

TOOLBOX_URL = "http://127.0.0.1:5000"
FIXTURE_PATH = "tests/fixtures/graph.cypher"


@pytest.fixture(scope="session", autouse=True)
def load_fixtures():
    """Clear the test Neo4j instance and load fixture data."""
    uri = os.environ["NEO4J_URI"]
    user = os.environ.get("NEO4J_USER") or None
    password = os.environ.get("NEO4J_PASSWORD") or None
    auth = (user, password) if user else ("neo4j", "")
    driver = GraphDatabase.driver(uri, auth=auth)
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        cypher = open(FIXTURE_PATH).read()
        for statement in cypher.split(";"):
            statement = statement.strip()
            if statement:
                session.run(statement)
    driver.close()


@pytest.fixture(scope="session")
def toolbox_url():
    try:
        with socket.create_connection(("127.0.0.1", 5000), timeout=2):
            pass
    except OSError:
        pytest.fail(
            f"Toolbox server not reachable at {TOOLBOX_URL}. "
            "Start it with: cd mcp-toolbox && source .env.test && ./toolbox --config tools.yaml"
        )
    return TOOLBOX_URL


@pytest_asyncio.fixture(scope="session")
async def toolbox_client(toolbox_url):
    async with ToolboxClient(toolbox_url) as client:
        yield client
