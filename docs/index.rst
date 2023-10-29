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

    # Modify matplotlib defaults to use Latex backend
    # with correct font family and size
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 9
    plt.rcParams['lines.linewidth'] = 1

    # Define the title of the article
    title = aastex.Title("An Interesting Article")

    # Define the author of the paper and their affiliated organization
    msu = aastex.Affiliation(
        'Montana State University, Department of Physics, '
        'P.O. Box 173840, Bozeman, MT 59717, USA'
    )
    author = aastex.Author('Roy T. Smart', msu)

    # Define the abstract of the article
    abstract = aastex.Abstract()
    abstract.packages.append(aastex.Package("lipsum"))
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")

    # Define the introduction of the article
    intro = aastex.Section("Introduction")
    intro.packages.append(aastex.Package("lipsum"))
    intro.append(r"\lipsum[2-4]")

    # Define a column-width figure with random data
    fig, ax = plt.subplots(
        figsize=(aastex.column_width_inches, 2),
        constrained_layout=True,
    )
    data = np.random.normal(size=(11, 11))
    ax.plot(data)
    figure = aastex.Figure("data")
    figure.add_fig(fig, width=None)
    figure.add_caption(aastex.NoEscape(
        r"Here is a figure caption. \lipsum[5-5]"
    ))
    plt.close(fig)

    # Define a new section of this article with some references
    methods = aastex.Section("Methods")
    methods.append(
        rf"Here is a reference to Section {intro}. "
        rf"Here is a reference to Figure {figure}. "
    )

    # Define a text-width figure with random data
    fig2, ax2 = plt.subplots(
        figsize=(aastex.text_width_inches, 2),
        constrained_layout=True,
    )
    x = np.linspace(-6, 6, num=101)[..., np.newaxis]
    y = np.sinc(x) + np.random.normal(scale=0.1, size=(101, 11))
    ax2.plot(*np.broadcast_arrays(x, y))
    figure2 = aastex.FigureStar("data2")
    figure2.add_fig(fig2, width=None)
    figure2.add_caption(aastex.NoEscape(
        r"Here is another figure caption. \lipsum[6-6]"
    ))
    plt.close(fig2)

    # Collect all of the above elements into a single document
    doc = aastex.Document()
    doc.append(title)
    doc.append(author)
    doc.append(abstract)
    doc.append(intro)
    doc.append(figure)
    doc.append(methods)
    doc.append(figure2)

    # Compile the document into a PDF
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
