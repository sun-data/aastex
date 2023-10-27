import pytest
import aastex


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Title("my fancy paper"),
    ]
)
class TestTitle:
    def test_name(self, a: aastex.Title):
        assert isinstance(a.name, str)

    def test_dumps(self, a: aastex.Title):
        assert isinstance(a.dumps(), str)
