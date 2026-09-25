# cli_project

CLI-chatbot joka keskustelee kuvitteellisista yritysdokumenteista Clauden ja oman [MCP](https://modelcontextprotocol.io/)-palvelimen kautta. Harjoitusprojekti, jossa MCP:n kolme rajapintaa (tools, resources, prompts) rakennetaan vaiheittain.

## Mitä projekti tekee

`main.py` käynnistää komentorivi-chatbotin, joka:

1. käynnistää `mcp_server.py`:n alaprosessina ja yhdistää siihen [MCP](https://modelcontextprotocol.io/)-protokollan yli (stdio),
2. välittää käyttäjän viestit Claudelle yhdessä palvelimen tarjoamien työkalujen kanssa,
3. antaa Clauden itse päättää milloin se listaa, lukee tai muokkaa kuvitteellisia dokumentteja MCP-työkalujen kautta,
4. tukee `@dokumentti.pääte`-mainintoja (esim. `@spec.txt`), jotka injektoivat dokumentin sisällön suoraan viestiin, sekä `/format <doc_id>`-komentoa, joka hakee palvelimelta valmiin promptipohjan dokumentin muotoiluun Markdowniksi.

Dokumentit elävät vain palvelinprosessin muistissa, joten muutokset eivät säily ajokertojen välillä.

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
- **`tests/`** — pytest-testit `mcp_server.py`:n työkaluille/resursseille, `MCPClient`-luokalle (oikeaa alaprosessia vasten) sekä `main.py`:n apufunktioille.
- **`.github/workflows/ci.yml`** — GitHub Actions -työnkulku, joka ajaa testit jokaisella pushilla ja pull requestilla.

## Asennus

```
pip install -r requirements.txt
```

> **Huom:** `requirements.txt` pinnaa `mcp<2`, koska koodi käyttää MCP SDK:n v1-rajapintaa (`mcp.server.fastmcp.FastMCP`). MCP-kirjaston versio 2.0 nimesi tämän uudelleen (`MCPServer`), joten pinnaamaton `pip install mcp` rikkoo projektin.

Luo `.env`-tiedosto projektin juureen (ks. `.env.example`):

```
ANTHROPIC_API_KEY="sinun-api-avaimesi"
```

## Käyttö

```
python main.py
```

Esimerkkisessio:

```
Sinä: mitä dokumentteja on saatavilla?
  [työkalu: list_documents({})]
Claude: Saatavilla on mm. deposition.md, report.pdf, financials.docx...

Sinä: mitä @spec.txt sisältää?
Claude: Se määrittelee laitteiston tekniset vaatimukset.

Sinä: /format plan.md
Claude: Muotoilin plan.md-dokumentin Markdown-otsikoiksi ja luetteloiksi.
```

Kirjoita `lopeta`, `exit` tai `quit` lopettaaksesi.

## Testien ajaminen

```
pip install -r requirements-dev.txt
pytest -v
```

Testit kattavat:

- `mcp_server.py`: dokumenttien listauksen, lukemisen ja muokkauksen (tools), suorat ja templatoidut resurssit sekä `format`-promptin, mukaan lukien virhetilanteet (tuntematon `doc_id`, `old_str` jota ei löydy).
- `mcp_client.py`: `MCPClient`-luokan koko rajapinnan (`list_tools`, `call_tool`, `read_resource`, `get_prompt`) oikeaa `mcp_server.py`-alaprosessia vasten.
- `main.py`: MCP-työkalujen muunnoksen Clauden työkaluformaattiin, `@maininta`-regexin ja `expand_mentions`-funktion (tunnettu/tuntematon dokumentti, ei mainintoja) käyttäen kevyttä testidubia oikean MCP-clientin sijaan.

Sama testisarja ajetaan automaattisesti GitHub Actionsissa jokaisella pushilla ja pull requestilla (`.github/workflows/ci.yml`), Python-versioilla 3.10–3.12.
