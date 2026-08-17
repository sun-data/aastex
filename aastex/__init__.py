"""
Write AAS journal articles as Python programs.

This package extends `PyLaTeX <https://github.com/JelteF/PyLaTeX>`_ with the
pieces of the `AASTeX <https://journals.aas.org/aastex-package-for-manuscript-preparation/>`_
class used by the journals of the American Astronomical Society: titles,
authors and their affiliations, acronyms, sections, figures, and
bibliographies.

The article is built by assembling a :class:`Document` from these objects and
calling :meth:`Document.generate_pdf`, which writes the ``.tex`` file, saves
every figure beside it, and compiles the result.
:meth:`Document.generate_archive` gathers the same files into the flat archive
that the AAS submission system expects.

Since the article is a program, the numbers quoted in the prose can be computed
rather than typed.  :class:`Variable` defines a LaTeX macro from a Python value,
so the text cites ``\\speedOfLight`` and the value follows whatever the code
computes.

Examples
--------

Write a very short article and compile it:

.. code-block:: python

    import pathlib
    import aastex

    doc = aastex.Document()
    doc.append(aastex.Title("An Interesting Article"))
    doc += [
        aastex.Author(
            name="Jane Doe",
            affiliation=aastex.Affiliation("Fancy University"),
            email="jane.doe@fancy.edu",
        )
    ]

    section = aastex.Section("Introduction")
    section.append("Some text.")
    doc.append(section)

    doc.generate_pdf(pathlib.Path("an_interesting_article"))

See the `documentation <https://aastex.readthedocs.io/en/latest/>`_ for a
complete example which includes figures, acronyms, computed variables, and a
bibliography.
"""

import pylatex

from ._formatting import *
from ._aastex import *

text_width_inches = 513.11743 / 72
"""
The width of the full page in inches, spanning both columns of an AASTeX
article, which is the natural figure width for a :class:`FigureStar`.
"""

column_width_inches = 242.26653 / 72
"""
The width of a single column of an AASTeX article in inches, which is the
natural figure width for a :class:`Figure`.
"""

textwidth = pylatex.Command("textwidth")
"""
The LaTeX ``\\textwidth`` length, the width of the full page, for use where a
length is expected instead of a number of inches.
"""

columnwidth = pylatex.Command("columnwidth")
"""
The LaTeX ``\\columnwidth`` length, the width of a single column, for use where
a length is expected instead of a number of inches.
"""
