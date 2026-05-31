"""Resume Parser – Streamlit UI."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io
import json

import pandas as pd
import streamlit as st

from app.file_reader import read_file
from app.parser import parse_resume
from app.schemas import ResumeData

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Resume Parser", layout="wide")

# ─── Custom styling ────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .block-container { max-width: 900px; padding-top: 2rem; }
    .stJSON { border-radius: 8px; }
    div[data-testid="stExpander"] { border: 1px solid #e0e0e0; border-radius: 8px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─── Header ────────────────────────────────────────────────────────────────────
st.title("Resume Parser")
st.caption("Upload resumes (PDF, DOCX, or TXT) and get structured JSON output powered by LLM.")

# ─── Mode selection ────────────────────────────────────────────────────────────
mode = st.radio("Mode", ["Single Resume", "Bulk Upload"], horizontal=True)


# ─── Helper: flatten ResumeData to a flat dict for tabular export ──────────────
def flatten_resume(data: ResumeData) -> dict:
    return {
        "Name": data.name,
        "Email": data.email,
        "Phone": data.phone,
        "Summary": data.summary,
        "Skills": ", ".join(data.skills),
        "Experience": " | ".join(
            f"{e.role} @ {e.company} ({e.duration})" for e in data.experience
        ),
        "Education": " | ".join(
            f"{e.degree}, {e.institution} ({e.year})" for e in data.education
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLE RESUME MODE
# ═══════════════════════════════════════════════════════════════════════════════
if mode == "Single Resume":
    uploaded_file = st.file_uploader(
        "Drop your resume here",
        type=["pdf", "docx", "doc", "txt"],
        help="Supported formats: PDF, DOCX, TXT",
    )

    if uploaded_file is not None:
        if st.button("Parse Resume", type="primary", use_container_width=True):
            with st.spinner("Extracting structured data..."):
                try:
                    raw_text = read_file(uploaded_file.getvalue(), uploaded_file.name)

                    if not raw_text.strip():
                        st.error("Could not extract text from the file. Try a different format.")
                    else:
                        with st.expander("Raw Text Preview", expanded=False):
                            st.text(raw_text[:3000] + ("..." if len(raw_text) > 3000 else ""))

                        result = parse_resume(raw_text)
                        st.success("Parsing complete!")

                        tab_json, tab_pretty = st.tabs(["JSON Output", "Formatted View"])

                        with tab_json:
                            st.json(json.loads(result.model_dump_json(indent=2)))

                        with tab_pretty:
                            st.subheader(result.name)
                            if result.email or result.phone:
                                st.caption(f"{result.email}  •  {result.phone}")
                            if result.summary:
                                st.markdown(f"**Summary:** {result.summary}")
                            if result.skills:
                                st.markdown("**Skills**")
                                st.markdown(" • ".join(f"`{s}`" for s in result.skills))
                            if result.experience:
                                st.markdown("**Experience**")
                                for exp in result.experience:
                                    st.markdown(f"**{exp.role}** at {exp.company} ({exp.duration})")
                                    for h in exp.highlights:
                                        st.markdown(f"  - {h}")
                            if result.education:
                                st.markdown("**Education**")
                                for edu in result.education:
                                    st.markdown(f"- {edu.degree}, {edu.institution} ({edu.year})")

                        st.download_button(
                            label="Download JSON",
                            data=result.model_dump_json(indent=2),
                            file_name="parsed_resume.json",
                            mime="application/json",
                            use_container_width=True,
                        )

                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.info("Upload a resume file to get started.")


# ═══════════════════════════════════════════════════════════════════════════════
# BULK UPLOAD MODE
# ═══════════════════════════════════════════════════════════════════════════════
else:
    uploaded_files = st.file_uploader(
        "Drop multiple resumes here",
        type=["pdf", "docx", "doc", "txt"],
        accept_multiple_files=True,
        help="Upload multiple resumes at once. Supported: PDF, DOCX, TXT",
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)}** file(s) selected")

        if st.button("Parse All Resumes", type="primary", use_container_width=True):
            results: list[ResumeData] = []
            errors: list[str] = []
            progress = st.progress(0, text="Parsing resumes...")

            for i, f in enumerate(uploaded_files):
                progress.progress((i + 1) / len(uploaded_files), text=f"Parsing {f.name}...")
                try:
                    raw_text = read_file(f.getvalue(), f.name)
                    if raw_text.strip():
                        result = parse_resume(raw_text)
                        results.append(result)
                    else:
                        errors.append(f"{f.name}: Could not extract text")
                except Exception as e:
                    errors.append(f"{f.name}: {e}")

            progress.empty()

            if errors:
                with st.expander(f"{len(errors)} error(s)", expanded=False):
                    for err in errors:
                        st.warning(err)

            if results:
                st.success(f"Successfully parsed {len(results)} resume(s)!")

                # Show results table
                df = pd.DataFrame([flatten_resume(r) for r in results])
                st.dataframe(df, use_container_width=True)

                # Export buttons
                col1, col2, col3 = st.columns(3)

                with col1:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name="parsed_resumes.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )

                with col2:
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False, engine="openpyxl")
                    st.download_button(
                        label="Download Excel",
                        data=buffer.getvalue(),
                        file_name="parsed_resumes.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

                with col3:
                    all_json = json.dumps(
                        [r.model_dump() for r in results], indent=2
                    )
                    st.download_button(
                        label="Download JSON",
                        data=all_json,
                        file_name="parsed_resumes.json",
                        mime="application/json",
                        use_container_width=True,
                    )
    else:
        st.info("Upload multiple resume files to parse them in bulk.")
