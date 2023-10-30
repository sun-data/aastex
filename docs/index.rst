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
    import astropy.units as u
    import astropy.constants
    import aastex

    # Modify matplotlib defaults to use Latex backend
    # with correct font family and size
    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 9
    plt.rcParams['lines.linewidth'] = 1

    # Define an object representing the Latex document
    doc = aastex.Document()

    # Define the title of the article
    title = aastex.Title("An Interesting Article")
    doc.append(title)

    # Define the author of the paper and their affiliated organization
    msu = aastex.Affiliation(
        'Montana State University, Department of Physics, '
        'P.O. Box 173840, Bozeman, MT 59717, USA'
    )
    author = aastex.Author('Roy T. Smart', msu)
    doc.append(author)

    # Define the abstract of the article
    abstract = aastex.Abstract()
    abstract.packages.append(aastex.Package("lipsum"))
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")
    doc.append(abstract)

    # Define the speed of light as a variable that can be used in the document
    doc.set_variable_quantity(
        name="speedOfLight",
        value=astropy.constants.c.to(u.km / u.s),
        scientific_notation=True,
        digits_after_decimal=4,
    )

    # Define a column-width figure with random data
    fig, ax = plt.subplots(
        figsize=(aastex.column_width_inches, 2),
        constrained_layout=True,
    )
    x = np.linspace(-6, 6, num=101)[..., np.newaxis]
    y = np.sinc(x) + np.random.normal(scale=0.1, size=(101, 11))
    ax.plot(*np.broadcast_arrays(x, y))
    figure = aastex.Figure("data")
    figure.add_fig(fig, width=None)
    plt.close(fig)
    figure.add_caption(aastex.NoEscape(
        r"Here is a figure caption. \lipsum[5-5]"
    ))

    # Define the introduction of the article
    intro = aastex.Section("Introduction")
    intro.packages.append(aastex.Package("lipsum"))
    intro.append(
        rf"Here is a citation \citep{{knuth:1984}}. "
        rf"The speed of light is \speedOfLight. "
        rf"Here is a reference to Section {intro}. "
        rf"Here is a reference to Figure {figure}. "
        rf"\lipsum[2-2]"
    )
    intro.append(figure)
    intro.append(r"\lipsum[3-5]")
    doc.append(intro)

    # Add the bibliography from sources.bib
    doc.append(aastex.Bibliography("sources"))

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
