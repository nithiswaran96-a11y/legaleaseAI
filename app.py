import html
import os
import re

import requests
import streamlit as st


BACKEND_URL = os.getenv(
    "BACKEND_URL",
    "http://127.0.0.1:8000",
).rstrip("/")
DOCUMENT_TYPES = (
    "Employment contract",
    "Lease agreement",
    "Non-disclosure agreement",
    "Freelance contract",
    "Service agreement",
    "Other",
)
EXPORTS = {
    "TXT": ("txt", "text/plain", ".txt"),
    "DOCX": (
        "docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
    ),
    "PDF": ("pdf", "application/pdf", ".pdf"),
}


def export_filename(document_type, extension):
    safe_type = re.sub(r"[^A-Za-z0-9._-]+", "_", document_type.strip())
    safe_type = safe_type.strip("._") or "legal_document"
    return f"{safe_type}_LegalEase{extension}"

st.set_page_config(
    page_title="LegalEase | Draft workspace",
    page_icon="LE",
    layout="wide",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
    :root {
        --ink: #17231f;
        --muted: #68756f;
        --paper: #f4f5f0;
        --line: #dce2dc;
        --green: #176b52;
        --green-dark: #0f4f3d;
        --coral: #ce6049;
    }
    .stApp {
        background-color: var(--paper);
        background-image: repeating-linear-gradient(0deg, transparent, transparent 35px, rgba(23, 35, 31, .025) 36px);
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }
    .block-container { max-width: 1440px; padding-top: 2rem; padding-bottom: 3rem; }
    h1, h2, h3 { color: var(--ink); }
    h1 { font-family: 'Playfair Display', Georgia, serif; font-size: 3rem; line-height: 1.08; }
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, .82);
        border: 1px solid var(--line);
        border-radius: 6px;
    }
    [data-testid="stForm"] { padding: 1.2rem 1.35rem; }
    label, [data-testid="stWidgetLabel"] p { color: var(--ink); font-weight: 600; }
    input, textarea, [data-baseweb="select"] > div {
        border-color: var(--line) !important;
        border-radius: 4px !important;
        background: #fff !important;
    }
    [data-testid="stTextArea"] textarea { line-height: 1.55; }
    .eyebrow {
        color: var(--green);
        font-family: 'DM Mono', monospace;
        font-size: .76rem;
        font-weight: 500;
        letter-spacing: 0;
        text-transform: uppercase;
    }
    .brand-mark {
        display: inline-grid;
        width: 38px;
        height: 38px;
        place-items: center;
        margin-right: 10px;
        border: 1px solid var(--green);
        border-radius: 50%;
        color: var(--green);
        font-family: 'DM Mono', monospace;
        font-size: .72rem;
        vertical-align: middle;
    }
    .status {
        margin-top: 1.35rem;
        color: var(--muted);
        font-family: 'DM Mono', monospace;
        font-size: .76rem;
        text-align: right;
    }
    .status-dot { color: var(--green); padding-right: 6px; }
    .status-down .status-dot { color: var(--coral); }
    .section-head { margin: 1.6rem 0 .75rem; }
    .draft-meta {
        color: var(--muted);
        font-family: 'DM Mono', monospace;
        font-size: .76rem;
        margin: 0 0 .7rem;
    }
    div.stButton > button[kind="primary"] {
        background: var(--green);
        border: 1px solid var(--green);
        border-radius: 4px;
        min-height: 2.8rem;
        font-weight: 700;
    }
    div.stButton > button[kind="primary"]:hover {
        background: var(--green-dark);
        border-color: var(--green-dark);
    }
    div.stDownloadButton > button, div.stButton > button {
        border-radius: 4px;
    }
    @media (max-width: 700px) {
        .block-container { padding: 1.2rem 1rem 2rem; }
        h1 { font-size: 2.35rem; }
        .status { margin-top: 0; text-align: left; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.session_state.setdefault("document_content", "")
st.session_state.setdefault("document_type", "")
st.session_state.setdefault("prepared_exports", {})

header, status_column = st.columns([2.5, 1])
with header:
    st.markdown(
        '<h1><span class="brand-mark">LE</span>LegalEase</h1>',
        unsafe_allow_html=True,
    )
with status_column:
    try:
        requests.get(f"{BACKEND_URL}/health", timeout=2).raise_for_status()
        st.markdown(
            '<p class="status"><span class="status-dot">●</span>API connected</p>',
            unsafe_allow_html=True,
        )
    except requests.RequestException:
        st.markdown(
            '<p class="status status-down"><span class="status-dot">●</span>API unavailable</p>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<p class="eyebrow">Document drafting workspace</p>',
    unsafe_allow_html=True,
)

compose_column, draft_column = st.columns([0.88, 1.12], gap="large")

with compose_column:
    st.markdown(
        '<div class="section-head"><span class="eyebrow">01 / Compose</span></div>',
        unsafe_allow_html=True,
    )
    with st.form("document_request"):
        selected_type = st.selectbox("Document type", DOCUMENT_TYPES)
        if selected_type == "Other":
            document_type = st.text_input(
                "Name the document",
                placeholder="e.g. Consulting agreement",
            )
        else:
            document_type = selected_type

        parties = st.text_area(
            "Parties",
            placeholder="Names, legal entities, and roles",
            height=110,
        )
        effective_date = st.text_input(
            "Effective date",
            placeholder="e.g. 1 October 2026",
        )
        terms = st.text_area(
            "Key terms",
            placeholder="Scope, payment, duration, responsibilities, and other agreed terms",
            height=190,
        )
        submitted = st.form_submit_button(
            "Generate draft",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not document_type.strip() or not parties.strip() or not terms.strip() or not effective_date.strip():
            st.warning("Complete each field to generate a draft.")
        else:
            try:
                with st.spinner("Drafting document..."):
                    response = requests.post(
                        f"{BACKEND_URL}/generate",
                        json={
                            "document_type": document_type,
                            "parties": parties,
                            "terms": terms,
                            "effective_date": effective_date,
                        },
                        timeout=120,
                    )
                    response.raise_for_status()
                generated = response.json()
                st.session_state.document_content = generated["content"]
                st.session_state.document_type = generated["document_type"]
                st.session_state.prepared_exports = {}
                st.success("Draft generated.")
            except requests.RequestException as error:
                detail = error.response.text if error.response is not None else str(error)
                st.error(f"Could not generate the draft: {detail}")

with draft_column:
    st.markdown(
        '<div class="section-head"><span class="eyebrow">02 / Review and export</span></div>',
        unsafe_allow_html=True,
    )
    if st.session_state.document_content:
        draft_type = st.session_state.document_type
        st.markdown(
            f'<p class="draft-meta">{html.escape(draft_type.upper())} &nbsp; / &nbsp; EDITABLE DRAFT</p>',
            unsafe_allow_html=True,
        )
        content = st.text_area(
            "Draft text",
            key="document_content",
            height=470,
            label_visibility="collapsed",
        )

        logo = st.file_uploader(
            "Optional logo for DOCX and PDF",
            type=["png", "jpg", "jpeg"],
            help="PNG or JPEG, up to 5 MB.",
        )
        logo_bytes = logo.getvalue() if logo is not None else None
        if logo_bytes and len(logo_bytes) > 5 * 1024 * 1024:
            st.error("The logo must be 5 MB or smaller.")
            logo_bytes = None

        export_columns = st.columns(3)
        for column, label in zip(export_columns, EXPORTS):
            endpoint, mime_type, extension = EXPORTS[label]
            with column:
                if st.button(f"Prepare {label}", key=f"prepare_{endpoint}", use_container_width=True):
                    try:
                        with st.spinner(f"Preparing {label}..."):
                            if endpoint == "txt":
                                response = requests.post(
                                    f"{BACKEND_URL}/export/txt",
                                    json={"document_type": draft_type, "content": content},
                                    timeout=30,
                                )
                            else:
                                files = {}
                                if logo_bytes:
                                    files["logo"] = (
                                        logo.name,
                                        logo_bytes,
                                        logo.type or "application/octet-stream",
                                    )
                                response = requests.post(
                                    f"{BACKEND_URL}/export/{endpoint}",
                                    data={"document_type": draft_type, "content": content},
                                    files=files,
                                    timeout=60,
                                )
                            response.raise_for_status()
                        st.session_state.prepared_exports[endpoint] = {
                            "data": response.content,
                            "content": content,
                            "document_type": draft_type,
                            "logo": logo_bytes,
                        }
                    except requests.RequestException as error:
                        detail = error.response.text if error.response is not None else str(error)
                        st.error(f"Could not prepare {label}: {detail}")

        prepared_columns = st.columns(3)
        for column, label in zip(prepared_columns, EXPORTS):
            endpoint, mime_type, extension = EXPORTS[label]
            prepared = st.session_state.prepared_exports.get(endpoint)
            if (
                prepared
                and prepared["content"] == content
                and prepared["document_type"] == draft_type
                and prepared["logo"] == logo_bytes
            ):
                with column:
                    filename = export_filename(draft_type, extension)
                    st.download_button(
                        f"Download {label}",
                        data=prepared["data"],
                        file_name=filename,
                        mime=mime_type,
                        key=f"download_{endpoint}",
                        use_container_width=True,
                    )

        st.caption(
            "AI-generated drafts are not legal advice. Have a qualified legal professional review this document before signing or relying on it."
        )
    else:
        st.info("Your draft will appear here. Complete the form and generate a document to begin editing.")