import collections
import dataclasses
import pathlib
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

__all__ = [
    "Command",
    "Title",
    "Affiliation",
    "Author",
    "Acronym",
    "Variable",
    "Abstract",
    "Section",
    "Subsection",
    "Subsubsection",
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
    "Figure",
    "Bibliography",
]


@dataclasses.dataclass
class Title(pylatex.base_classes.LatexObject):
    name: str

    def dumps(self) -> str:
        return pylatex.Command("title", self.name).dumps()


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

        # AASTeX v7 requires an `\email` command for every author,
        # so emit an empty one if no email address was given.
        email = pylatex.Command(
            command="email",
            arguments=self.email if self.email is not None else "",
            options=show,
        ).dumps()

        affiliation = "\n".join(a.dumps() for a in self.affiliations)

        result += f"{author}\n{email}\n{affiliation}"

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

    @property
    def _name(self) -> str:
        return NoEscape(f"\\{self.name}")

    @property
    def _value(self) -> str:
        v = self.value
        if isinstance(v, u.Quantity):
            v = f"{v:latex_inline}"
            v = rf"\ensuremath{{{v[1:~0]}}}"
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


class Figure(
    pylatex.Figure,
):
    marker_prefix = "fig"
    # separate_paragraph = False

    def __init__(
        self,
        label: str | Label,
        position: None | str = None,
        **kwargs,
    ):
        super().__init__(
            position=position,
            **kwargs,
        )
        self.label = label
        self._aastex_images: list[Image] = []

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
        super().add_caption(caption)
        self.append(self._label)


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
    linenumbers
        Whether to number the lines of the article.
        The AAS journals `require line numbers
        <https://journals.aas.org/pre-submission-checklist-for-aas-journal-authors/>`_
        for review, so they are on by default, and can be turned off for a
        version meant to be read rather than reviewed.
    """

    def __init__(
        self,
        default_filepath: str | pathlib.Path = "default_filepath",
        documentclass: str = "aastex701",
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
    ):
        if document_options is None:
            document_options = ["twocolumn"]
        elif isinstance(document_options, str):
            document_options = [document_options]
        else:
            document_options = list(document_options)

        if linenumbers and "linenumbers" not in document_options:
            document_options.append("linenumbers")

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
        self.preamble.append(pylatex.Command("bibliographystyle", "aasjournalv7"))

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

        base = pathlib.Path(__file__).parent

        copies = []
        for name in ("aastex701.cls", "aasjournalv7.bst", "orcid-ID.png"):
            destination = directory / name
            if destination.exists():
                continue
            shutil.copyfile(base / name, destination)
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

        members = [
            filepath.with_suffix(".tex"),
            directory / "aastex701.cls",
            directory / "aasjournalv7.bst",
            directory / "orcid-ID.png",
        ]

        members += [directory / image.name for image in self.images]

        # The AAS conversion software requires the .bbl file, so it is only
        # optional for a document without a bibliography.
        bbl = filepath.with_suffix(".bbl")
        cited = any(isinstance(d, Bibliography) for d in _descendants(self))
        if cited or bbl.exists():
            members.append(bbl)

        if bibliography is not None:
            members.append(pathlib.Path(bibliography))

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

        return result


class Bibliography(pylatex.base_classes.CommandBase):
    def __init__(
        self,
        sources: str,
    ):
        super().__init__(
            arguments=sources,
        )
