"""
MCP-palvelin joka hallinnoi kuvitteellisia dokumentteja muistissa.
Päivitetty oppitunnin virallista tyyliä vastaavaksi: pydantic Field
tuottaa parametrikuvaukset automaattisesti JSON-skeemaan @mcp.tool()-
dekoraattorin docstringin sijaan.

Lisätty 22.7.2026 ("Defining resources" -oppitunti): kaksi Resourcea
Toolien rinnalle. Resources ovat datan hakemiseen (kuin HTTP GET),
Tools toimintojen suorittamiseen (kuin HTTP POST/PUT). Näiden avulla
voisi rakentaa esim. main.py:hen @dokumentin_nimi-automaattitäydennyksen,
joka injektoi dokumentin sisällön suoraan Clauden promptiin ilman
erillistä työkalukutsua.

Lisätty 24.7.2026 ("Defining prompts" -oppitunti): yksi Prompt.
Prompts ovat valmiiksi hiottuja, testattuja viestipohjia joita client
voi käyttää sellaisenaan sen sijaan että käyttäjä kirjoittaisi oman,
mahdollisesti huonomman promptin itse.

HUOM (Laatukontrolli, 24.7.2026): kurssimateriaali väitti importin
olevan "from mcp.server.fastmcp import base" - tämä EI toimi asennetulla
SDK-versiolla 1.28.1 (ImportError). Oikea polku tarkistettu suoraan
asennetusta paketista: "from mcp.server.fastmcp.prompts import base".
"""
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pydantic import Field

mcp = FastMCP("DocumentMCP", log_level="ERROR")

docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditure.",
    "outlook.pdf": "This document presents the projected future performance of the project.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}


@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string.",
)
def read_document(
    doc_id: str = Field(description="Id of the document to read"),
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string.",
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(description="The text to replace. Must match exactly, including whitespace."),
    new_str: str = Field(description="The new text to insert in place of the old text."),
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    if old_str not in docs[doc_id]:
        raise ValueError(f"old_str not found in document '{doc_id}'")
    docs[doc_id] = docs[doc_id].replace(old_str, new_str)
    return f"Document '{doc_id}' updated."


@mcp.tool(
    name="list_documents",
    description="List the IDs of all documents currently available.",
)
def list_documents():
    return list(docs.keys())


# --- Resources (lisätty 22.7.2026) ---
# Suora resurssi: kiinteä URI, palauttaa aina koko dokumenttilistan.
# Käyttötarkoitus: esim. @-automaattitäydennyksen ehdotuslista.
@mcp.resource(
    "docs://documents",
    mime_type="application/json",
)
def list_docs() -> list[str]:
    return list(docs.keys())


# Templatoitu resurssi: {doc_id} poimitaan automaattisesti URI:sta ja
# annetaan funktiolle argumenttina. Käyttötarkoitus: kun käyttäjä
# valitsee tietyn dokumentin (esim. "@deposition.md"), sen sisältö
# haetaan suoraan tämän kautta ilman erillistä työkalukutsua.
@mcp.resource(
    "docs://documents/{doc_id}",
    mime_type="text/plain",
)
def fetch_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")
    return docs[doc_id]


# --- Prompts (lisätty 24.7.2026) ---
# Valmiiksi hiottu, testattu viestipohja dokumentin muotoiluun
# Markdown-muotoon. Client voi käyttää tätä suoraan sen sijaan että
# käyttäjä kirjoittaisi oman, vähemmän tarkan pyynnön itse.
@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format.",
)
def format_document(
    doc_id: str = Field(description="Id of the document to format"),
) -> list[base.Message]:
    prompt = f"""
Your goal is to reformat a document to be written with markdown syntax.

The id of the document you need to reformat is:

{doc_id}

Add in headers, bullet points, tables, etc as necessary. Feel free to add in extra formatting.
Use the 'edit_document' tool to edit the document. After the document has been reformatted...
"""
    return [
        base.UserMessage(prompt)
    ]


if __name__ == "__main__":
    mcp.run()
