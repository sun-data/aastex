Introduction
============

This Python library extends `PyLaTeX <https://github.com/JelteF/PyLaTeX>`_ to support the
AASTeX LaTeX package.

Example
=======

.. jupyter-execute::

    import pathlib
    import pylatex
    import aastex
    import IPython

    title = aastex.Title("An Interesting Article")

    abstract = aastex.Abstract()
    abstract.escape = False
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")

    intro = pylatex.Section("Introduction")
    intro.escape = False
    intro.append(r"\lipsum[2-4]")

    doc = aastex.Document(
        default_filepath=str(path_pdf),
        documentclass="aastex631",
        document_options=["twocolumn"],
    )

    doc.packages.append(pylatex.Package("lipsum"))

    doc.append(title)
    doc.append(abstract)
    doc.append(intro)

    path_pdf = pathlib.Path("an_interesting_article.pdf")
    doc.generate_pdf(filepath=path_pdf.with_suffix(""))

.. jupyter-execute::
    :hide-code:

    import os

    path_build = pathlib.Path(os.environ["READTHEDOCS_OUTPUT"]) / "html"
    path_pdf_new = path_pdf.rename(path_build / path_pdf.name)
    print(path_pdf_new)

    url = f"https://aastex.readthedocs.io/en/latest/{path_pdf.name}"
    print(url)
    IPython.display.IFrame(url, width=900, height=800)

|

API Reference
=============

.. autosummary::
    :toctree: _autosummary
    :template: module_custom.rst
    :recursive:

    aastex



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
