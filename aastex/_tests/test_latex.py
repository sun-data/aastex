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
