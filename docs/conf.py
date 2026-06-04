# Sphinx configuration for ibx-cli documentation
import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "ibx-cli"
copyright = "2026, ibx-cli contributors"
author = "ibx-cli contributors"

from ibxcli import __version__ as version  # noqa: E402

release = version

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx_click",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# sphinx_click settings
click_command = "ibxcli.cli.main:cli"

# Autodoc
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": False,
}
