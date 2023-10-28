import dataclasses
import pathlib
import pylatex

__all__ = [
    "Title",
    "Affiliation",
    "Author",
    "Label",
    "Acronym",
    "Abstract",
    "Section",
    "Document",
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
    affiliation: Affiliation
    """organization affiliated with the author"""

    def dumps(self) -> str:
        return pylatex.Command("author", self.name).dumps() + self.affiliation.dumps()


@dataclasses.dataclass
class Label(pylatex.base_classes.LatexObject):
    name: str

    def dumps(self):
        return pylatex.Command("label", pylatex.NoEscape(self.name)).dumps()


@dataclasses.dataclass
class Acronym(pylatex.base_classes.LatexObject):
    acronym: str
    name_full: str
    name_short: None | str = None
    plural: bool = False
    short: bool = False

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
                pylatex.NoEscape(rf"\ac{self.acronym}"),
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
        return command


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


class Document(pylatex.Document):
    def __init__(
        self,
        default_filepath: str | pathlib.Path = "default_filepath",
        documentclass: str = "aastex631",
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
    ):
        if document_options is None:
            document_options = ["twocolumn"]
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
