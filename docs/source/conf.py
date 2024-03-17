import os
from importers import AddPath

lib_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "ugokukun"
)
with AddPath(lib_path):
    from __init__ import __author__, __version__

# -- Project information

project = "Ugoku-kun"
copyright = "2024, " + __author__
author = __author__

release = __version__
version = __version__

# -- General configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master/", None),
}
intersphinx_disabled_domains = ["std"]

templates_path = ["_templates"]

# -- Options for HTML output

html_theme = "sphinx_rtd_theme"

# -- Options for EPUB output
epub_show_urls = "footnote"

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "methods": True,
    "special-members": "__call__",
    "exclude-members": "_abc_impl",
    "show-inheritance": True,
}

autosummary_generate = True
autosummary_generate_overwrite = False
