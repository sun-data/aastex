import pathlib
import shutil
import subprocess
import tarfile
import zipfile

import pytest
import pylatex
import numpy as np
import matplotlib

matplotlib.use("agg")

import matplotlib.pyplot as plt  # noqa: E402
import astropy.units as u  # noqa: E402
import aastex  # noqa: E402


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
            orcid="0000-0000-0000-0000",
            email="jane.doe@tmp.com",
            corresponding=True,
        ),
        aastex.Author(
            name="John Doe",
            affiliation=aastex.Affiliation("Fancy University"),
        ),
        aastex.Author(
            name="Jane Roe",
            affiliation=[
                aastex.Affiliation("Fancy University"),
                aastex.Affiliation("Another Fancy University"),
            ],
        ),
        aastex.Author(
            name="John Roe",
            affiliation=aastex.Affiliation("Fancy University"),
            altaffiliation="Deceased",
        ),
    ],
)
class TestAuthor:
    def test_name(self, a: aastex.Author):
        assert isinstance(a.name, str)

    def test_affiliation(self, a: aastex.Author):
        result = a.affiliation
        if not isinstance(result, aastex.Affiliation):
            assert all(isinstance(r, aastex.Affiliation) for r in result)

    def test_affiliations(self, a: aastex.Author):
        result = a.affiliations
        assert isinstance(result, list)
        assert result
        assert all(isinstance(r, aastex.Affiliation) for r in result)

        # every affiliation given is rendered
        dumps = a.dumps()
        assert dumps.count(r"\affiliation") == len(result)
        for affiliation in result:
            assert affiliation.name in dumps

    def test_altaffiliation(self, a: aastex.Author):
        result = a.altaffiliation
        dumps = a.dumps()
        if result is not None:
            assert isinstance(result, str)

            # the footnote symbol attaches to the preceding text, so this has
            # to follow `\author` and nothing else
            author = dumps.index(r"\author")
            assert dumps.index(r"\altaffiliation") > author
            assert dumps.index(result, author) < dumps.index(r"\email")
        else:
            assert r"\altaffiliation" not in dumps

    def test_orcid(self, a: aastex.Author):
        result = a.orcid
        if result is not None:
            assert isinstance(result, str)
            assert result in a.dumps()

    def test_email(self, a: aastex.Author):
        result = a.email
        if result is not None:
            assert isinstance(result, str)
            assert result in a.dumps()
        else:
            assert r"\email{}" in a.dumps()

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

    def test_capital(self, a: aastex.Acronym):
        """A capitalized command is defined for a sentence starting with the acronym."""
        dumps = a.dumps()
        assert rf"\{a.acronym}Capital" in dumps
        assert rf"\Ac{{{a.acronym}}}" in dumps
        if a.plural:
            assert rf"\{a.acronym}Capitals" in dumps
            assert rf"\Acp{{{a.acronym}}}" in dumps


@pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="requires a LaTeX installation",
)
def test_acronym_capital_compiles(tmp_path: pathlib.Path):
    """
    The capitalized command raises the article of a name which carries one.

    An instrument named "the Multi-slit Solar Explorer" should open a sentence
    with "The", which is what the underlying `acronym` package provides.
    """
    doc = aastex.Document(document_options="twocolumn", linenumbers=False)
    doc.preamble.append(aastex.Acronym("MUSE", "the Multi-slit Solar Explorer"))
    doc.append(aastex.Title("Acronyms"))
    doc += [
        aastex.Author(
            name="Jane Doe",
            affiliation=aastex.Affiliation("Fancy University"),
        )
    ]
    section = aastex.Section("Introduction")
    section.append(pylatex.NoEscape(r"\MUSECapital\ observes the Sun. \MUSE\ again."))
    doc.append(section)

    path = tmp_path / "acronyms"
    doc.generate_pdf(path, clean_tex=False)

    text = subprocess.run(
        args=["pdftotext", str(path.with_suffix(".pdf")), "-"],
        capture_output=True,
        text=True,
    ).stdout

    assert "The Multi-slit Solar Explorer (MUSE)" in text
    assert "MUSE again" in text


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Variable("foo", 2),
        aastex.Variable("bar", 3 * u.AA),
        aastex.Variable(
            name="baz",
            value=17.5 * u.km / u.s / u.pix,
            unit=(u.km, u.s**-1, u.pix**-1),
        ),
    ],
)
class TestVariable:

    def test_name(self, a: aastex.Variable):
        assert isinstance(a.name, str)

    def test_value(self, a: aastex.Variable):
        assert isinstance(a.value, (int, float, u.Quantity))

    def test_dumps(self, a: aastex.Variable):
        assert isinstance(a.dumps(), str)


def test_variable_unit():
    """The factors of a unit are set in the order they were given."""
    value = 17.5 * u.km / u.s / u.pix

    # the order astropy chooses, which is not the one this is read in
    assert r"\mathrm{km\,pix^{-1}\,s^{-1}}" in aastex.Variable("a", value).dumps()

    result = aastex.Variable("a", value, unit=(u.km, u.s**-1, u.pix**-1)).dumps()
    assert r"\mathrm{km\,s^{-1}\,pix^{-1}}" in result

    # the number is left as astropy wrote it
    assert "17.5" in result


def test_variable_unit_converts():
    """A value is converted to the unit it is to be set in."""
    result = aastex.Variable("a", 1500 * u.m, unit=(u.km,)).dumps()
    assert r"\mathrm{km}" in result
    assert "1.5" in result


def test_variable_unit_scientific_notation():
    """Replacing the unit leaves an exponent alone."""
    result = aastex.Variable("a", 1.2e-5 * u.cm**2, unit=(u.cm**2,)).dumps()
    assert r"\times 10^{-5}" in result
    assert r"\mathrm{cm^{2}}" in result


def test_variable_unit_mismatch():
    """A unit the value cannot be expressed in raises."""
    with pytest.raises(u.UnitConversionError):
        aastex.Variable("a", 3 * u.m, unit=(u.s,)).dumps()


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
        aastex.ShortTitle("A short title"),
        aastex.ShortAuthors("Doe et al."),
        aastex.SubmitJournal("ApJ"),
    ],
)
class TestRunningHead:
    def test_name(self, a: aastex.ShortTitle | aastex.ShortAuthors):
        assert isinstance(a.name, str)

    def test_dumps(self, a: aastex.ShortTitle | aastex.ShortAuthors):
        assert isinstance(a.dumps(), str)


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Received("2026 January 1"),
        aastex.Revised("2026 February 1"),
        aastex.Accepted("2026 March 1"),
        aastex.Published("2026 April 1"),
    ],
)
class TestDate:
    def test_date(self, a: aastex.Received):
        assert isinstance(a.date, str)

    def test_dumps(self, a: aastex.Received):
        assert isinstance(a.dumps(), str)


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.UAT("Solar physics", 1476),
    ],
)
class TestUAT:
    def test_number(self, a: aastex.UAT):
        assert isinstance(a.number, int)

    def test_dumps(self, a: aastex.UAT):
        result = a.dumps()
        assert a.name in result
        assert str(a.number) in result


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Keywords(["spectrographs"]),
        aastex.Keywords([aastex.UAT("Solar physics", 1476), "spectrographs"]),
    ],
)
class TestKeywords:
    def test_dumps(self, a: aastex.Keywords):
        result = a.dumps()
        assert r"\keywords" in result
        assert "spectrographs" in result

    def test_dumps_uat(self, a: aastex.Keywords):
        """A thesaurus concept is expanded rather than printed as a repr."""
        if any(isinstance(k, aastex.UAT) for k in a.keywords):
            assert r"\uat" in a.dumps()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Software(["numpy", "astropy"]),
        aastex.Facilities(["IRIS", "SDO(AIA)"]),
    ],
)
class TestNameList:
    def test_dumps(self, a: aastex.Software | aastex.Facilities):
        result = a.dumps()
        for name in a.names:
            assert name in result


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Dataset("10.5281/zenodo.1234"),
        aastex.Dataset("10.5281/zenodo.1234", name="ESIS Level 1"),
    ],
)
class TestDataset:
    def test_dumps(self, a: aastex.Dataset):
        result = a.dumps()
        assert r"\dataset" in result
        assert a.doi in result

    def test_dumps_name(self, a: aastex.Dataset):
        """The DOI stands in for the text when no text is given."""
        if a.name is not None:
            assert a.name in a.dumps()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Acknowledgments(),
        aastex.Contribution(),
    ],
)
class TestFrontMatterEnvironment:
    def test_dumps(self, a: aastex.Acknowledgments | aastex.Contribution):
        a.append("Some text.")
        result = a.dumps()
        assert "Some text." in result


def test_metadata_in_document():
    """Every metadata object reaches the document it is appended to."""
    doc = aastex.Document()
    doc.append(aastex.Title("An interesting article"))
    doc += [
        aastex.ShortTitle("Interesting"),
        aastex.ShortAuthors("Doe et al."),
        aastex.Keywords([aastex.UAT("Solar physics", 1476)]),
        aastex.Software(["astropy"]),
        aastex.Facilities(["IRIS"]),
        aastex.Dataset("10.5281/zenodo.1234"),
        aastex.SubmitJournal("ApJ"),
    ]

    result = doc.dumps()

    for command in (
        r"\shorttitle",
        r"\shortauthors",
        r"\keywords",
        r"\uat",
        r"\software",
        r"\facilities",
        r"\dataset",
        r"\submitjournal",
    ):
        assert command in result


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Appendix(),
    ],
)
class TestAppendix:
    def test_dumps(self, a: aastex.Appendix):
        assert a.dumps() == r"\appendix"


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Added("some new text"),
        aastex.Added("some new text", why="referee 1"),
    ],
)
class TestAdded:
    def test_dumps(self, a: aastex.Added):
        result = a.dumps()
        assert r"\added" in result
        assert a.text in result

    def test_dumps_why(self, a: aastex.Added):
        """The note about the change is optional."""
        if a.why is not None:
            assert f"[{a.why}]" in a.dumps()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Explain("rewrote the introduction"),
        aastex.Explain("rewrote the introduction", label="sec:intro"),
    ],
)
class TestExplain:
    def test_dumps(self, a: aastex.Explain):
        result = a.dumps()
        assert r"\explain" in result
        assert a.text in result

    def test_dumps_label(self, a: aastex.Explain):
        """The label is optional."""
        if a.label is not None:
            assert f"[{a.label}]" in a.dumps()


@pytest.mark.parametrize(
    argnames="kwargs,expected,unexpected",
    argvalues=[
        (dict(), ["linenumbers"], ["anonymous", "trackchanges"]),
        (dict(linenumbers=False), [], ["linenumbers"]),
        (dict(anonymous=True), ["anonymous"], ["trackchanges"]),
        (dict(trackchanges=True), ["trackchanges"], ["anonymous"]),
        (dict(anonymous=True, trackchanges=True), ["anonymous", "trackchanges"], []),
    ],
)
def test_document_options(
    kwargs: dict,
    expected: list[str],
    unexpected: list[str],
):
    """Each option reaches `\\documentclass`, and none appears uninvited."""
    doc = aastex.Document(**kwargs)

    (documentclass,) = [
        line for line in doc.dumps().splitlines() if "documentclass" in line
    ]

    for option in expected:
        assert option in documentclass
    for option in unexpected:
        assert option not in documentclass


def test_document_options_not_duplicated():
    """Naming an option twice does not repeat it."""
    doc = aastex.Document(document_options=["twocolumn", "anonymous"], anonymous=True)

    (documentclass,) = [
        line for line in doc.dumps().splitlines() if "documentclass" in line
    ]

    assert documentclass.count("anonymous") == 1


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

    def test_add_caption(self, a: aastex.Figure):
        a.add_caption("foo")
        assert r"\caption" in a.dumps()


def _figure_with_plot(label: str = "myFigure", **kwargs) -> aastex.Figure:
    """
    A figure containing a single matplotlib plot, for the tests below.

    The plot is closed after it is added, as in the example in the
    documentation, since images are not saved until the document is compiled.
    """
    result = aastex.Figure(label)
    fig, ax = plt.subplots()
    ax.plot(np.random.normal(size=11))
    result.add_fig(fig, width=None, **kwargs)
    plt.close(fig)
    return result


def test_image_is_public():
    """The images of a figure are instances of a documented, public class."""
    a = _figure_with_plot()
    (image,) = a.images

    assert isinstance(image, aastex.Image)
    assert aastex.Image.__name__ == "Image"


def test_image_write_directly(tmp_path: pathlib.Path):
    """An image can be constructed and written on its own."""
    source = tmp_path / "diagram.pdf"
    plt.figure().savefig(source)

    image = aastex.Image(name="renamed.pdf", source=source)

    destination = tmp_path / "build"
    destination.mkdir()

    assert image.write(destination) == destination / "renamed.pdf"
    assert (destination / "renamed.pdf").exists()


def test_figure_image_name():
    a = _figure_with_plot()
    (image,) = a.images

    assert image.name == "myFigure.pdf"
    assert "myFigure.pdf" in a.dumps()


def test_figure_image_filename():
    a = _figure_with_plot(filename="f1", extension="png")
    (image,) = a.images

    assert image.name == "f1.png"
    assert "f1.png" in a.dumps()


def test_figure_image_multiple():
    a = _figure_with_plot()
    fig, ax = plt.subplots()
    ax.plot(np.random.normal(size=11))
    a.add_fig(fig, width=None)

    first, second = a.images

    assert first.name == "myFigure.pdf"
    assert second.name == "myFigure-2.pdf"


def test_figure_image_write(tmp_path: pathlib.Path):
    a = _figure_with_plot()
    (image,) = a.images

    assert image.write(tmp_path) == tmp_path / "myFigure.pdf"
    assert (tmp_path / "myFigure.pdf").exists()


@pytest.mark.parametrize("as_string", [False, True])
def test_figure_add_image(tmp_path: pathlib.Path, as_string: bool):
    source = tmp_path / "source" / "diagram.png"
    source.parent.mkdir()
    plt.figure().savefig(source)

    a = aastex.Figure("myFigure")
    a.add_image(str(source) if as_string else source, width=None)

    (image,) = a.images

    assert image.name == "diagram.png"
    assert "diagram.png" in a.dumps()
    assert str(source.parent) not in a.dumps()

    destination = tmp_path / "build"
    destination.mkdir()

    assert image.write(destination) == destination / "diagram.png"
    assert (destination / "diagram.png").exists()


def test_figure_add_image_same_directory(tmp_path: pathlib.Path):
    """Writing an image that already lives in the build directory is a no-op."""
    source = tmp_path / "diagram.png"
    plt.figure().savefig(source)

    a = aastex.Figure("myFigure")
    a.add_image(source, width=None)

    (image,) = a.images

    assert image.write(tmp_path) == source
    assert source.exists()


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
    def test_images(self, a: aastex.Fig):
        (image,) = a.images
        assert image.name == "foo.pdf"
        assert image.name in a.dumps()


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


def test_document_linenumbers_default():
    """The AAS journals require line numbers for review."""
    assert "linenumbers" in aastex.Document().dumps()


def test_document_linenumbers_disabled():
    assert "linenumbers" not in aastex.Document(linenumbers=False).dumps()


@pytest.mark.parametrize(
    argnames="document_options",
    argvalues=[
        "twocolumn",
        ["twocolumn"],
        ["twocolumn", "linenumbers"],
    ],
)
def test_document_linenumbers_options(document_options: str | list[str]):
    """Line numbers are added to the given options without disturbing them."""
    dumps = aastex.Document(document_options=document_options).dumps()
    options = dumps.split("{aastex701}")[0]

    assert options.count("linenumbers") == 1
    assert "twocolumn" in options


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

    def test_generate_pdf(
        self,
        a: aastex.Document,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ):
        assets = ["aastex701.cls", "aasjournalv7.bst", "orcid-ID.png"]
        during = []

        def compile(self, filepath, **kwargs):
            during.extend(n for n in assets if (tmp_path / n).exists())

        monkeypatch.setattr(pylatex.Document, "generate_pdf", compile)

        a.generate_pdf(tmp_path / "article")

        assert during == assets
        assert not any((tmp_path / n).exists() for n in assets)

    def test_generate_pdf_clean_tex(
        self,
        a: aastex.Document,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ):
        assets = ["aastex701.cls", "aasjournalv7.bst", "orcid-ID.png"]

        monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

        a.generate_pdf(tmp_path / "article", clean_tex=False)

        assert all((tmp_path / n).exists() for n in assets)

    def test_generate_pdf_default_filepath(
        self,
        a: aastex.Document,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ):
        observed = []

        def compile(self, filepath, **kwargs):
            observed.append(filepath)

        monkeypatch.setattr(pylatex.Document, "generate_pdf", compile)
        monkeypatch.setattr(a, "default_filepath", str(tmp_path / "article"))

        a.generate_pdf()

        assert observed == [tmp_path / "article"]

    def test_generate_pdf_existing_asset(
        self,
        a: aastex.Document,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ):
        existing = tmp_path / "aastex701.cls"
        existing.write_text("a locally modified class file")

        monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

        a.generate_pdf(tmp_path / "article")

        assert existing.read_text() == "a locally modified class file"

    def test_generate_pdf_images(
        self,
        a: aastex.Document,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
    ):
        a.append(_figure_with_plot())

        monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

        a.generate_pdf(tmp_path / "article")

        assert (tmp_path / "myFigure.pdf").exists()


def test_generate_pdf_duplicate_label(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
):
    """Two figures sharing a label would otherwise silently overwrite each other."""
    doc = aastex.Document()
    doc.append(_figure_with_plot())
    doc.append(_figure_with_plot())

    monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

    with pytest.raises(ValueError, match="myFigure"):
        doc.generate_pdf(tmp_path / "article")


def test_generate_pdf_repeated_image(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
):
    """The same image file may be used by more than one figure."""
    source = tmp_path / "logo.png"
    plt.figure().savefig(source)

    doc = aastex.Document()
    for label in ("first", "second"):
        figure = aastex.Figure(label)
        figure.add_image(source, width=None)
        doc.append(figure)

    monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

    build = tmp_path / "build"
    doc.generate_pdf(build / "article")

    assert (build / "logo.png").exists()


def test_document_images():
    figure = _figure_with_plot()

    section = aastex.Section("A section")
    section.append(figure)

    doc = aastex.Document()
    doc.append(section)

    assert [i.name for i in doc.images] == ["myFigure.pdf"]


def _submittable_document() -> aastex.Document:
    """A small but complete document, for the archive tests below."""
    doc = aastex.Document()
    doc.append(aastex.Title("An interesting article"))
    doc += [
        aastex.Author(
            name="Jane Doe",
            affiliation=aastex.Affiliation("Fancy University"),
        ),
        aastex.Author(
            name="John Roe",
            affiliation=aastex.Affiliation("Fancy University"),
            altaffiliation="Deceased",
        ),
    ]
    section = aastex.Section("A section")
    section.append("Some text.")
    section.append(_figure_with_plot())
    doc.append(section)
    return doc


def _fake_compiler(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Stand in for the LaTeX compiler, which is not installed everywhere,
    by writing the files that a real compilation would leave behind.
    """

    def compile(self, filepath, **kwargs):
        filepath = pathlib.Path(filepath)
        filepath.with_suffix(".tex").write_text("a compiled document")
        filepath.with_suffix(".bbl").write_text("a formatted bibliography")

    monkeypatch.setattr(pylatex.Document, "generate_pdf", compile)


@pytest.mark.parametrize(
    argnames="format,suffix",
    argvalues=[
        ("zip", ".zip"),
        ("gztar", ".tar.gz"),
    ],
)
def test_generate_archive(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    format: str,
    suffix: str,
):
    doc = _submittable_document()
    _fake_compiler(monkeypatch)

    archive = doc.generate_archive(tmp_path / "article", format=format)

    assert archive == (tmp_path / "article").with_suffix(suffix)
    assert archive.exists()

    if format == "zip":
        with zipfile.ZipFile(archive) as f:
            names = f.namelist()
    else:
        with tarfile.open(archive) as f:
            names = f.getnames()

    # the AAS submission system cannot parse subdirectories
    assert not any("/" in name for name in names)

    assert set(names) == {
        "article.tex",
        "article.bbl",
        "aastex701.cls",
        "aasjournalv7.bst",
        "orcid-ID.png",
        "myFigure.pdf",
    }


def test_generate_archive_bibliography(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """A document with a bibliography ships the .bib alongside the .bbl."""
    sources = tmp_path / "sources.bib"
    sources.write_text("@ARTICLE{Doe2020}")

    doc = _submittable_document()
    doc.append(aastex.Bibliography("sources"))
    _fake_compiler(monkeypatch)

    archive = doc.generate_archive(
        tmp_path / "article",
        bibliography=sources,
    )

    with zipfile.ZipFile(archive) as f:
        names = set(f.namelist())

    assert "article.bbl" in names
    assert "sources.bib" in names


def test_generate_archive_missing_bbl(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    """The .bbl is required for a document which cites anything."""
    doc = _submittable_document()
    doc.append(aastex.Bibliography("sources"))

    def compile(self, filepath, **kwargs):
        pathlib.Path(filepath).with_suffix(".tex").write_text("a compiled document")

    monkeypatch.setattr(pylatex.Document, "generate_pdf", compile)

    with pytest.raises(FileNotFoundError, match=".bbl"):
        doc.generate_archive(tmp_path / "article")


def test_generate_archive_missing_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    doc = _submittable_document()
    _fake_compiler(monkeypatch)

    with pytest.raises(FileNotFoundError):
        doc.generate_archive(
            tmp_path / "article",
            bibliography=tmp_path / "nonexistent.bib",
        )


def test_generate_archive_unknown_format(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    doc = _submittable_document()
    _fake_compiler(monkeypatch)

    with pytest.raises(ValueError, match="unrecognized format"):
        doc.generate_archive(tmp_path / "article", format="rar")


def test_generate_archive_default_filepath(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    doc = _submittable_document()
    _fake_compiler(monkeypatch)
    monkeypatch.setattr(doc, "default_filepath", str(tmp_path / "article"))

    assert doc.generate_archive() == tmp_path / "article.zip"


@pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="requires a LaTeX installation",
)
def test_generate_archive_compiles(tmp_path: pathlib.Path):
    """The unpacked archive must compile on its own, with nothing else around it."""
    doc = _submittable_document()

    archive = doc.generate_archive(tmp_path / "build" / "article")

    clean = tmp_path / "clean"
    clean.mkdir()
    with zipfile.ZipFile(archive) as f:
        f.extractall(clean)

    subprocess.run(
        args=["latexmk", "-pdf", "-interaction=nonstopmode", "article.tex"],
        cwd=clean,
        check=True,
        capture_output=True,
    )

    assert (clean / "article.pdf").exists()


def test_document_images_gridline(tmp_path: pathlib.Path):
    """Images inside a `\\gridline` command are found too."""
    source = tmp_path / "diagram.pdf"
    plt.figure().savefig(source)

    doc = aastex.Document()
    doc.append(
        aastex.Gridline(
            [
                aastex.LeftFig(source, width=r"\textwidth", caption="a caption"),
            ]
        )
    )

    assert [i.name for i in doc.images] == ["diagram.pdf"]


def _movie(directory: pathlib.Path, name: str = "movie.mp4") -> pathlib.Path:
    """A stand-in for a movie file, since nothing here plays it."""
    result = directory / name
    result.write_bytes(b"not really a movie")
    return result


def _animated_figure(
    movie: pathlib.Path,
    url: None | str = "https://example.org/movie.mp4",
    label: str = "myFigure",
    caption: None | str = "The evolution of the event.",
) -> aastex.Figure:
    """A figure with a single still and a movie, for the tests below."""
    result = aastex.Figure(
        label,
        animation=aastex.Animation(source=movie, url=url),
    )
    fig, ax = plt.subplots()
    ax.plot(np.random.normal(size=11))
    result.add_fig(fig, width=None)
    plt.close(fig)
    if caption is not None:
        result.add_caption(caption)
    return result


def test_animation(tmp_path: pathlib.Path):
    movie = _movie(tmp_path)
    a = aastex.Animation(source=str(movie), url="https://example.org/movie.mp4")

    assert a.source == movie.resolve()
    assert a.name == "movie.mp4"

    destination = tmp_path / "build"
    destination.mkdir()

    assert a.write(destination) == destination / "movie.mp4"
    assert (destination / "movie.mp4").read_bytes() == movie.read_bytes()


def test_figure_animation(tmp_path: pathlib.Path):
    """The still is tagged as standing in for the movie, and the caption is not."""
    a = _animated_figure(_movie(tmp_path))
    result = a.dumps()

    begin = result.index(r"\begin{interactive}{animation}{movie.mp4}")
    end = result.index(r"\end{interactive}")

    assert begin < result.index(r"\includegraphics") < end
    assert end < result.index(r"\caption")
    assert end < result.index(r"\label{fig:myFigure}")


def test_figure_animation_url(tmp_path: pathlib.Path):
    """The caption links to wherever the movie can be watched."""
    a = _animated_figure(_movie(tmp_path), caption="The evolution & the end.")
    result = a.dumps()

    assert r"The evolution \& the end." in result
    assert r"\url{https://example.org/movie.mp4}" in result
    assert result.index(r"\url") > result.index(r"\caption")
    assert any(p.arguments._positional_args == ["url"] for p in a.packages)


def test_figure_animation_url_noescape(tmp_path: pathlib.Path):
    """A caption written in LaTeX is left alone when the link is added."""
    a = _animated_figure(
        _movie(tmp_path),
        caption=aastex.NoEscape(r"The evolution of \textit{the event}."),
    )

    assert r"The evolution of \textit{the event}." in a.dumps()


def test_figure_animation_no_url(tmp_path: pathlib.Path):
    """Without a URL there is nowhere to link to."""
    a = _animated_figure(_movie(tmp_path), url=None)
    result = a.dumps()

    assert r"\begin{interactive}" in result
    assert r"\url" not in result
    assert not any(p.arguments._positional_args == ["url"] for p in a.packages)


def test_figure_animation_no_caption(tmp_path: pathlib.Path):
    """A figure without a caption is wrapped whole."""
    a = _animated_figure(_movie(tmp_path), caption=None)
    result = a.dumps()

    assert result.index(r"\includegraphics") < result.index(r"\end{interactive}")


def test_figure_without_animation():
    """An ordinary figure is not tagged."""
    assert r"\begin{interactive}" not in _figure_with_plot().dumps()


def test_figurestar_animation(tmp_path: pathlib.Path):
    a = aastex.FigureStar(
        "wide",
        animation=aastex.Animation(source=_movie(tmp_path)),
    )

    assert a.animation is not None
    assert r"\begin{figure*}" in a.dumps()
    assert r"\begin{interactive}{animation}{movie.mp4}" in a.dumps()


def test_document_animations(tmp_path: pathlib.Path):
    first = _animated_figure(_movie(tmp_path, "first.mp4"), label="first")
    second = _animated_figure(_movie(tmp_path, "second.mp4"), label="second")

    section = aastex.Section("A section")
    section.append(first)
    section.append(_figure_with_plot())
    section.append(second)

    doc = aastex.Document()
    doc.append(section)

    assert [a.name for a in doc.animations] == ["first.mp4", "second.mp4"]


def test_generate_pdf_animations(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
):
    """The movies are copied beside the PDF, so that they can be published with it."""
    doc = aastex.Document()
    doc.append(_animated_figure(_movie(tmp_path)))

    monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

    build = tmp_path / "build"
    doc.generate_pdf(build / "article")

    assert (build / "movie.mp4").exists()


def test_generate_pdf_duplicate_movie(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
):
    """Two different movies with the same name would overwrite each other."""
    doc = aastex.Document()
    for label in ("first", "second"):
        directory = tmp_path / label
        directory.mkdir()
        doc.append(_animated_figure(_movie(directory), label=label))

    monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

    with pytest.raises(ValueError, match="movie.mp4"):
        doc.generate_pdf(tmp_path / "build" / "article")


def test_generate_pdf_repeated_movie(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: pathlib.Path,
):
    """The same movie may accompany more than one figure."""
    movie = _movie(tmp_path)
    doc = aastex.Document()
    for label in ("first", "second"):
        doc.append(_animated_figure(movie, label=label))

    monkeypatch.setattr(pylatex.Document, "generate_pdf", lambda *a, **k: None)

    build = tmp_path / "build"
    doc.generate_pdf(build / "article")

    assert (build / "movie.mp4").exists()


@pytest.mark.parametrize(
    argnames="aux,name",
    argvalues=[
        (None, "figanimatedanim.zip"),
        ("\\newlabel{fig:animated}{{3}{2}{caption}{figure.3}{}}\n", "fig03anim.zip"),
        ("\\newlabel{fig:animated}{{A1}{9}{caption}{figure.A1}{}}\n", "figA1anim.zip"),
    ],
)
def test_generate_archive_animation(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    aux: None | str,
    name: str,
):
    """
    Each movie goes in an archive of its own, named after the number of its
    figure, and not in the main archive.
    """
    doc = _submittable_document()
    doc.append(_animated_figure(_movie(tmp_path), label="animated"))

    def compile(self, filepath, **kwargs):
        filepath = pathlib.Path(filepath)
        filepath.with_suffix(".tex").write_text("a compiled document")
        filepath.with_suffix(".bbl").write_text("a formatted bibliography")
        if aux is not None:
            filepath.with_suffix(".aux").write_text(aux)

    monkeypatch.setattr(pylatex.Document, "generate_pdf", compile)

    build = tmp_path / "build"
    archive = doc.generate_archive(build / "article")

    with zipfile.ZipFile(archive) as f:
        assert "movie.mp4" not in f.namelist()

    with zipfile.ZipFile(build / name) as f:
        assert f.namelist() == ["movie.mp4"]


@pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="requires a LaTeX installation",
)
def test_generate_archive_animation_compiles(tmp_path: pathlib.Path):
    """
    The interactive environment compiles, and the figure number is read back.

    The other figure of this document has no caption, so it is not numbered,
    and the animated figure is the first.
    """
    doc = _submittable_document()
    doc.append(_animated_figure(_movie(tmp_path), label="animated"))

    build = tmp_path / "build"
    doc.generate_archive(build / "article")

    assert (build / "article.pdf").exists()
    assert (build / "fig01anim.zip").exists()
    assert not (build / "figanimatedanim.zip").exists()


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Bibliography("sources"),
    ],
)
class TestBibliography:
    pass


def test_document_class_files_default():
    """By default the AASTeX class, the AAS style, and the ORCID logo are used."""
    doc = aastex.Document()

    assert [f.name for f in doc.class_files] == [
        "aastex701.cls",
        "aasjournalv7.bst",
        "orcid-ID.png",
    ]
    assert all(f.exists() for f in doc.class_files)
    assert r"\bibliographystyle{aasjournalv7}" in doc.dumps()


def test_document_other_class(tmp_path: pathlib.Path):
    """Another class, its files, and its bibliography style can be given."""
    cls = tmp_path / "other.cls"
    cls.write_text("")

    doc = aastex.Document(
        documentclass="other",
        class_files=[cls, "orcid-ID.png"],
        bibliographystyle="plain",
        document_options=[],
        linenumbers=False,
    )

    assert doc.class_files == [cls, doc.class_files[1]]
    assert doc.class_files[1].name == "orcid-ID.png"
    assert r"\documentclass{other}" in doc.dumps()
    assert r"\bibliographystyle{plain}" in doc.dumps()


def test_document_no_bibliographystyle():
    """A document may declare no bibliography style at all."""
    doc = aastex.Document(bibliographystyle=None)

    assert "bibliographystyle" not in doc.dumps()


@pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="requires a LaTeX installation",
)
def test_document_other_class_compiles(tmp_path: pathlib.Path):
    """A class file of your own is copied into the build directory and used."""
    source = tmp_path / "source"
    source.mkdir()
    cls = source / "minimal.cls"
    cls.write_text(
        "\\NeedsTeXFormat{LaTeX2e}\n"
        "\\ProvidesClass{minimal}\n"
        "\\LoadClass{article}\n"
    )

    doc = aastex.Document(
        documentclass="minimal",
        class_files=[cls],
        bibliographystyle=None,
        document_options=[],
        linenumbers=False,
    )
    doc.append(pylatex.NoEscape("A minimal article."))

    build = tmp_path / "build"
    path = build / "article"
    doc.generate_pdf(path, clean_tex=False)

    assert path.with_suffix(".pdf").exists()
    assert (build / "minimal.cls").exists()

    archive = doc.generate_archive(path)
    with zipfile.ZipFile(archive) as z:
        assert "minimal.cls" in z.namelist()
        assert "aastex701.cls" not in z.namelist()
