import dataclasses
import pylatex

__all__ = [
    "Title",
    "Affiliation",
]


@dataclasses.dataclass
class Title(pylatex.base_classes.LatexObject):
    name: str

    def dumps(self):
        return pylatex.Command("title", self.name).dumps()


@dataclasses.dataclass
class Affiliation(pylatex.base_classes.LatexObject):
    """Organization that an author is associated with"""

    name: str
    """human-readable name of the organization"""

    def dumps(self):
        return pylatex.Command('affiliation', self.name).dumps()
