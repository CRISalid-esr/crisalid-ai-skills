import os
import socket  # noqa: F401 used in toolbox_url fixture
from typing import Any, Dict

import pytest
import pytest_asyncio
import toolbox_core.protocol as _tc_protocol
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase
from toolbox_langchain import ToolboxClient

# toolbox server serialises float parameters as JSON Schema "number";
# the client type map only has "float" — add the alias so float array
# parameters (e.g. embedding vectors) load without ValueError.
_tc_protocol.__TYPE_MAP["number"] = float  # type: ignore[attr-defined]

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
        session.run(
            "CREATE FULLTEXT INDEX person_fulltext_name IF NOT EXISTS "
            "FOR (p:Person) ON EACH [p.display_name, p.display_name_variants] "
            "OPTIONS { indexConfig: { `fulltext.analyzer`: 'standard-no-stop-words' } }"
        )
        session.run(
            "CREATE VECTOR INDEX embeddable_embedding IF NOT EXISTS "
            "FOR (n:Embeddable) ON n.embedding "
            "OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}}"
        )
        title_vec = [1.0 if i == 0 else 0.0 for i in range(1024)]
        abstract_vec = [1.0 if i == 1 else 0.0 for i in range(1024)]
        session.run(
            "MATCH (doc:Document {uid: 'doc1'})-[:HAS_TITLE]->(t:Literal {language: 'en'}) "
            "SET t:Embeddable, t.type = 'document_title', t.embedding_status = 'success', "
            "    t.embedding_model = 'bge-m3', t.embedding = $vec",
            vec=title_vec,
        )
        session.run(
            "MATCH (doc:Document {uid: 'doc1'})-[:HAS_ABSTRACT]->(a:TextLiteral {language: 'en'}) "
            "SET a:Embeddable, a.type = 'document_abstract', a.embedding_status = 'success', "
            "    a.embedding_model = 'bge-m3', a.embedding = $vec",
            vec=abstract_vec,
        )
        session.run("CALL db.awaitIndexes(30)")
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


def load_sorbobot_tools_from_yaml() -> Dict[str, Any]:
    """Load SorboBot tools directly from tools-sorbobot.yaml file."""
    yaml_path = "mcp-toolbox/tools-sorbobot.yaml"
    with open(yaml_path, "r") as f:
        documents = list(yaml.safe_load_all(f))
    
    tools_dict = {}
    for doc in documents:
        if doc and doc.get("kind") == "tool":
            tools_dict[doc["name"]] = doc
    return tools_dict


class MockSorbobotTool:
    """Mock tool that executes Cypher queries directly against Neo4j."""
    
    def __init__(self, tool_def, driver):
        self.name = tool_def["name"]
        self.tool_def = tool_def
        self.driver = driver
    
    async def ainvoke(self, params):
        """Execute the Cypher query with the given parameters."""
        statement = self.tool_def["statement"]
        
        # Apply default values from tool definition
        tool_params = {}
        if "parameters" in self.tool_def:
            for param_def in self.tool_def["parameters"]:
                param_name = param_def["name"]
                if param_name in params:
                    tool_params[param_name] = params[param_name]
                elif "default" in param_def:
                    tool_params[param_name] = param_def["default"]
                else:
                    tool_params[param_name] = params.get(param_name)
        else:
            tool_params = params
        
        with self.driver.session() as session:
            result = session.run(statement, tool_params)
            rows = [dict(record) for record in result]
            return rows


@pytest.fixture
def sorbobot_tools_dict():
    """Fixture that provides the SorboBot tools dictionary."""
    return load_sorbobot_tools_from_yaml()


@pytest.fixture
def neo4j_driver():
    """Fixture that provides a Neo4j driver for executing queries directly."""
    uri = os.environ["NEO4J_URI"]
    user = os.environ.get("NEO4J_USER") or None
    password = os.environ.get("NEO4J_PASSWORD") or None
    auth = (user, password) if user else ("neo4j", "")
    
    driver = GraphDatabase.driver(uri, auth=auth)
    yield driver
    driver.close()


# ===== SorboBot Tool Fixtures =====

@pytest.fixture
def sorbobot_search_domains_tool(sorbobot_tools_dict, neo4j_driver):
    """Fixture for sorbobot-search-domains tool."""
    tool_def = sorbobot_tools_dict.get("sorbobot-search-domains")
    if not tool_def:
        raise ValueError("sorbobot-search-domains tool not found")
    return MockSorbobotTool(tool_def, neo4j_driver)


@pytest.fixture
def sorbobot_get_domain_authors_tool(sorbobot_tools_dict, neo4j_driver):
    """Fixture for sorbobot-get-domain-authors tool."""
    tool_def = sorbobot_tools_dict.get("sorbobot-get-domain-authors")
    if not tool_def:
        raise ValueError("sorbobot-get-domain-authors tool not found")
    return MockSorbobotTool(tool_def, neo4j_driver)


@pytest.fixture
def sorbobot_get_parent_domains_tool(sorbobot_tools_dict, neo4j_driver):
    """Fixture for sorbobot-get-parent-domains tool."""
    tool_def = sorbobot_tools_dict.get("sorbobot-get-parent-domains")
    if not tool_def:
        raise ValueError("sorbobot-get-parent-domains tool not found")
    return MockSorbobotTool(tool_def, neo4j_driver)


@pytest.fixture
def sorbobot_get_person_expertise_tool(sorbobot_tools_dict, neo4j_driver):
    """Fixture for sorbobot-get-person-expertise tool."""
    tool_def = sorbobot_tools_dict.get("sorbobot-get-person-expertise")
    if not tool_def:
        raise ValueError("sorbobot-get-person-expertise tool not found")
    return MockSorbobotTool(tool_def, neo4j_driver)
