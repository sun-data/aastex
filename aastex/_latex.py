import dataclasses
import pylatex

__all__ = [
    "Title",
    "Affiliation",
    "Author",
    "Label",
    "Acronym",
    "Abstract",
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
    pass
