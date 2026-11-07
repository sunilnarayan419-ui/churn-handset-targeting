"""Sphinx configuration for the Churn Handset Targeting documentation.

Build (see docs/development/development-workflow.md):

    uv sync --extra api --group sphinx-docs
    uv run sphinx-build -b html docs docs/_build/html
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

REPO_URL = "https://github.com/sunilnarayan419-ui/churn-handset-targeting"

# Read the version statically so that building the docs never needs the package metadata.
_init = (ROOT / "src" / "churn_targeting" / "__init__.py").read_text(encoding="utf-8")
_match = re.search(r'__version__\s*=\s*"([^"]+)"', _init)

# -- Project information ------------------------------------------------------------------------
project = "Churn Handset Targeting"
author = "Sunil Mandloi"
copyright = "2026, Sunil Mandloi (MIT License)"
release = _match.group(1) if _match else "0.0.0"
version = release

# -- General configuration ----------------------------------------------------------------------
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.extlinks",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.mermaid",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
language = "en"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "DATA_CARD.md"]
templates_path: list[str] = []

# Link to files that live outside docs/ (source, configs, workflows) on GitHub:
#   {repo}`src/churn_targeting/finance.py`
extlinks = {"repo": (f"{REPO_URL}/blob/main/%s", "%s")}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "sklearn": ("https://scikit-learn.org/stable/", None),
}

# -- MyST (Markdown) ----------------------------------------------------------------------------
myst_enable_extensions = ["amsmath", "colon_fence", "deflist", "dollarmath", "tasklist"]
myst_heading_anchors = 3

# -- autodoc ------------------------------------------------------------------------------------
# `neo4j` is an optional extra and is imported lazily by graph.py; mock it so that the API
# reference builds without installing a database driver.
autodoc_mock_imports = ["neo4j"]
autodoc_member_order = "bysource"
autodoc_default_options = {"members": True, "show-inheritance": True}
typehints_document_rtype = True
typehints_defaults = "comma"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Mermaid ------------------------------------------------------------------------------------
# Diagrams are rendered client-side. The neutral theme stays legible in Furo's light and dark modes.
mermaid_version = "11.4.1"
mermaid_init_js = "mermaid.initialize({startOnLoad: true, theme: 'neutral'});"

# -- HTML output (Furo) -------------------------------------------------------------------------
html_theme = "furo"
html_title = "Churn Handset Targeting"
html_static_path = ["assets"]
html_css_files = ["custom.css"]
html_favicon = "icon.svg"

html_theme_options = {
    "light_logo": "logo-light.svg",
    "dark_logo": "logo-dark.svg",
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "source_repository": f"{REPO_URL}/",
    "source_branch": "main",
    "source_directory": "docs/",
    "light_css_variables": {
        "color-brand-primary": "#0b7a8a",
        "color-brand-content": "#0b7a8a",
    },
    "dark_css_variables": {
        "color-brand-primary": "#4fd1de",
        "color-brand-content": "#4fd1de",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": REPO_URL,
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">'
                '<path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 '
                "0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53"
                ".63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
                "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36"
                ".09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75"
                "-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0"
                '-4.42-3.58-8-8-8z"></path></svg>'
            ),
            "class": "",
        },
    ],
}
