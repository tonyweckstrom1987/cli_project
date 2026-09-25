import asyncio
import os
import sys

from mcp_client import MCPClient

SERVER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mcp_server.py")


async def _run_against_real_server(callback):
    async with MCPClient(command=sys.executable, args=[SERVER_PATH]) as client:
        return await callback(client)


def test_list_tools_exposes_document_tools():
    async def scenario(client):
        tools = await client.list_tools()
        return sorted(t.name for t in tools)

    assert asyncio.run(_run_against_real_server(scenario)) == [
        "edit_document",
        "list_documents",
        "read_doc_contents",
    ]


def test_read_resource_returns_document_list_as_json():
    async def scenario(client):
        return await client.read_resource("docs://documents")

    docs = asyncio.run(_run_against_real_server(scenario))
    assert "spec.txt" in docs
    assert isinstance(docs, list)


def test_read_resource_returns_single_document_text():
    async def scenario(client):
        return await client.read_resource("docs://documents/spec.txt")

    content = asyncio.run(_run_against_real_server(scenario))
    assert content == "These specifications define the technical requirements for the equipment."


def test_call_tool_edit_document_round_trip():
    async def scenario(client):
        await client.call_tool(
            "edit_document",
            {"doc_id": "plan.md", "old_str": "implementation", "new_str": "rollout"},
        )
        result = await client.call_tool("read_doc_contents", {"doc_id": "plan.md"})
        return result.content[0].text

    updated = asyncio.run(_run_against_real_server(scenario))
    assert "rollout" in updated


def test_get_prompt_format_interpolates_doc_id():
    async def scenario(client):
        return await client.get_prompt("format", {"doc_id": "outlook.pdf"})

    messages = asyncio.run(_run_against_real_server(scenario))
    assert "outlook.pdf" in messages[0].content.text
