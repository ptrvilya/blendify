# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
sys.path.append("..")
import blendify

project = 'Blendify'
copyright = '2025, Vladimir Guzov and Ilya Petrov'
author = 'Vladimir Guzov and Ilya Petrov'

version = blendify.__version__
release = blendify.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.napoleon',
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

source_suffix = ['.rst', '.md']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_title = "Blendify"

autosectionlabel_prefix_document = True

html_context = {
   "default_mode": "dark"
}


html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#3FDC55",
        "color-brand-content": "#4B9B28",
    },
    "dark_css_variables": {
        "color-brand-primary": "#CAFD6C",
        "color-brand-content": "#95FE6A",
    },
    "light_logo": "logo/blendify_logo_small.png",
    "dark_logo": "logo/blendify_logo_small.png",
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True


html_static_path = ['_static']
