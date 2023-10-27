import dataclasses
import pylatex

__all__ = [
    "Title",
    "Affiliation",
    "Author",
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

    def dumps(self)-> str:
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
