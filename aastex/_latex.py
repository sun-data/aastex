import dataclasses
import pylatex

__all__ = [
    "Title",
]


@dataclasses.dataclass
class Title(pylatex.base_classes.LatexObject):
    name: str

    def dumps(self):
        return pylatex.Command("title", self.name).dumps()
