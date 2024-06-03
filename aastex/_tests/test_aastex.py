import pathlib

import pytest
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
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
            email="jane.doe@tmp.com"
        ),
    ],
)
class TestAuthor:
    def test_name(self, a: aastex.Author):
        assert isinstance(a.name, str)

    def test_affiliation(self, a: aastex.Author):
        assert isinstance(a.affiliation, aastex.Affiliation)

    def test_email(self, a: aastex.Author):
        result = a.email
        if result is not None:
            assert isinstance(result, str)

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
        aastex.Subsection("Foo"),
    ],
)
class TestSubsection:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Subsubsection("Foo"),
    ],
)
class TestSubsubsection:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Figure(aastex.Label(aastex.Marker("fig", "data"))),
        aastex.Figure("fig:data"),
        aastex.Figure("data"),
    ],
)
class TestFigure:
    def test__format__(self, a: aastex.Section):
        result = f"{a}"
        assert r"\ref" in result

    def test_add_fig(self, a: aastex.Figure):
        fig, ax = plt.subplots()
        ax.plot(np.random.normal(size=11))
        a.add_fig(fig, width=None)

        assert r"\includegraphics" in a.dumps()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.FigureStar("fig:figurestar"),
    ],
)
class TestFigureStar:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Fig(
            file=pathlib.Path("foo.pdf"),
            width=r"\textwidth",
            caption="test caption",
        ),
    ],
)
class TestFig:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.LeftFig(
            file=pathlib.Path("foo.pdf"),
            width=r"\textwidth",
            caption="test caption",
        ),
    ],
)
class TestLeftFig:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.RightFig(
            file=pathlib.Path("foo.pdf"),
            width=r"\textwidth",
            caption="test caption",
        ),
    ],
)
class TestRightFig:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Gridline(
            figures=[
                aastex.LeftFig(
                    file=pathlib.Path("foo.pdf"),
                    width=r"0.5\textwidth",
                    caption="test caption",
                ),
                aastex.LeftFig(
                    file=pathlib.Path("bar.pdf"),
                    width=r"0.5\textwidth",
                    caption="test caption",
                ),
            ],
        ),
    ],
)
class TestGridline:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Document(),
    ],
)
class TestDocument:
    @pytest.mark.parametrize(
        argnames="value",
        argvalues=[
            0 * u.K,
            1e-5 * u.m,
            [1, 2, 3] * u.s,
        ],
    )
    @pytest.mark.parametrize(
        argnames="scientific_notation",
        argvalues=[
            None,
            False,
            True,
        ],
    )
    @pytest.mark.parametrize(
        argnames="digits_after_decimal",
        argvalues=[
            4,
        ],
    )
    def test_set_variable_quantity(
        self,
        a: aastex.Document,
        value: u.Quantity,
        scientific_notation: None | bool,
        digits_after_decimal: int,
    ):
        name = "testVariable"
        a.set_variable_quantity(
            name=name,
            value=value,
            scientific_notation=scientific_notation,
            digits_after_decimal=digits_after_decimal,
        )

        assert name in a.dumps()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Bibliography("sources"),
    ],
)
class TestBibliography:
    pass
