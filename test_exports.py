from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


CONTENT = """
NON-DISCLOSURE AGREEMENT

1. CONFIDENTIALITY

The parties agree to protect confidential information.

2. TERM

This draft remains subject to the agreed terms.

Review Notice

This AI-generated draft should be reviewed by a qualified legal professional before signing.
"""


def test_txt_export():

    response = client.post(

        "/export/txt",

        json={

            "document_type": "NDA",

            "content": CONTENT,

            "terms": "Confidentiality",
        },
    )

    assert response.status_code == 200

    assert (
        b"NON-DISCLOSURE AGREEMENT"
        in response.content
    )


def test_docx_export():

    response = client.post(

        "/export/docx",

        data={

            "document_type": "NDA",

            "content": CONTENT,
        },
    )

    assert response.status_code == 200

    # DOCX files are ZIP-based.

    assert (
        response.content[:2]
        == b"PK"
    )


def test_pdf_export():

    response = client.post(

        "/export/pdf",

        data={

            "document_type": "NDA",

            "content": CONTENT,
        },
    )

    assert response.status_code == 200

    assert (
        response.content.startswith(
            b"%PDF"
        )
    )