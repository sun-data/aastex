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
    import wand.image
    import IPython

    path_pdf = pathlib.Path("../_readthedocs/html/an_interesting_article")

    title = aastex.Title("An Interesting Article")

    abstract = aastex.Abstract()
    abstract.escape = False
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")

    intro = pylatex.Section("Introduction")
    intro.escape = False
    intro.append("Some text introducing the contents of the article")
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

    path_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc.generate_pdf(filepath=str(path_pdf.resolve()))

    filename = f"{str(path_pdf.resolve())}.pdf"
    url = f"https://aastex.readthedocs.io/en/latest/an_interesting_article.pdf"
    print(url)
    IPython.display.IFrame(url=url)
    #wand.image.Image(filename=filename, resolution=100)

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
