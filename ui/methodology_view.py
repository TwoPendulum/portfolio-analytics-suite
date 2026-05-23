import os
import re
from pathlib import Path

import streamlit as st


def _parse_sections(content: str):
    """Parse markdown content into sections keyed by ## headers."""
    sections = []
    current_title = ""
    current_body = []
    for line in content.split("\n"):
        if line.startswith("## "):
            if current_title or current_body:
                sections.append((current_title, "\n".join(current_body).strip()))
            current_title = line[3:].strip()
            current_body = []
        else:
            current_body.append(line)
    if current_title or current_body:
        sections.append((current_title, "\n".join(current_body).strip()))
    return sections


def _render_markdown_with_latex(text: str):
    """Render markdown text with $$...$$ blocks handled by st.latex."""
    parts = re.split(r"(\$\$.*?\$\$)", text, flags=re.DOTALL)
    for part in parts:
        if part.startswith("$$") and part.endswith("$$"):
            latex = part[2:-2].strip()
            st.latex(latex)
        else:
            stripped = part.strip()
            if stripped:
                st.markdown(stripped)


def render_methodology(docs_dir: str = "docs"):
    """Render the methodology tab with language toggle and section expanders."""
    st.title("Methodology")

    # Language toggle
    lang_options = ["中文", "English"]
    if "methodology_language" not in st.session_state:
        st.session_state.methodology_language = "中文"

    selected_lang = st.radio(
        "Language / 语言",
        lang_options,
        horizontal=True,
        key="methodology_lang_toggle",
        index=0 if st.session_state.methodology_language == "中文" else 1,
    )
    st.session_state.methodology_language = selected_lang

    # Determine file
    lang_code = "zh" if selected_lang == "中文" else "en"
    doc_dir = Path(docs_dir)
    doc_path = doc_dir / f"methodology_{lang_code}.md"

    if not doc_path.exists():
        st.error(f"Documentation file not found: {doc_path}")
        return

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Expand all toggle
    expand_all = st.checkbox("Expand All / 全部展开", value=False, key="expand_all_methodology")

    # Extract sections
    sections = _parse_sections(content)

    for idx, (title, body) in enumerate(sections):
        # Sections 1-2 expanded by default, rest collapsed
        default_expanded = expand_all or idx < 2
        with st.expander(title, expanded=default_expanded):
            _render_markdown_with_latex(body)

    # Footer
    st.markdown("---")
    st.caption(
        "This methodology documentation is maintained as a living document. "
        "Last updated: 2026-05-23"
    )
