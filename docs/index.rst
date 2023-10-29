Introduction
============

This Python library extends `PyLaTeX <https://github.com/JelteF/PyLaTeX>`_
to support the `AASTeX LaTeX package <https://journals.aas.org/aastex-package-for-manuscript-preparation/>`_.

Please see the `PyLaTeX documentation <https://jeltef.github.io/PyLaTeX/current/>`_
for more information on how to use this package.

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
    import numpy as np
    import matplotlib.pyplot as plt
    import aastex

    title = aastex.Title("An Interesting Article")

    msu = aastex.Affiliation(
        'Montana State University, Department of Physics, '
        'P.O. Box 173840, Bozeman, MT 59717, USA'
    )

    author = aastex.Author('Roy T. Smart', msu)

    abstract = aastex.Abstract()
    abstract.packages.append(aastex.Package("lipsum"))
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")

    intro = aastex.Section("Introduction")
    intro.packages.append(aastex.Package("lipsum"))
    intro.append(r"\lipsum[2-4]")

    fig, ax = plt.subplots(figsize=(aastex.column_width_inches, 2))
    data = np.random.normal(size=(11, 11))
    ax.plot(data)
    figure = aastex.Figure("data")
    figure.add_fig(fig, width=None)
    figure.add_caption(aastex.NoEscape(
        r"Here is a figure caption. \lipsum[5-5]"
    ))
    plt.close(fig)

    methods = aastex.Section("Methods")
    methods.append(
        rf"Here is a reference to Section {intro}. "
        rf"Here is a reference to Figure {figure}. "
    )

    doc = aastex.Document()
    doc.append(title)
    doc.append(author)
    doc.append(abstract)
    doc.append(intro)
    doc.append(figure)
    doc.append(methods)

    path_pdf = pathlib.Path("an_interesting_article.pdf")
    doc.generate_pdf(filepath=path_pdf.with_suffix(""))

Which outputs the following PDF:

.. jupyter-execute::
    :hide-code:

    import os
    import IPython

    try:
        path_build = pathlib.Path(os.environ["READTHEDOCS_OUTPUT"]) / "html"
        path_pdf_new = path_pdf.rename(path_build / path_pdf.name)

        url = f"https://aastex.readthedocs.io/en/latest/{path_pdf.name}"

    except KeyError:
        url = path_pdf.resolve()

    IPython.display.IFrame(url, width=900, height=400)

|

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
