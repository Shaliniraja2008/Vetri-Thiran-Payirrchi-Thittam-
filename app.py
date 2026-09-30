import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import streamlit as st

import config
from ai_core.generator import format_docx, format_html_preview, format_pdf, sanitize_text

st.set_page_config(page_title="LegalEase", layout="centered")

# ---- Header -------------------------------------------------------------
_, mid, _ = st.columns([1, 2, 1])
with mid:
    if os.path.exists(config.WEB_LOGO_PATH):
        st.image(config.WEB_LOGO_PATH, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align:center;'>LegalEase</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center;'>AI Legal Document Generator</h2>", unsafe_allow_html=True)

# ---- Inputs -------------------------------------------------------------
document_type = st.text_input("Document Type (Ex: Agreement, Contract, NDA)")
parties = st.text_area("Parties Involved")
terms = st.text_area("Terms & Conditions (Use semicolons for bullet points)")
dates = st.text_input("Effective Date")

if st.button("Generate Document"):
    if not all(v.strip() for v in (document_type, parties, terms, dates)):
        st.warning("Please fill in all four fields.")
    else:
        try:
            with st.spinner("Drafting your document with Gemini..."):
                resp = requests.post(
                    f"{config.API_URL}/generate",
                    json={"document_type": document_type, "parties": parties,
                          "terms": terms, "dates": dates},
                    timeout=180,
                )
            if resp.status_code == 200:
                st.session_state.generated_text = sanitize_text(resp.json()["document"])
                st.session_state.doc_type = document_type
                st.session_state.terms = terms
                st.session_state.show_edit = False
                st.session_state.pop("editor", None)
            else:
                st.error(f"Backend error: {resp.json().get('detail', resp.text)}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot reach the FastAPI backend. Start it with: "
                     "uvicorn legalEaseAPI.main:app --reload")
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")

# ---- Preview, edit, download -------------------------------------------
if st.session_state.get("generated_text"):
    st.success("Document Generated Successfully!")

    if st.button("✏️ Click to Edit Document"):
        st.session_state.show_edit = True
        st.session_state.editor = st.session_state.generated_text
    if st.session_state.get("show_edit"):
        st.text_area("Edit Document Below:", key="editor", height=300)
        st.session_state.generated_text = st.session_state.editor

    text = st.session_state.generated_text
    doc_type = st.session_state.doc_type
    doc_terms = st.session_state.get("terms", "")

    st.markdown(
        "<div style='background:#0f172a;color:#e2e8f0;padding:20px;border-radius:10px;"
        f"max-height:420px;overflow-y:auto;'>{format_html_preview(text)}</div>",
        unsafe_allow_html=True,
    )

    fname = doc_type.strip().replace(" ", "_").lower() or "legal_document"
    st.download_button("📄 Download as .TXT", data=text, file_name=f"{fname}.txt", mime="text/plain")
    st.download_button(
        "📝 Download as .DOCX", data=format_docx(text, doc_type, doc_terms), file_name=f"{fname}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    st.download_button(
        "📕 Download as .PDF", data=format_pdf(text, doc_type, doc_terms),
        file_name=f"{fname}.pdf", mime="application/pdf",
    )
else:
    st.info("Click 'Generate Document' to start")
