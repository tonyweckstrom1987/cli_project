# cli_project

CLI-chatbot joka keskustelee kuvitteellisista yritysdokumenteista Clauden ja oman [MCP](https://modelcontextprotocol.io/)-palvelimen kautta. Harjoitusprojekti, jossa MCP:n kolme rajapintaa (tools, resources, prompts) rakennetaan vaiheittain.

## Rakenne

- **`mcp_server.py`** — MCP-palvelin, joka hallinnoi kuvitteellisia dokumentteja muistissa.
  - Tools: `list_documents`, `read_doc_contents`, `edit_document`
  - Resources: `docs://documents` (dokumenttilista), `docs://documents/{doc_id}` (yksittäisen dokumentin sisältö)
  - Prompts: `format` (valmis promptipohja dokumentin muotoiluun Markdownia varten)
- **`mcp_client.py`** — uudelleenkäytettävä `MCPClient`-luokka, joka kätkee stdio-yhteyden ja MCP-kirjaston matalan tason API:n.
- **`main.py`** — CLI-chatbot, joka yhdistää Clauden ja MCP-palvelimen:
  - Normaalit viestit menevät Claudelle, joka päättää itse mitä työkaluja käyttää
  - `@dokumentti.pääte`-maininnat injektoivat dokumentin sisällön suoraan viestiin resurssin kautta
  - `/format <doc_id>` hakee valmiin promptipohjan palvelimelta ja käynnistää dokumentin muotoilun

## Asennus

```
pip install anthropic mcp python-dotenv pydantic
```

Luo `.env`-tiedosto projektin juureen:

```
ANTHROPIC_API_KEY="sinun-api-avaimesi"
```

## Käyttö

```
python main.py
```

Kirjoita `lopeta`, `exit` tai `quit` lopettaaksesi. Dokumentit elävät vain palvelinprosessin muistissa — muutokset eivät säily ajokertojen välillä.
