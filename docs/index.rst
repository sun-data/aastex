Introduction
============

This Python library extends `PyLaTeX <https://github.com/JelteF/PyLaTeX>`_ to support the
AASTeX LaTeX package.

|

API Reference
=============

.. autosummary::
    :toctree: _autosummary
    :template: module_custom.rst
    :recursive:

    aastex

|

Example
=======

Here is a simple example showing some of the basic features of :mod:`aastex`.

.. jupyter-execute::

    import pathlib
    import pylatex
    import aastex
    import IPython

    title = aastex.Title("An Interesting Article")

    msu = aastex.Affiliation(
        'Montana State University, Department of Physics, '
        'P.O. Box 173840, Bozeman, MT 59717, USA'
    )

    author = aastex.Author('Roy T. Smart', msu)

    abstract = aastex.Abstract()
    abstract.escape = False
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")

    intro = pylatex.Section("Introduction")
    intro.escape = False
    intro.append(r"\lipsum[2-4]")

    doc = aastex.Document(
        documentclass="aastex631",
        document_options=["twocolumn"],
    )

    doc.packages.append(pylatex.Package("lipsum"))

    doc.append(title)
    doc.append(author)
    doc.append(abstract)
    doc.append(intro)

    path_pdf = pathlib.Path("an_interesting_article.pdf")
    doc.generate_pdf(filepath=path_pdf.with_suffix(""))

Which generates the following PDF:

.. jupyter-execute::
    :hide-code:

    import os

    path_build = pathlib.Path(os.environ.get("READTHEDOCS_OUTPUT", "_build")) / "html"
    path_pdf_new = path_pdf.rename(path_build / path_pdf.name)

    url = f"https://aastex.readthedocs.io/en/latest/{path_pdf.name}"
    IPython.display.IFrame(url, width=900, height=400)

|

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
