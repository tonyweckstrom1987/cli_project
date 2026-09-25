import asyncio
import os
from types import SimpleNamespace

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")

import main


class FakeMCPClient:
    """Korvaa oikean MCPClientin expand_mentions-testeissä ilman
    että tarvitaan oikeaa alaprosessia tai MCP-palvelinta."""

    def __init__(self, resources):
        self.resources = resources

    async def read_resource(self, uri: str):
        return self.resources[uri]


def test_mcp_tools_to_claude_format_maps_fields():
    mcp_tools = [
        SimpleNamespace(name="list_documents", description="Lists docs", inputSchema={"type": "object"}),
        SimpleNamespace(name="edit_document", description="Edits a doc", inputSchema={"type": "object", "properties": {}}),
    ]

    claude_tools = main.mcp_tools_to_claude_format(mcp_tools)

    assert claude_tools == [
        {"name": "list_documents", "description": "Lists docs", "input_schema": {"type": "object"}},
        {"name": "edit_document", "description": "Edits a doc", "input_schema": {"type": "object", "properties": {}}},
    ]


def test_mention_regex_finds_dotted_ids():
    assert main.MENTION_RE.findall("katso @spec.txt ja @plan.md kiitos") == ["spec.txt", "plan.md"]


def test_mention_regex_ignores_text_without_at():
    assert main.MENTION_RE.findall("ei mainintoja tässä") == []


def test_expand_mentions_returns_original_text_when_no_mentions():
    client = FakeMCPClient(resources={"docs://documents": []})
    result = asyncio.run(main.expand_mentions(client, "moi, ei mainintoja"))
    assert result == "moi, ei mainintoja"


def test_expand_mentions_injects_known_document_content():
    client = FakeMCPClient(
        resources={
            "docs://documents": ["spec.txt"],
            "docs://documents/spec.txt": "Tekniset vaatimukset.",
        }
    )
    result = asyncio.run(main.expand_mentions(client, "voitko tiivistää @spec.txt"))
    assert "voitko tiivistää @spec.txt" in result
    assert "Tekniset vaatimukset." in result


def test_expand_mentions_notes_unknown_document():
    client = FakeMCPClient(resources={"docs://documents": []})
    result = asyncio.run(main.expand_mentions(client, "avaa @ei_ole.txt"))
    assert "ei löytynyt" in result
