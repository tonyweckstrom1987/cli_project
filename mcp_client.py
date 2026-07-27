"""
Uudelleenkäytettävä MCP-asiakasluokka. Kätkee AsyncExitStack- ja
stdio-yksityiskohdat siistin rajapinnan taakse: connect(), list_tools(),
call_tool(). main.py käyttää tätä luokkaa eikä koskaan puhu suoraan
mcp-kirjaston matalan tason API:lle.

Lisätty 24.7.2026 ("Accessing resources" -oppitunti): list_resources()
ja read_resource() Toolien rinnalle. Näiden avulla main.py voisi toteuttaa
@dokumentti-automaattitäydennyksen, joka injektoi dokumentin sisällön
suoraan promptiin ilman erillistä työkalukutsua.

Lisätty 24.7.2026 ("Prompts in the client" -oppitunti): list_prompts()
ja get_prompt() Resourcesin rinnalle. Näiden avulla main.py voisi
toteuttaa /format-tyyppisen komennon, joka hakee palvelimelta valmiiksi
hiotun, interpoloidun viestin ja lähettää sen suoraan Claudelle.
"""
import json
from contextlib import AsyncExitStack
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from pydantic import AnyUrl


class MCPClient:
    def __init__(self, command: str, args: list[str], env: Optional[dict] = None):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(command=self._command, args=self._args, env=self._env)
        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await self._exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        self._session = session

    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError("MCP-sessiota ei ole alustettu - kutsu connect() ensin.")
        return self._session

    async def list_tools(self):
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, tool_input: dict):
        return await self.session().call_tool(tool_name, tool_input)

    async def list_resources(self):
        """Listaa suorat resurssit (esim. dokumenttilista @-automaattitäydennystä varten)."""
        result = await self.session().list_resources()
        return result.resources

    async def read_resource(self, uri: str) -> Any:
        """
        Hakee resurssin sisällön URI:n perusteella (esim. "docs://documents"
        tai "docs://documents/deposition.md"). MIME-tyyppi kertoo miten data
        pitää tulkita: JSON-resurssit parsitaan Python-olioiksi, muut
        palautetaan sellaisenaan merkkijonona.
        """
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]

        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                return json.loads(resource.text)
            return resource.text

        return resource

    async def list_prompts(self) -> list[types.Prompt]:
        """Listaa kaikki palvelimen tarjoamat valmiit promptipohjat (esim. /format)."""
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name: str, args: dict[str, str]):
        """
        Hakee tietyn promptin, argumentit interpoloituna. `args`-sanakirjan
        avaimet vastaavat palvelimen prompt-funktion parametreja (esim.
        {"doc_id": "deposition.md"} format-promptille). Palauttaa valmiin
        viestilistan, joka voidaan syöttää suoraan Claudelle.
        """
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def cleanup(self):
        await self._exit_stack.aclose()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
