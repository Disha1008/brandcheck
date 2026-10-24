"""Repeatable local API smoke test. Run: python tests/smoke_test.py"""
import os
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from docx import Document
from fastapi.testclient import TestClient

fd, db_path = tempfile.mkstemp(suffix=".db")
os.close(fd)
os.unlink(db_path)
os.environ["DATABASE_URL"] = "sqlite:///" + db_path
os.environ["SECRET_KEY"] = "brandcheck-smoke-test-secret-key-long-enough"

# Import only after the temporary database environment is configured.
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from main import app


def main():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200

        def get_token(email, password):
            response = client.post("/auth/login", json={"email": email, "password": password})
            assert response.status_code == 200, response.text
            return response.json()["access_token"]

        creator = get_token("creator@freshsip.com", "creator123")
        reviewer = get_token("reviewer@freshsip.com", "reviewer123")
        admin = get_token("admin@freshsip.com", "admin123")
        hc = {"Authorization": f"Bearer {creator}"}
        hr = {"Authorization": f"Bearer {reviewer}"}
        ha = {"Authorization": f"Bearer {admin}"}

        # Create and check a draft, including a term and unsupported claim.
        response = client.post("/drafts", headers=hc, json={
            "title": "Smoke test",
            "content": "Fresh Sip cures every cold. FreshSip is cheap."
        })
        assert response.status_code == 201, response.text
        draft_id = response.json()["id"]
        response = client.post(f"/drafts/{draft_id}/check", headers=hc)
        assert response.status_code == 200, response.text
        findings = response.json()
        assert any(f["issue_type"] == "product_name" for f in findings)
        assert any(f["issue_type"] == "unsupported_claim" for f in findings)

        # Corrections apply to the exact checked span and stale the other findings.
        term_finding = next(f for f in findings if f["issue_type"] == "product_name")
        response = client.patch(f"/drafts/{draft_id}/findings/{term_finding['id']}",
                                headers=hc, json={"action": "accept"})
        assert response.status_code == 200, response.text
        draft = client.get(f"/drafts/{draft_id}", headers=hc).json()
        assert draft["content"].startswith("FreshSip cures every cold.")
        assert any(f["status"] == "stale" for f in client.get(f"/drafts/{draft_id}/findings", headers=hc).json())

        # Submit and reviewer decision.
        assert client.post(f"/drafts/{draft_id}/check", headers=hc).status_code == 200
        assert client.post(f"/drafts/{draft_id}/submit", headers=hc).status_code == 200
        response = client.post(f"/drafts/{draft_id}/review", headers=hr,
                               json={"decision": "request_changes", "comment": "Verify the claim."})
        assert response.status_code == 200, response.text
        assert client.get("/insights/summary", headers=hr).status_code == 200

        # Import both supported document types.
        response = client.post("/drafts/import", headers=hc,
            files={"file": ("post.txt", b"A plain text import.", "text/plain")})
        assert response.status_code == 201, response.text
        document_buffer = BytesIO(); doc = Document(); doc.add_paragraph("A Word document import."); doc.save(document_buffer)
        response = client.post("/drafts/import", headers=hc,
            files={"file": ("post.docx", document_buffer.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
        assert response.status_code == 201, response.text
        assert "Word document import" in response.json()["content"]

        # Fact source/expiry metadata and update route.
        response = client.post("/facts", headers=ha, json={"code": "F-004", "statement": "Verified fact.",
            "category": "general", "source_url": "https://example.org", "expires_at": "2027-01-01"})
        assert response.status_code == 201, response.text
        fact_id = response.json()["id"]
        response = client.put(f"/facts/{fact_id}", headers=ha, json={"code": "F-004", "statement": "Updated fact.",
            "category": "general", "source_url": "https://example.org/source", "expires_at": "2027-02-01"})
        assert response.status_code == 200, response.text

        # Expired approved facts must not be treated as supporting evidence.
        response = client.post("/facts", headers=ha, json={"code": "F-005", "statement": "A health claim fact that has expired.",
            "category": "health", "expires_at": "2020-01-01"})
        assert response.status_code == 201, response.text
        expired_draft = client.post("/drafts", headers=hc, json={"title": "Expired fact test", "content": "This product cures every illness."}).json()
        exp_check = client.post(f"/drafts/{expired_draft['id']}/check", headers=hc)
        assert exp_check.status_code == 200, exp_check.text
        assert any(f["issue_type"] == "outdated_fact" for f in exp_check.json())

        # Visual asset exact-match check.
        image = Image.new("RGB", (32, 24), (30, 120, 210))
        buffer = BytesIO(); image.save(buffer, format="PNG"); raw = buffer.getvalue()
        response = client.post("/assets/palette", headers=ha, json={"name":"Primary Blue","hex_color":"#1E78D2"})
        assert response.status_code == 201, response.text
        assert len(client.get("/assets/palette", headers=hc).json()) == 1
        response = client.post("/assets", headers=ha, files={"file": ("logo.png", raw, "image/png")})
        assert response.status_code == 201, response.text
        response = client.post("/assets/check", headers=hc, files={"file": ("copy.png", raw, "image/png")})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "exact_match"
        other = Image.new("RGB", (32, 24), (240, 20, 20)); other_buffer = BytesIO(); other.save(other_buffer, format="PNG")
        response = client.post("/assets/check", headers=hc, files={"file": ("unapproved.png", other_buffer.getvalue(), "image/png")})
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "not_in_library"

        # Role boundary: creators cannot change approved facts.
        response = client.post("/facts", headers=hc, json={"code": "F-X", "statement": "No", "category": "general"})
        assert response.status_code == 403, response.text
        print("BrandCheck API smoke tests passed.")


if __name__ == "__main__":
    try:
        main()
    finally:
        try: os.unlink(db_path)
        except OSError: pass
