import collections.abc
import dataclasses
import functools
import operator
import pathlib
import re
import shutil
import tarfile
import zipfile

import matplotlib.figure
import astropy.units as u
import pylatex
from pylatex import (
    Command,
    NoEscape,
    Package,
    Marker,
    Label,
    Ref,
)
from . import _formatting
from ._python_packages import PythonPackage

__all__ = [
    "Command",
    "Title",
    "ShortTitle",
    "ShortAuthors",
    "Affiliation",
    "Author",
    "UAT",
    "Keywords",
    "Software",
    "Facilities",
    "Dataset",
    "Received",
    "Revised",
    "Accepted",
    "Published",
    "SubmitJournal",
    "Acknowledgments",
    "Contribution",
    "Acronym",
    "Variable",
    "Abstract",
    "Section",
    "Subsection",
    "Subsubsection",
    "Appendix",
    "Added",
    "Explain",
    "FigureStar",
    "Fig",
    "LeftFig",
    "RightFig",
    "Gridline",
    "Document",
    "NoEscape",
    "Package",
    "Marker",
    "Label",
    "Image",
    "Animation",
    "Figure",
    "Bibliography",
]


@dataclasses.dataclass
class Title(pylatex.base_classes.LatexObject):
    name: str

    def dumps(self) -> str:
        return pylatex.Command("title", self.name).dumps()


@dataclasses.dataclass
class ShortTitle(pylatex.base_classes.LatexObject):
    """
    An abbreviated title for the running head at the top of each page.

    AASTeX falls back to the full :class:`Title` if this is not given, which
    overflows the running head for all but the shortest titles.
    """

    name: str
    """The abbreviated title."""

    def dumps(self) -> str:
        return pylatex.Command("shorttitle", self.name).dumps()


@dataclasses.dataclass
class ShortAuthors(pylatex.base_classes.LatexObject):
    """
    An abbreviated author list for the running head, such as
    ``"Doe et al."``.
    """

    name: str
    """The abbreviated author list."""

    def dumps(self) -> str:
        return pylatex.Command("shortauthors", self.name).dumps()


@dataclasses.dataclass
class Affiliation(pylatex.base_classes.LatexObject):
    """Organization that an author is associated with"""

    name: str
    """human-readable name of the organization"""

    def dumps(self) -> str:
        return pylatex.Command("affiliation", self.name).dumps()


@dataclasses.dataclass
class Author(pylatex.base_classes.LatexObject):
    """One of the authors of this article"""

    name: str
    """Name of the author"""

    affiliation: Affiliation | list[Affiliation]
    """
    The organization affiliated with the author.

    A list may be given for an author with more than one affiliation, such as
    someone who has moved since the work was done, in which case the
    organization where the work was done is usually given first.
    """

    altaffiliation: None | str = None
    """
    A note about the author which is not an organization, rendered as a
    footnote on their name.

    This is where AASTeX puts anything which needs saying about an author
    besides where they work, such as ``"Hubble Fellow"``, or ``"Deceased"``
    for an author who died before the article was published.
    """

    email: None | str = None
    """
    The email address of the author.
    """

    orcid: None | str = None
    """The optional ORCID of the author."""

    corresponding: bool = False
    """Whether this author is the corresponding author."""

    def dumps(self) -> str:

        result = ""

        show = None

        if self.corresponding:
            result += (
                pylatex.Command(
                    command="correspondingauthor",
                    arguments=self.name,
                ).dumps()
                + "\n"
            )
            show = "show"

        author = pylatex.Command(
            command="author",
            arguments=self.name,
            options=NoEscape(self.orcid) if self.orcid is not None else None,
        ).dumps()

        # The footnote symbol attaches to whatever precedes it, so this has to
        # follow `\author` immediately.
        altaffiliation = ""
        if self.altaffiliation is not None:
            altaffiliation = (
                pylatex.Command(
                    command="altaffiliation",
                    arguments=self.altaffiliation,
                ).dumps()
                + "\n"
            )

        # AASTeX v7 requires an `\email` command for every author,
        # so emit an empty one if no email address was given.
        email = pylatex.Command(
            command="email",
            arguments=self.email if self.email is not None else "",
            options=show,
        ).dumps()

        affiliation = "\n".join(a.dumps() for a in self.affiliations)

        result += f"{author}\n{altaffiliation}{email}\n{affiliation}"

        return result

    @property
    def affiliations(self) -> list[Affiliation]:
        """
        The organizations affiliated with the author, as a list, whether one
        or several were given.
        """
        if isinstance(self.affiliation, Affiliation):
            return [self.affiliation]
        return list(self.affiliation)


@dataclasses.dataclass
class UAT(pylatex.base_classes.LatexObject):
    """
    A concept from the `Unified Astronomy Thesaurus
    <https://astrothesaurus.org/>`_.

    The AAS journals ask that keywords be drawn from the thesaurus, and AASTeX
    renders one as a link to its entry, so the concept number is needed as well
    as its name.
    """

    name: str
    """The name of the concept, such as ``"Solar physics"``."""

    number: int
    """
    The number identifying the concept, which is the last part of the URL of
    its entry in the thesaurus.
    """

    def dumps(self) -> str:
        return pylatex.Command(
            command="uat",
            arguments=[self.name, str(self.number)],
        ).dumps()


@dataclasses.dataclass
class Keywords(pylatex.base_classes.LatexObject):
    """
    The keywords describing this article.

    Examples
    --------

    Describe an article using two thesaurus concepts and a free-form keyword::

        import aastex

        keywords = aastex.Keywords([
            aastex.UAT("Solar physics", 1476),
            aastex.UAT("Ultraviolet astronomy", 1736),
            "spectrographs",
        ])
    """

    keywords: "list[str | UAT]"
    """
    The keywords, given either as a :class:`UAT` concept or as free-form text.
    """

    def dumps(self) -> str:
        keywords = ", ".join(
            k.dumps() if isinstance(k, UAT) else str(k) for k in self.keywords
        )
        return pylatex.Command("keywords", NoEscape(keywords)).dumps()


@dataclasses.dataclass
class Software(pylatex.base_classes.LatexObject):
    """
    The software used to produce this article.

    The AAS journals ask that software be cited like any other work, so each
    entry is usually a name followed by a citation.
    A :class:`PythonPackage` is written that way for you, and is cited by the
    archive of the version the article was built with.
    """

    names: "list[str | PythonPackage]"
    """
    The software packages, one entry each.
    Each is either the text of the entry, such as ``r"astropy \\citep{astropy}"``,
    or a :class:`PythonPackage`.
    """

    def dumps(self) -> str:
        names = ", ".join(
            n.dumps() if isinstance(n, PythonPackage) else str(n) for n in self.names
        )
        return pylatex.Command("software", NoEscape(names)).dumps()


@dataclasses.dataclass
class Facilities(pylatex.base_classes.LatexObject):
    """
    The observing facilities which provided the data used in this article.

    The AAS journals keep a `vocabulary of facility keywords
    <https://journals.aas.org/facility-keywords/>`_, and the entries here
    should be drawn from it where one applies.
    """

    names: list[str]
    """The facilities, one entry each."""

    def dumps(self) -> str:
        return pylatex.Command("facilities", NoEscape(", ".join(self.names))).dumps()


@dataclasses.dataclass
class Dataset(pylatex.base_classes.LatexObject):
    """
    A dataset used by this article, identified by its DOI.

    AASTeX renders this as a link, so the DOI is what makes the data citable
    rather than merely mentioned.
    """

    doi: str
    """The DOI of the dataset, without the ``https://doi.org/`` prefix."""

    name: None | str = None
    """
    The text to display.  The DOI itself is displayed if this is not given.
    """

    def dumps(self) -> str:
        return pylatex.Command(
            command="dataset",
            options=NoEscape(self.doi),
            arguments=self.doi if self.name is None else self.name,
        ).dumps()


@dataclasses.dataclass
class Received(pylatex.base_classes.LatexObject):
    """The date on which the journal received this article."""

    date: str
    """The date, as it should be printed."""

    def dumps(self) -> str:
        return pylatex.Command("received", self.date).dumps()


@dataclasses.dataclass
class Revised(pylatex.base_classes.LatexObject):
    """The date on which the journal received the revision of this article."""

    date: str
    """The date, as it should be printed."""

    def dumps(self) -> str:
        return pylatex.Command("revised", self.date).dumps()


@dataclasses.dataclass
class Accepted(pylatex.base_classes.LatexObject):
    """The date on which the journal accepted this article."""

    date: str
    """The date, as it should be printed."""

    def dumps(self) -> str:
        return pylatex.Command("accepted", self.date).dumps()


@dataclasses.dataclass
class Published(pylatex.base_classes.LatexObject):
    """The date on which the journal published this article."""

    date: str
    """The date, as it should be printed."""

    def dumps(self) -> str:
        return pylatex.Command("published", self.date).dumps()


@dataclasses.dataclass
class SubmitJournal(pylatex.base_classes.LatexObject):
    """
    The AAS journal this article is being submitted to, which is printed on
    the title page of a manuscript.
    """

    name: str
    """The name of the journal, such as ``"ApJ"``."""

    def dumps(self) -> str:
        return pylatex.Command("submitjournal", self.name).dumps()


class Acknowledgments(pylatex.base_classes.Environment):
    """
    The acknowledgments of this article.

    AASTeX hides this section when the ``anonymous`` class option is set for
    dual-anonymous review, so it is the right place for anything which would
    identify the authors.
    """

    def __init__(
        self,
        *,
        options: None | str | list[str] = None,
        arguments: None | str | list[str] = None,
        start_arguments: None | str | list[str] = None,
        **kwargs,
    ):
        super().__init__(
            options=options,
            arguments=arguments,
            start_arguments=start_arguments,
            **kwargs,
        )
        self.escape = False


class Contribution(pylatex.base_classes.Environment):
    """
    A statement of what each author contributed to this article.

    Added in AASTeX v7, and free-form text rather than a fixed taxonomy.
    Like :class:`Acknowledgments`, AASTeX hides it under the ``anonymous``
    class option.
    """

    def __init__(
        self,
        *,
        options: None | str | list[str] = None,
        arguments: None | str | list[str] = None,
        start_arguments: None | str | list[str] = None,
        **kwargs,
    ):
        super().__init__(
            options=options,
            arguments=arguments,
            start_arguments=start_arguments,
            **kwargs,
        )
        self.escape = False


@dataclasses.dataclass
class Acronym(pylatex.base_classes.LatexObject):
    r"""
    An acronym which is expanded on first use and abbreviated thereafter.

    Defining an acronym also defines LaTeX commands for using it:
    ``\NASA`` expands it on first use and abbreviates it afterwards, and
    ``\NASACapital`` does the same with the first letter capitalized, for a
    sentence which begins with the acronym.
    The capitalized form matters for an instrument whose name reads as
    ``"the Multi-slit Solar Explorer"``, since a sentence should open with
    "The" rather than "the".
    ``\NASAs`` and ``\NASACapitals`` are the plural forms, and ``\NASAShort``
    is the abbreviation whether or not it has been used before.
    """

    acronym: str
    """The abbreviated form of this acronym."""

    name_full: str
    """
    The expanded form of this acronym.

    Include a leading article, as in ``"the Multi-slit Solar Explorer"``,
    for a name which needs one.
    """

    name_short: None | str = None
    """The abbreviation to display, if it differs from :attr:`acronym`."""

    plural: bool = False
    """Whether to define the plural forms of this acronym."""

    short: bool = False
    """Whether to define a command which always gives the abbreviation."""

    def __post_init__(self):
        self.packages.append(pylatex.Package("acronym"))

    def dumps(self):
        name_short = self.name_short
        if name_short is None:
            name_short = self.acronym

        command = pylatex.Command(
            command="newacro",
            arguments=[
                self.acronym,
            ],
            options=[name_short],
            extra_arguments=[
                pylatex.NoEscape(self.name_full),
            ],
        ).dumps()
        command += pylatex.Command(
            command="newcommand",
            arguments=[
                pylatex.NoEscape(rf"\{self.acronym}"),
                pylatex.NoEscape(rf"\ac{{{self.acronym}}}"),
            ],
        ).dumps()
        if self.plural:
            command += pylatex.Command(
                command="newcommand",
                arguments=[
                    pylatex.NoEscape(rf"\{self.acronym}s"),
                    pylatex.NoEscape(rf"\acp{{{self.acronym}}}"),
                ],
            ).dumps()
        if self.short:
            command += pylatex.Command(
                command="newcommand",
                arguments=[
                    pylatex.NoEscape(rf"\{self.acronym}Short"),
                    pylatex.NoEscape(rf"\acs{{{self.acronym}}}"),
                ],
            ).dumps()
        command += pylatex.Command(
            command="newcommand",
            arguments=[
                pylatex.NoEscape(rf"\{self.acronym}Capital"),
                pylatex.NoEscape(rf"\Ac{{{self.acronym}}}"),
            ],
        ).dumps()
        if self.plural:
            command += pylatex.Command(
                command="newcommand",
                arguments=[
                    pylatex.NoEscape(rf"\{self.acronym}Capitals"),
                    pylatex.NoEscape(rf"\Acp{{{self.acronym}}}"),
                ],
            ).dumps()
        return command


@dataclasses.dataclass
class Variable(pylatex.base_classes.LatexObject):
    """
    A wrapper around the ``\\newcommand`` LaTeX command.
    """

    name: str
    """The name of the variable."""

    value: float | u.Quantity
    """The value of the variable."""

    unit: "None | collections.abc.Sequence[u.UnitBase]" = None
    """
    The unit to express :attr:`value` in, written as its factors in the
    order they should be read.

    ``astropy`` prints the bases of a composite unit in an order of its own,
    so a Doppler dispersion comes out as :math:`\\mathrm{km\\,pix^{-1}\\,s^{-1}}`
    however it was written. Giving the factors, ``(u.km, u.s**-1, u.pix**-1)``,
    prints them in that order instead.

    The value is converted to the product of the factors, so a unit it cannot
    be expressed in raises rather than mislabelling it.
    """

    @property
    def _name(self) -> str:
        return NoEscape(f"\\{self.name}")

    @property
    def _unit(self) -> str:
        """The factors of :attr:`unit`, set as one unit in the given order."""
        return r"\,".join(
            # each factor is set on its own, and the wrapper each comes in is
            # removed so that the whole product can share one
            f"{factor:latex_inline}"[1:~0].removeprefix(r"\mathrm{").removesuffix("}")
            for factor in self.unit
        )

    @property
    def _value(self) -> str:
        v = self.value
        if isinstance(v, u.Quantity):
            if self.unit is not None:
                v = v.to(functools.reduce(operator.mul, self.unit))
            v = f"{v:latex_inline}"[1:~0]
            if self.unit is not None:
                # the unit is the last thing set, so replacing it leaves the
                # number as astropy wrote it, scientific notation and all
                v = v[: v.rindex(r"\mathrm{")] + rf"\mathrm{{{self._unit}}}"
            v = rf"\ensuremath{{{v}}}"
        else:
            v = str(v)
        return NoEscape(v)

    def dumps(self) -> str:
        return Command(
            command="newcommand",
            arguments=[self._name, self._value],
        ).dumps()


class Abstract(pylatex.base_classes.Environment):
    def __init__(
        self,
        *,
        options: None | str | list[str] = None,
        arguments: None | str | list[str] = None,
        start_arguments: None | str | list[str] = None,
        **kwargs,
    ):
        super().__init__(
            options=options,
            arguments=arguments,
            start_arguments=start_arguments,
            **kwargs,
        )
        self.escape = False


class Section(pylatex.Section):
    def __init__(
        self,
        title: None | str = None,
        numbering: None | bool = None,
        *,
        label: pylatex.Label | bool | str = True,
        **kwargs,
    ):
        super().__init__(
            title=title,
            numbering=numbering,
            label=label,
            **kwargs,
        )
        self.escape = False

    def __format__(self, format_spec):
        return pylatex.Ref(self.label.marker).dumps()


class Subsection(
    Section,
    pylatex.Subsection,
):
    pass


class Subsubsection(
    Subsection,
    pylatex.Subsubsection,
):
    pass


@dataclasses.dataclass
class Appendix(pylatex.base_classes.LatexObject):
    """
    The start of the appendices.

    This is a switch rather than a container: append it to the document once,
    and every :class:`Section` after it is an appendix.
    """

    def dumps(self) -> str:
        return pylatex.Command("appendix").dumps()


@dataclasses.dataclass
class Added(pylatex.base_classes.LatexObject):
    """
    Text added since the previous version of the article.

    This renders only if the document was built with ``trackchanges=True``,
    so a revision can be marked up once and compiled either for the referee or
    for the reader.

    Notes
    -----
    AASTeX v7 removed the companion ``\\replaced`` and ``\\deleted`` commands,
    which now raise a LaTeX error telling the author to use this one instead.
    Describe what was removed or replaced in :class:`Explain`, or in the
    ``why`` of the text which replaced it.
    """

    text: str
    """The text which was added."""

    why: None | str = None
    """An optional note about the change, printed before the text."""

    def dumps(self) -> str:
        return pylatex.Command(
            command="added",
            options=self.why,
            arguments=self.text,
        ).dumps()


@dataclasses.dataclass
class Explain(pylatex.base_classes.LatexObject):
    """
    A note to the referee explaining a change, which prints beside it.

    Like :class:`Added`, this renders only under ``trackchanges=True``.
    """

    text: str
    """The explanation."""

    label: None | str = None
    """An optional label for the change being explained."""

    def dumps(self) -> str:
        return pylatex.Command(
            command="explain",
            options=self.label,
            arguments=self.text,
        ).dumps()


@dataclasses.dataclass
class Image:
    """
    An image file which needs to live in the build directory next to the
    ``.tex`` file which references it.

    Images are written by :meth:`Document.generate_pdf` instead of when they
    are added to a :class:`Figure`, since the build directory is not known
    until the document is compiled.

    Instances are created by :meth:`Figure.add_fig` and :meth:`Figure.add_image`
    rather than directly, and the images belonging to a figure or a whole
    document can be inspected using :attr:`Figure.images` and
    :attr:`Document.images`.
    """

    name: str
    """The name of this image inside the build directory."""

    figure: None | matplotlib.figure.Figure = None
    """A :mod:`matplotlib` figure to save, if this image is generated."""

    source: None | pathlib.Path = None
    """The current location of this image, if it is an existing file."""

    args: tuple = ()
    """Extra arguments passed to :meth:`matplotlib.figure.Figure.savefig`."""

    kwargs: dict = dataclasses.field(default_factory=dict)
    """Extra keyword arguments passed to :meth:`matplotlib.figure.Figure.savefig`."""

    def write(self, directory: pathlib.Path) -> pathlib.Path:
        """
        Save or copy this image into ``directory`` and return its new location.
        """
        destination = directory / self.name
        if self.figure is not None:
            self.figure.savefig(destination, *self.args, **self.kwargs)
        elif self.source.resolve() != destination.resolve():
            shutil.copyfile(self.source, destination)
        return destination

    def is_same_file(self, other: "Image") -> bool:
        """
        Whether this image and ``other`` are the same file on disk.

        Two generated images are never the same file, since each is saved
        from its own :mod:`matplotlib` figure.
        """
        if self.figure is not None or other.figure is not None:
            return False
        return self.source == other.source


@dataclasses.dataclass
class Animation:
    """
    A movie which accompanies a :class:`Figure`.

    The AAS journals play the movie in the online version of the article, in
    place of the still frames which the figure shows in the PDF.
    The figure tags its stills with the AASTeX ``interactive`` environment,
    which names the movie but plays nothing.
    Neither the compiled PDF nor the HTML version of the article made by arXiv
    can play it, so until the article is published the movie can only be
    watched where its authors have put it.
    If :attr:`url` is given, the caption of the figure links to it there.

    The movie is copied into the build directory by
    :meth:`Document.generate_pdf`, beside the PDF, and
    :meth:`Document.generate_archive` packs it into an archive of its own, as
    the journals ask.

    Examples
    --------

    Accompany a figure with a movie, which can be watched online before the
    article is published:

    .. code-block:: python

        import aastex

        figure = aastex.Figure(
            label="evolution",
            animation=aastex.Animation(
                source="evolution.mp4",
                url="https://example.org/article/evolution.mp4",
            ),
        )
        figure.add_image("evolution.pdf", width=None)
        figure.add_caption(
            "The evolution of the event. "
            "The animation runs for 30 seconds and shows the whole event."
        )
    """

    source: str | pathlib.Path
    """
    The movie file.

    The AAS journals ask for an H.264 encoded MPEG-4 file, smaller than 15 MB.
    """

    url: None | str = None
    """
    Where the movie can be watched before the article is published.

    If given, a sentence linking to it is added to the end of the caption.
    """

    def __post_init__(self):
        self.source = pathlib.Path(self.source).resolve()

    @property
    def name(self) -> str:
        """The name of this movie inside the build directory."""
        return pathlib.Path(self.source).name

    def write(self, directory: pathlib.Path) -> pathlib.Path:
        """
        Copy this movie into ``directory`` and return its new location.
        """
        image = Image(name=self.name, source=pathlib.Path(self.source))
        return image.write(directory)


def _descendants(obj: object) -> list:
    """
    Recursively gather ``obj`` and everything it contains.

    Both the children of containers and the arguments of commands are
    searched, since figures can appear inside either.
    """
    if isinstance(obj, str):
        return []

    result = [obj]

    if isinstance(obj, (list, tuple, collections.UserList)):
        for child in obj:
            result += _descendants(child)

    arguments = getattr(obj, "arguments", None)
    if arguments is not None:
        for child in getattr(arguments, "_positional_args", []):
            result += _descendants(child)

    return result


def _images(obj: object) -> list[Image]:
    """
    Recursively gather the images referenced by ``obj`` and its children.
    """
    result = []
    for descendant in _descendants(obj):
        result += getattr(descendant, "_aastex_images", [])
    return result


def _python_packages(obj: object) -> list[PythonPackage]:
    """
    Recursively gather every :class:`PythonPackage` listed in a
    :class:`Software` command of ``obj`` and its children, once each,
    in the order they appear.
    """
    result = {}
    for descendant in _descendants(obj):
        if not isinstance(descendant, Software):
            continue
        for package in descendant.names:
            if not isinstance(package, PythonPackage):
                continue
            other = result.get(package.key_)
            if other is not None and other != package:
                raise ValueError(
                    f"two different packages are cited as {package.key_!r}"
                )
            result[package.key_] = package
    return list(result.values())


_header_software = (
    "% Written by aastex from the Python packages cited by the article.\n"
    "% It is rewritten every time the article is built, so do not edit it.\n\n"
)
"""
The first lines of the ``software.bib`` file written by
:meth:`Document.generate_pdf`, which mark it as safe to overwrite.
"""


class _Documentation(pylatex.base_classes.LatexObject):
    r"""
    The ``\docs`` macro, which expands to the URL of the documentation of each
    :class:`PythonPackage` cited by a document, given its key.

    The URLs are found when the document is written, so they follow whatever
    the document cites at that time.
    """

    def __init__(self, document: "Document") -> None:
        super().__init__()
        self.document = document
        """The document whose packages are documented."""

    def dumps(self) -> str:
        urls = {p.key_: p.url_docs for p in self.document.python_packages}
        lines = [
            rf"\expandafter\def\csname aastex@docs@{key}\endcsname{{{url}}}"
            for key, url in urls.items()
            if url is not None
        ]
        if not lines:
            return ""
        lines.insert(0, r"\newcommand{\docs}[1]{\csname aastex@docs@#1\endcsname}")
        return "\n".join(lines)


def _animated_figures(obj: object) -> "list[tuple[Figure, Animation]]":
    """
    Recursively gather the figures in ``obj`` which are accompanied by an
    :class:`Animation`, each paired with its animation.
    """
    result = []
    for descendant in _descendants(obj):
        if isinstance(descendant, Figure) and descendant.animation is not None:
            result.append((descendant, descendant.animation))
    return result


class Figure(
    pylatex.Figure,
):
    """
    A figure, holding images and a caption.

    Parameters
    ----------
    label
        The label used to reference this figure, which also names the images
        generated for it.
    position
        The placement specifier of the LaTeX float, such as ``"ht"``.
    animation
        A movie to accompany this figure.
        If given, the images of this figure are its still frames, which the
        AASTeX ``interactive`` environment tags as standing in for the movie.
    kwargs
        Additional keyword arguments passed to :class:`pylatex.Figure`.
    """

    marker_prefix = "fig"
    # separate_paragraph = False

    def __init__(
        self,
        label: str | Label,
        position: None | str = None,
        *,
        animation: None | Animation = None,
        **kwargs,
    ):
        super().__init__(
            position=position,
            **kwargs,
        )
        self.label = label
        self.animation = animation
        self._aastex_images: list[Image] = []
        self._aastex_caption_index: None | int = None

    @property
    def images(self) -> list[Image]:
        """
        The images referenced by this figure.
        """
        return self._aastex_images

    @property
    def _label(self) -> Label:
        label = self.label
        if not isinstance(label, Label):
            if ":" in label:
                label = label.split(":", 1)
                label = Label(Marker(label[1], label[0]))
            else:
                label = Label(Marker(label, self.marker_prefix))
        return label

    def __format__(self, format_spec):
        return Ref(self._label.marker).dumps()

    def _name_image(self, extension: str) -> str:
        """
        The name to give the next image added to this figure.

        The name is derived from this figure's label so that the image files
        are recognizable, and an index is appended if this figure already
        contains an image.
        """
        stem = self._label.marker.name
        index = len(self._aastex_images)
        if index:
            stem = f"{stem}-{index + 1}"
        return f"{stem}.{extension.strip('.')}"

    def add_image(
        self,
        filename: str | pathlib.Path,
        *,
        width: None | str = NoEscape(r"0.8\textwidth"),
        placement: str = NoEscape(r"\centering"),
    ):
        """
        Add an existing image file to this :class:`Figure`.

        The image is copied into the build directory by
        :meth:`Document.generate_pdf`, and is referenced by name so that the
        generated ``.tex`` file does not depend on where the image was
        originally stored.

        Parameters
        ----------
        filename
            The location of the image to add to this figure.
        width
            The width of the image in the compiled document.
        placement
            The placement of the image in the compiled document.
        """
        filename = pathlib.Path(filename)

        image = Image(name=filename.name, source=filename.resolve())
        self._aastex_images.append(image)

        super().add_image(
            filename=image.name,
            width=width,
            placement=placement,
        )

    def add_fig(
        self,
        fig: matplotlib.figure.Figure,
        *args,
        extension: str = "pdf",
        filename: None | str = None,
        **kwargs,
    ):
        """
        Add a :class:`matplotlib.figure.Figure` to this :class:`Figure`

        The figure is not saved until the document is compiled by
        :meth:`Document.generate_pdf`, which saves it into the build directory
        next to the ``.tex`` file which references it.

        Parameters
        ----------
        fig
            :mod:`matplotlib` figure to add to this document
        args
            Arguments passed to plt.savefig for displaying the plot.
        extension
            The file type extension to save the image as.
        filename
            The name to save the image as, without the extension.
            If :obj:`None`, the name is derived from this figure's label.
        kwargs
            Keyword arguments passed to plt.savefig for displaying the plot. In
            case these contain ``width`` or ``placement``, they will be used
            for the same purpose as in the add_image command. Namely, the width
            and placement of the generated plot in the LaTeX document.
        """
        add_image_kwargs = {}

        for key in ("width", "placement"):
            if key in kwargs:
                add_image_kwargs[key] = kwargs.pop(key)

        if filename is None:
            name = self._name_image(extension)
        else:
            name = f"{filename}.{extension.strip('.')}"

        image = Image(
            name=name,
            figure=fig,
            args=args,
            kwargs=kwargs,
        )
        self._aastex_images.append(image)

        super().add_image(
            filename=image.name,
            **add_image_kwargs,
        )

    def add_caption(self, caption) -> None:
        """
        Add a caption to this figure, followed by its label.

        If this figure has an :attr:`animation` with a
        :attr:`~Animation.url`, a sentence linking to the movie is added to
        the end of the caption.

        Parameters
        ----------
        caption
            The text of the caption, which is escaped unless it is a
            :class:`NoEscape` string.
        """
        animation = self.animation
        if animation is not None and animation.url is not None:
            self.packages.append(Package("url"))
            caption = NoEscape(
                pylatex.utils.dumps_list([caption])
                + rf" The animation can be watched at \url{{{animation.url}}}."
            )
        self._aastex_caption_index = len(self)
        super().add_caption(caption)
        self.append(self._label)

    def dumps_content(self, **kwargs) -> str:
        """
        Represent the contents of this figure as a string in LaTeX syntax.

        If this figure has an :attr:`animation`, everything before the caption
        is wrapped in the AASTeX ``interactive`` environment, which marks it
        as the still frames standing in for the movie.
        """
        if self.animation is None:
            return super().dumps_content(**kwargs)

        index = self._aastex_caption_index
        if index is None:
            index = len(self)

        def dumps(items: list) -> str:
            return pylatex.utils.dumps_list(
                items,
                escape=self.escape,
                token=self.content_separator,
                **kwargs,
            )

        stills = dumps(self.data[:index])
        rest = dumps(self.data[index:])

        return (
            rf"\begin{{interactive}}{{animation}}{{{self.animation.name}}}"
            f"{self.content_separator}{stills}{self.content_separator}"
            rf"\end{{interactive}}"
            f"{self.content_separator}{rest}"
        )


class FigureStar(
    Figure,
):
    def __init__(
        self,
        label: str | Label,
        position: None | str = None,
        **kwargs,
    ):
        super().__init__(
            label=label,
            position=position,
            **kwargs,
        )
        self._latex_name = "figure"
        self._star_latex_name = True


class Fig(pylatex.base_classes.CommandBase):
    r"""
    An AASTeX 6+ `\fig command <https://journals.aas.org/aastex-v6-3-author-guide/#new_figure_features>`_
    """

    def __init__(
        self,
        file: str | pathlib.Path,
        width: str,
        caption: str,
    ):
        file = pathlib.Path(file)

        image = Image(name=file.name, source=file.resolve())
        self._aastex_images = [image]

        super().__init__(
            arguments=[
                NoEscape(image.name),
                width,
                caption,
            ]
        )

    @property
    def images(self) -> list[Image]:
        """
        The images referenced by this command.
        """
        return self._aastex_images


class LeftFig(Fig):
    pass


class RightFig(Fig):
    pass


class Gridline(pylatex.base_classes.CommandBase):
    r"""
    An AASTeX 6+ `\gridline command <https://journals.aas.org/aastex-v6-3-author-guide/#new_figure_features>`_
    """

    def __init__(
        self,
        figures: list[Fig],
    ):
        super().__init__(
            arguments=figures,
        )


class Document(pylatex.Document):
    """
    An article using the AASTeX class.

    Parameters
    ----------
    documentclass
        The LaTeX class to use.
        Another journal's class can be given here, along with its
        ``class_files`` and ``bibliographystyle``, to build an article for
        that journal with the rest of this package.
    class_files
        The files which the class needs alongside the ``.tex`` file, such as
        the ``.cls`` and ``.bst`` files.
        They are copied into the build directory by :meth:`generate_pdf` and
        included in the archive made by :meth:`generate_archive`.
        A bare name refers to a file distributed with this package, and a path
        refers to a file of your own.
        If :obj:`None`, the AASTeX class, the AAS bibliography style, and the
        ORCID logo are used.
    bibliographystyle
        The BibTeX style to declare in the preamble, or :obj:`None` to declare
        none.
    linenumbers
        Whether to number the lines of the article.
        The AAS journals `require line numbers
        <https://journals.aas.org/pre-submission-checklist-for-aas-journal-authors/>`_
        for review, so they are on by default, and can be turned off for a
        version meant to be read rather than reviewed.
    anonymous
        Whether to hide everything which identifies the authors.
        The AAS journals review most initial submissions `dual-anonymously
        <https://journals.aas.org/dual-anonymous-peer-review/>`_, which AASTeX
        supports by suppressing the authors, their affiliations, the
        :class:`Acknowledgments`, and the :class:`Contribution`.
    trackchanges
        Whether to mark up the changes made since the previous version, which
        is what makes :class:`Added` and :class:`Explain` render.
        Without it they leave no trace, so a revision can be written once and
        compiled either way.
    """

    def __init__(
        self,
        default_filepath: str | pathlib.Path = "default_filepath",
        documentclass: str = "aastex701",
        class_files: "None | collections.abc.Sequence[str | pathlib.Path]" = None,
        bibliographystyle: None | str = "aasjournalv7",
        document_options: None | str | list[str] = None,
        fontenc: str = "T1",
        inputenc: str = "utf8",
        font_size: str = "normalsize",
        lmodern: bool = True,
        textcomp: bool = True,
        microtype: None = None,
        page_numbers: bool = True,
        indent: None | bool = None,
        geometry_options: None | dict = None,
        data: None | list = None,
        linenumbers: bool = True,
        anonymous: bool = False,
        trackchanges: bool = False,
    ):
        if document_options is None:
            document_options = ["twocolumn"]
        elif isinstance(document_options, str):
            document_options = [document_options]
        else:
            document_options = list(document_options)

        requested = dict(
            linenumbers=linenumbers,
            anonymous=anonymous,
            trackchanges=trackchanges,
        )
        for option, enabled in requested.items():
            if enabled and option not in document_options:
                document_options.append(option)

        super().__init__(
            default_filepath=str(default_filepath),
            documentclass=documentclass,
            document_options=document_options,
            fontenc=fontenc,
            inputenc=inputenc,
            font_size=font_size,
            lmodern=lmodern,
            textcomp=textcomp,
            microtype=microtype,
            page_numbers=page_numbers,
            indent=indent,
            geometry_options=geometry_options,
            data=data,
        )
        self.escape = False

        if class_files is None:
            class_files = ("aastex701.cls", "aasjournalv7.bst", "orcid-ID.png")
        base = pathlib.Path(__file__).parent
        self.class_files = [
            (
                base / f
                if isinstance(f, str) and pathlib.Path(f).name == f
                else pathlib.Path(f)
            )
            for f in class_files
        ]
        """The files copied alongside the ``.tex`` file when building."""

        if bibliographystyle is not None:
            self.preamble.append(
                pylatex.Command("bibliographystyle", bibliographystyle)
            )

        self.preamble.append(_Documentation(self))

    def set_variable_quantity(
        self,
        name: str,
        value: u.Quantity,
        scientific_notation: None | bool = None,
        digits_after_decimal: int = 3,
    ) -> None:
        """
        Similar to :meth:`set_variable`, but allows for ``value`` to be an
        instance of :class:`astropy.units.Quantity`.

        Parameters
        ----------
        name
            The name to set for the variable
        value
            The value to set for the variable
        scientific_notation
            Flag controlling whether to use scientific notation.
            If :obj:`None`, scientific notation is used if ``np.all(values.abs() < .1)``
        digits_after_decimal
            Number of digits to include after the decimal
        """
        self.set_variable(
            name=name,
            value=pylatex.NoEscape(
                _formatting.format_quantity(
                    a=value,
                    scientific_notation=scientific_notation,
                    digits_after_decimal=digits_after_decimal,
                )
            ),
        )

    @property
    def images(self) -> list[Image]:
        """
        Every image referenced by this document, in the order they appear.
        """
        return _images(self)

    @property
    def animations(self) -> list[Animation]:
        """
        Every movie accompanying a figure in this document, in the order they
        appear.
        """
        return [animation for _, animation in _animated_figures(self)]

    @property
    def python_packages(self) -> list[PythonPackage]:
        """
        Every :class:`PythonPackage` listed in a :class:`Software` command of
        this document, in the order they appear.
        """
        return _python_packages(self)

    def _check_docs(self) -> None:
        r"""
        Raise an error if the prose links to the documentation of a package
        through ``\docs`` which this document does not cite, or which declares
        no documentation, since LaTeX would quietly make a broken link.
        """
        known = {p.key_ for p in self.python_packages if p.url_docs is not None}
        used = set(re.findall(r"\\docs\{(.*?)\}", self.dumps()))
        unknown = sorted(used - known)
        if unknown:
            raise ValueError(
                f"the documentation of {unknown} is linked to with `\\docs`, "
                f"but no package with documentation is cited by that key in a "
                f"`Software` command of this document"
            )

    def _write_software(self, directory: pathlib.Path) -> None:
        """
        Write the BibTeX entry of every :class:`PythonPackage` this document
        cites into ``software.bib`` in ``directory``.

        Parameters
        ----------
        directory
            The directory the document is built in.
        """
        packages = self.python_packages
        if not packages:
            return

        sources = [
            source.strip()
            for bibliography in _descendants(self)
            if isinstance(bibliography, Bibliography)
            for source in bibliography.sources.split(",")
        ]
        if "software" not in sources:
            raise ValueError(
                "the Python packages in this document are cited from "
                "`software.bib`, which needs to be one of the sources of its "
                "bibliography, as in `aastex.Bibliography('sources,software')`"
            )

        path = directory / "software.bib"
        if path.exists():
            if not path.read_text(encoding="utf-8").startswith(_header_software):
                raise FileExistsError(
                    f"{path} was not written by aastex, so it is not overwritten"
                )

        entries = "\n".join(p.bibtex() for p in packages)
        path.write_text(_header_software + entries, encoding="utf-8")

    def generate_pdf(
        self,
        filepath: None | str | pathlib.Path = None,
        *,
        clean: bool = True,
        clean_tex: bool = True,
        compiler: None | str = None,
        compiler_args: None | list[str] = None,
        silent: bool = True,
    ) -> None:
        """
        Generate a pdf file from this document.

        The AASTeX class file, the bibliography style, and the ORCID logo are
        copied into the build directory before compiling, since the ``.tex``
        file expects to find them alongside itself.
        Any of these files already present in the build directory is left
        alone, and only the copies made here are removed afterwards.

        Every image in this document is also saved into the build directory,
        so that the build directory contains everything needed to compile the
        ``.tex`` file.
        Every :class:`Animation` is copied there too, so that the movies sit
        beside the PDF and can be published with it.

        The BibTeX entry of every :class:`PythonPackage` in :attr:`python_packages`
        is written into ``software.bib`` there, which looks up the archive of
        each package on Zenodo, so the article cites the versions it was built
        with.

        Parameters
        ----------
        filepath
            The name of the file (without the ``.pdf`` extension).
            If :obj:`None`, :attr:`default_filepath` is used.
        clean
            Whether the non-pdf files created during compilation should be
            removed.
        clean_tex
            Whether the generated tex file should be removed.
        compiler
            The name of the LaTeX compiler to use.
            If :obj:`None`, ``latexmk`` and then ``pdflatex`` are tried.
        compiler_args
            Extra arguments to pass to the LaTeX compiler.
        silent
            Whether to hide the output of the compiler.
        """

        if filepath is None:
            filepath = self.default_filepath

        filepath = pathlib.Path(filepath)

        directory = filepath.parent
        directory.mkdir(parents=True, exist_ok=True)

        self._check_docs()
        self._write_software(directory)

        copies = []
        for source in self.class_files:
            source = pathlib.Path(source)
            destination = directory / source.name
            if destination.exists():
                continue
            shutil.copyfile(source, destination)
            copies.append(destination)

        seen = {}
        for image in self.images:
            other = seen.get(image.name)
            if other is not None and not image.is_same_file(other):
                raise ValueError(
                    f"two different images are named {image.name!r}, which "
                    f"usually means two figures share the label "
                    f"{pathlib.Path(image.name).stem!r}"
                )
            seen[image.name] = image
            image.write(directory)

        movies = {}
        for animation in self.animations:
            other = movies.get(animation.name)
            if other is not None and other.source != animation.source:
                raise ValueError(f"two different movies are named {animation.name!r}")
            movies[animation.name] = animation
            animation.write(directory)

        try:
            super().generate_pdf(
                filepath=filepath,
                clean=clean,
                clean_tex=clean_tex,
                compiler=compiler,
                compiler_args=compiler_args,
                silent=silent,
            )
        finally:
            if clean_tex:
                for destination in copies:
                    destination.unlink(missing_ok=True)

    def generate_archive(
        self,
        filepath: None | str | pathlib.Path = None,
        *,
        format: str = "zip",
        bibliography: None | str | pathlib.Path = None,
        **kwargs,
    ) -> pathlib.Path:
        """
        Compile this document and gather everything needed to submit it into a
        single archive.

        The archive is flat, since the
        `AAS submission system <https://journals.aas.org/pre-submission-checklist-for-aas-journal-authors/>`_
        cannot parse subdirectories,
        and it contains the ``.tex`` file, the ``.bbl`` file required by the
        AAS conversion software, the AASTeX class and bibliography style
        files, the ORCID logo, and every image in this document.

        The journals ask for the movie of each animated figure to be uploaded
        separately, as a zip archive named after the number of the figure,
        such as ``fig01anim.zip``, so each :class:`Animation` is packed into an
        archive of its own beside the main one.
        The number of each figure is read from the ``.aux`` file left by the
        compiler, and the label of the figure is used instead if the ``.aux``
        file does not record it.

        Parameters
        ----------
        filepath
            The name of the archive (without the extension).
            If :obj:`None`, the name of the compiled document is used.
        format
            The type of archive to create, either ``"zip"`` or ``"gztar"``.
        bibliography
            The location of the ``.bib`` file to include in the archive.
            If :obj:`None`, no ``.bib`` file is included.
        kwargs
            Additional keyword arguments passed to :meth:`generate_pdf`.
        """

        if filepath is None:
            filepath = self.default_filepath
        filepath = pathlib.Path(filepath)

        self.generate_pdf(
            filepath=filepath,
            clean=False,
            clean_tex=False,
            **kwargs,
        )

        directory = filepath.parent

        members = [filepath.with_suffix(".tex")]
        members += [directory / pathlib.Path(f).name for f in self.class_files]

        members += [directory / image.name for image in self.images]

        # The AAS conversion software requires the .bbl file, so it is only
        # optional for a document without a bibliography.
        bbl = filepath.with_suffix(".bbl")
        cited = any(isinstance(d, Bibliography) for d in _descendants(self))
        if cited or bbl.exists():
            members.append(bbl)

        if bibliography is not None:
            members.append(pathlib.Path(bibliography))

        if self.python_packages:
            members.append(directory / "software.bib")

        missing = [m for m in members if not m.exists()]
        if missing:
            raise FileNotFoundError(
                f"the files {[str(m) for m in missing]} are needed to submit "
                f"this document but were not found"
            )

        if format == "zip":
            result = filepath.with_suffix(".zip")
            with zipfile.ZipFile(result, "w", zipfile.ZIP_DEFLATED) as archive:
                for member in members:
                    archive.write(member, arcname=member.name)
        elif format == "gztar":
            result = filepath.with_suffix(".tar.gz")
            with tarfile.open(result, "w:gz") as archive:
                for member in members:
                    archive.add(member, arcname=member.name)
        else:
            raise ValueError(f"unrecognized format {format!r}")

        numbers = _label_numbers(filepath.with_suffix(".aux"))
        for figure, animation in _animated_figures(self):
            marker = figure._label.marker
            number = numbers.get(marker.dumps(), marker.name)
            if number.isdigit():
                number = f"{int(number):02}"
            movie = directory / animation.name
            path = directory / f"fig{number}anim.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.write(movie, arcname=movie.name)

        return result


def _label_numbers(aux: pathlib.Path) -> dict[str, str]:
    """
    The number LaTeX gave each label, as recorded in the ``.aux`` file of a
    compiled document, or nothing if there is no ``.aux`` file.
    """
    if not aux.exists():
        return {}
    text = aux.read_text(encoding="utf-8", errors="replace")
    return dict(re.findall(r"\\newlabel\{(.+?)\}\{\{(.*?)\}", text))


class Bibliography(pylatex.base_classes.CommandBase):
    """
    The bibliography of an article, read from the BibTeX files beside it.

    Parameters
    ----------
    sources
        The names of the BibTeX files, without the ``.bib`` extension,
        separated by commas.
        A document which cites a :class:`PythonPackage` must include
        ``software``, the file :meth:`Document.generate_pdf` writes the
        entries of the packages into, as in ``"sources,software"``.
    """

    def __init__(
        self,
        sources: str,
    ) -> None:
        super().__init__(
            arguments=sources,
        )
        self.sources = sources
        """The names of the BibTeX files, separated by commas."""
