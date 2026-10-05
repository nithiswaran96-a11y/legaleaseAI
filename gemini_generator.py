import time

from google import genai
from google.genai import types

from backend.config import settings


SYSTEM_INSTRUCTION = """
You are the LegalEase drafting assistant.

Create a professional legal-document DRAFT from the user's supplied information.

Do not invent:
- names
- dates
- addresses
- money amounts
- laws
- courts
- registrations
- facts

If an important detail is missing, use a clearly marked placeholder such as:

[INSERT INFORMATION]

Use clear headings and numbered clauses.

Keep the document internally consistent.

For semicolon-separated terms, incorporate every supplied term into an
appropriate clause.

Do not claim that the document is legally valid or enforceable.

Do not claim that the document is suitable for a particular jurisdiction
unless the user explicitly provides the jurisdiction.

Return plain text only.

Do not use Markdown code fences.

End the document with:

Review Notice

This AI-generated draft should be reviewed by a qualified legal professional
before signing or relying on it.
"""


class GeminiDocumentGenerator:

    def __init__(self):

        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. "
                "Add it to the .env file."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

    def generate_document(
        self,
        document_type: str,
        parties: str,
        terms: str,
        effective_date: str,
    ) -> str:

        prompt = f"""
Document Type:
{document_type}

Parties:
{parties}

Effective Date:
{effective_date}

Terms and Conditions:
{terms}

Create a professional legal document draft.

Use only the information supplied above.

Create:

1. Document title
2. Introduction / parties
3. Effective date
4. Definitions if required
5. Main terms and conditions
6. Responsibilities
7. Confidentiality if applicable
8. Termination if applicable
9. General provisions if applicable
10. Signature section
11. Review Notice

Do not invent missing facts.
Use placeholders when information is missing.
"""

        response = None

        for attempt in range(4):
            try:
                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.2,
                        max_output_tokens=5000,
                    ),
                )
                break

            except Exception as error:
                error_text = str(error)

                if (
                    "503" not in error_text
                    and "UNAVAILABLE" not in error_text
                ):
                    raise

                if attempt == 3:
                    raise

                time.sleep(2 ** attempt)

        text = (response.text or "").strip()

        if not text:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return text