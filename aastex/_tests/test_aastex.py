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
    ],
)
class TestAuthor:
    def test_name(self, a: aastex.Author):
        assert isinstance(a.name, str)

    def test_affiliation(self, a: aastex.Author):
        assert isinstance(a.affiliation, aastex.Affiliation)

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


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Variable("foo", 2),
        aastex.Variable("bar", 3 * u.AA),
    ],
)
class TestVariable:

    def test_name(self, a: aastex.Variable):
        assert isinstance(a.name, str)

    def test_value(self, a: aastex.Variable):
        assert isinstance(a.value, (int, float, u.Quantity))

    def test_dumps(self, a: aastex.Variable):
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
        )
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


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.Bibliography("sources"),
    ],
)
class TestBibliography:
    pass
