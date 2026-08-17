Introduction
============

:mod:`aastex` lets you write an article for the journals of the American
Astronomical Society as a Python program.
It extends `PyLaTeX <https://github.com/JelteF/PyLaTeX>`_ with the pieces of the
`AASTeX LaTeX package <https://journals.aas.org/aastex-package-for-manuscript-preparation/>`_
that a manuscript needs: titles, authors and their affiliations, acronyms,
sections, figures, and bibliographies.

In an ordinary manuscript, the numbers quoted in the prose and the figures
printed beside them are copied out of an analysis by hand, and they begin to
drift from that analysis as soon as it changes.
Writing the article as a program removes the copying step.
Figures are drawn by the same code that produced the result, and quantities are
declared as LaTeX macros computed from Python values, so the text cannot
disagree with the analysis behind it.

Since :mod:`aastex` is built on PyLaTeX, anything that library can express is
available here as well;
see the `PyLaTeX documentation <https://jeltef.github.io/PyLaTeX/current/>`_
for the underlying model of documents, environments, and commands.

|

Installation
============

:mod:`aastex` is available on PyPI and can be installed using pip:

.. code-block:: bash

    pip install aastex

Compiling an article also requires a LaTeX installation providing the
dependencies of the AASTeX class.
On Debian and Ubuntu:

.. code-block:: bash

    sudo apt-get install texlive-publishers texlive-science cm-super latexmk

|

Writing an article
==================

The example below builds a small but complete article, one piece at a time.
Each step appends to the same :class:`aastex.Document`, which is compiled at the
end.

Start by configuring :mod:`matplotlib` to render text with LaTeX, so that the
figures use the same fonts as the surrounding article, and create the document.
:class:`aastex.Document` defaults to the AASTeX class in its two column style.

.. jupyter-execute::

    import pathlib
    import numpy as np
    import matplotlib.pyplot as plt
    import astropy.units as u
    import astropy.constants
    import aastex

    plt.rcParams['text.usetex'] = True
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['font.size'] = 9
    plt.rcParams['lines.linewidth'] = 1

    doc = aastex.Document()

Every article needs a title, and one or more authors.
An :class:`aastex.Author` carries an :class:`aastex.Affiliation`, and optionally
an ORCID and an email address, which AASTeX prints in the front matter.

.. jupyter-execute::

    title = aastex.Title("An Interesting Article")
    doc.append(title)

    msu = aastex.Affiliation(
        'Montana State University, Department of Physics, '
        'P.O. Box 173840, Bozeman, MT 59717, USA'
    )
    author = aastex.Author(
        name='Roy T. Smart',
        affiliation=msu,
        email="roytsmart@gmail.com",
        corresponding=True,
    )
    doc.append(author)

An :class:`aastex.Acronym` is defined once and then used in the prose through a
macro named after it, ``\NASA`` in this case.
The first use in the text expands to the full phrase followed by the
abbreviation, and later uses give the abbreviation alone, so the convention is
applied for you no matter how the text is later rearranged.

.. jupyter-execute::

    nasa = aastex.Acronym("NASA", "National Aeronautics and Space Administration")
    doc.preamble.append(nasa)

The abstract is a container like any other section of the document, so text is
appended to it.
Here :mod:`lipsum` provides placeholder prose.

.. jupyter-execute::

    abstract = aastex.Abstract()
    abstract.packages.append(aastex.Package("lipsum"))
    abstract.append("Some text summarizing the article. ")
    abstract.append(r"\lipsum[1-1]")
    doc.append(abstract)

This is the step that keeps the article honest.
:meth:`aastex.Document.set_variable_quantity` defines a LaTeX macro from an
:class:`astropy.units.Quantity`, formatting the value and its units, so the
prose can cite ``\speedOfLight`` instead of a number typed by hand.
Recompute the value and the article follows.

.. jupyter-execute::

    doc.set_variable_quantity(
        name="speedOfLight",
        value=astropy.constants.c.to(u.km / u.s),
        scientific_notation=True,
        digits_after_decimal=4,
    )

Figures are created from :mod:`matplotlib` figures using
:meth:`aastex.Figure.add_fig`.
The label given to :class:`aastex.Figure` names both the LaTeX label and the
image file saved next to the article, and the plot may be closed once it has
been added, since it is not saved until the document is compiled.
The constants :attr:`aastex.column_width_inches` and
:attr:`aastex.text_width_inches` give the width of a column and of the full page,
which are the two useful figure widths in a two column article.

.. jupyter-execute::

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

Now the body of the article.
Note how the section and the figure are formatted into the string:
:class:`aastex.Section` and :class:`aastex.Figure` render as references to
themselves, so numbering is never written by hand and never goes stale when the
document is reordered.
The acronym and the variable defined above are used here as ``\NASA`` and
``\speedOfLight``.

.. jupyter-execute::

    intro = aastex.Section("Introduction")
    intro.packages.append(aastex.Package("lipsum"))
    intro.append(
        rf"Here is a citation \citep{{knuth:1984}}. "
        rf"The speed of light is \speedOfLight. "
        rf"Here is a reference to Section {intro}. "
        rf"Here is a reference to Figure {figure}. "
        rf"Here is an acronym: \NASA. "
        rf"Here is the acronym again: \NASA. "
        rf"\lipsum[2-2]"
    )
    intro.append(figure)
    intro.append(r"\lipsum[3-5]")
    doc.append(intro)

Finally the bibliography, which reads the BibTeX file ``sources.bib`` sitting
beside the article, and resolves the citation used above.

.. jupyter-execute::

    doc.append(aastex.Bibliography("sources"))

:meth:`aastex.Document.generate_pdf` writes the ``.tex`` file, saves each figure
next to it, copies in the AASTeX class and bibliography style, and runs LaTeX.

.. jupyter-execute::

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

Preparing a submission
======================

The `AAS submission system <https://journals.aas.org/pre-submission-checklist-for-aas-journal-authors/>`_
requires every file of a manuscript to sit at the same directory level, since it
cannot parse subdirectories.
:meth:`aastex.Document.generate_archive` compiles the article and gathers the
``.tex`` file, the ``.bbl`` file required by the AAS conversion software, the
AASTeX class and bibliography style files, and every figure into a flat archive
which is ready to upload:

.. code-block:: python

    doc.generate_archive(
        pathlib.Path("an_interesting_article"),
        bibliography="sources.bib",
    )

Pass ``format="gztar"`` for a ``.tar.gz`` archive instead of a ``.zip``.

|

API Reference
=============

.. autosummary::
    :toctree: _autosummary
    :template: module_custom.rst
    :recursive:

    aastex

|

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
