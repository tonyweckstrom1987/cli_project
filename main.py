"""
CLI-chatbot joka keskustelee kuvitteellisista yritysdokumenteista Clauden ja
oman MCP-palvelimemme (mcp_server.py) kautta. Tämä on se "täysi projekti" -osa:
main.py ei tiedä mitään dokumenttien tallennuksesta - se vain välittää
käyttäjän kysymykset Claudelle ja Clauden työkalukutsut MCP-clientille.
"""
import asyncio
import re

from dotenv import load_dotenv
from anthropic import Anthropic

from mcp_client import MCPClient

load_dotenv()
client = Anthropic()
model = "claude-sonnet-5"

SYSTEM_PROMPT = (
    "Olet avulias assistentti joka auttaa käyttäjää löytämään ja muokkaamaan "
    "yrityksen dokumentteja. Käytä list_documents-työkalua nähdäksesi mitä "
    "dokumentteja on saatavilla, read_document-työkalua lukeaksesi niiden "
    "sisällön, ja edit_document-työkalua tehdäksesi muutoksia. Älä koskaan "
    "keksi dokumenttien sisältöä - tarkista se aina työkalujen kautta."
)


def mcp_tools_to_claude_format(mcp_tools):
    return [
        {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
        for t in mcp_tools
    ]


MENTION_RE = re.compile(r"@([\w.\-]+)")


async def expand_mentions(mcp_client: MCPClient, text: str) -> str:
    """
    Etsii viestistä @dokumentti-maininnat (esim. "@spec.txt") ja injektoi
    niiden sisällön suoraan viestiin docs://documents/{doc_id}-resurssin
    kautta, ilman että Claude tarvitsee erillistä työkalukutsua nähdäkseen
    sisällön.
    """
    mentions = MENTION_RE.findall(text)
    if not mentions:
        return text

    known_docs = await mcp_client.read_resource("docs://documents")

    injected = []
    for doc_id in mentions:
        if doc_id not in known_docs:
            injected.append(f"[Huom: dokumenttia '{doc_id}' ei löytynyt]")
            continue
        content = await mcp_client.read_resource(f"docs://documents/{doc_id}")
        injected.append(f"[Dokumentin '{doc_id}' sisältö: {content}]")

    if not injected:
        return text

    return text + "\n\n" + "\n".join(injected)


async def process_query(mcp_client: MCPClient, messages: list, claude_tools: list) -> str:
    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            tools=claude_tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "\n".join([b.text for b in response.content if b.type == "text"])

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [työkalu: {block.name}({block.input})]")
            try:
                result = await mcp_client.call_tool(block.name, block.input)
                result_text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                    "is_error": result.isError,
                })
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(e),
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})


async def main():
    async with MCPClient(command="python", args=["mcp_server.py"]) as mcp_client:
        mcp_tools = await mcp_client.list_tools()
        claude_tools = mcp_tools_to_claude_format(mcp_tools)

        print(f"Yhdistetty MCP-palvelimeen. Käytössä {len(claude_tools)} työkalua: "
              f"{[t['name'] for t in claude_tools]}")
        print("Kirjoita 'lopeta' lopettaaksesi.\n")

        messages = []
        while True:
            user_input = input("Sinä: ")
            if user_input.strip().lower() in ("lopeta", "exit", "quit"):
                break
            if not user_input.strip():
                continue

            if user_input.startswith("/format"):
                parts = user_input.split(maxsplit=1)
                if len(parts) != 2:
                    print("Käyttö: /format <doc_id>\n")
                    continue
                doc_id = parts[1].strip()
                try:
                    prompt_messages = await mcp_client.get_prompt("format", {"doc_id": doc_id})
                except Exception as e:
                    print(f"Virhe promptin haussa: {e}\n")
                    continue
                for m in prompt_messages:
                    messages.append({"role": m.role, "content": m.content.text})
            else:
                expanded_input = await expand_mentions(mcp_client, user_input)
                messages.append({"role": "user", "content": expanded_input})

            answer = await process_query(mcp_client, messages, claude_tools)
            print(f"Claude: {answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
