import copy

import pytest

import mcp_server as server


@pytest.fixture(autouse=True)
def restore_docs():
    """mcp_server.docs on moduulitason muuttuva sanakirja - palautetaan
    alkuperäiseen tilaan jokaisen testin jälkeen, jotta edit_document-testit
    eivät vuoda toisiinsa."""
    original = copy.deepcopy(server.docs)
    yield
    server.docs.clear()
    server.docs.update(original)


def test_list_documents_returns_all_ids():
    assert server.list_documents() == [
        "deposition.md",
        "report.pdf",
        "financials.docx",
        "outlook.pdf",
        "plan.md",
        "spec.txt",
    ]


def test_read_document_returns_content():
    content = server.read_document(doc_id="spec.txt")
    assert content == "These specifications define the technical requirements for the equipment."


def test_read_document_unknown_id_raises():
    with pytest.raises(ValueError, match="not found"):
        server.read_document(doc_id="unknown.txt")


def test_edit_document_replaces_matching_text():
    result = server.edit_document(
        doc_id="plan.md",
        old_str="implementation",
        new_str="rollout",
    )
    assert result == "Document 'plan.md' updated."
    assert "rollout" in server.docs["plan.md"]
    assert "implementation" not in server.docs["plan.md"]


def test_edit_document_unknown_id_raises():
    with pytest.raises(ValueError, match="not found"):
        server.edit_document(doc_id="unknown.txt", old_str="a", new_str="b")


def test_edit_document_missing_old_str_raises():
    with pytest.raises(ValueError, match="old_str not found"):
        server.edit_document(doc_id="spec.txt", old_str="ei löydy tekstistä", new_str="x")


def test_list_docs_resource_matches_list_documents():
    assert server.list_docs() == server.list_documents()


def test_fetch_doc_resource_returns_content():
    assert server.fetch_doc("financials.docx") == server.docs["financials.docx"]


def test_fetch_doc_resource_unknown_id_raises():
    with pytest.raises(ValueError, match="not found"):
        server.fetch_doc("unknown.txt")


def test_format_prompt_includes_doc_id():
    messages = server.format_document(doc_id="report.pdf")
    assert len(messages) == 1
    assert "report.pdf" in messages[0].content.text
