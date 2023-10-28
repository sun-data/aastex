import pytest
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
        aastex.Label("momentum-equation"),
    ],
)
class TestLabel:
    def test_name(self, a: aastex.Label):
        assert isinstance(a.name, str)

    def test_dumps(self, a: aastex.Label):
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
class TestAbstract:
    pass


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Document(),
    ],
)
class TestDocument:
    pass