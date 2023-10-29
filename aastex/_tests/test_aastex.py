import pytest
import numpy as np
import matplotlib.pyplot as plt
import aastex


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Title("my fancy paper"),
    ],
)
class TestTitle:
    def test_name(self, a: aastex.Title):
        assert isinstance(a.name, str)

    def test_dumps(self, a: aastex.Title):
        assert isinstance(a.dumps(), str)


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Affiliation("Fancy University"),
    ],
)
class TestAffiliation:
    def test_name(self, a: aastex.Affiliation):
        assert isinstance(a.name, str)

    def test_dumps(self, a: aastex.Affiliation):
        assert isinstance(a.dumps(), str)


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Author(
            name="Jane Doe",
            affiliation=aastex.Affiliation("Fancy University"),
        ),
    ],
)
class TestAuthor:
    def test_name(self, a: aastex.Author):
        assert isinstance(a.name, str)

    def test_affiliation(self, a: aastex.Author):
        assert isinstance(a.affiliation, aastex.Affiliation)

    def test_dumps(self, a: aastex.Author):
        assert isinstance(a.dumps(), str)


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Acronym(
            acronym="NASA",
            name_full="National Aeronautical and Space Administration",
            name_short=name_short,
            plural=plural,
            short=short,
        )
        for short in [False, True]
        for plural in [False, True]
        for name_short in [None, "Naysah"]
    ],
)
class TestAcronym:
    def test_acronym(self, a: aastex.Acronym):
        assert isinstance(a.acronym, str)

    def test_name_full(self, a: aastex.Acronym):
        assert isinstance(a.name_full, str)

    def test_name_short(self, a: aastex.Acronym):
        result = a.name_short
        if result is not None:
            assert isinstance(result, str)

    def test_plural(self, a: aastex.Acronym):
        result = a.plural
        assert isinstance(result, bool)

    def test_short(self, a: aastex.Acronym):
        result = a.short
        assert isinstance(result, bool)

    def test_dumps(self, a: aastex.Title):
        assert isinstance(a.dumps(), str)


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Abstract(),
    ],
)
class TestAbstract:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Section("Introduction"),
    ],
)
class TestSection:
    def test__format__(self, a: aastex.Section):
        result = f"{a}"
        assert r"\ref" in result


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Figure(),
    ],
)
class TestFigure:
    def test_add_fig(self, a: aastex.Figure):
        fig, ax = plt.subplots()
        ax.plot(np.random.normal(size=11))
        a.add_fig(fig, width=None)

        assert r"\includegraphics" in a.dumps()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Document(),
    ],
)
class TestDocument:
    pass
