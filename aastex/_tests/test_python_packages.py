import pathlib
import shutil
import zipfile
import importlib.metadata

import pytest
import pylatex
import aastex

_doi_concept = "10.5281/zenodo.23108302"
"""The concept DOI of :mod:`aastex`, which its metadata declares."""


def _bibtex(self: aastex.PythonPackage) -> str:
    """A stand-in for :meth:`aastex.PythonPackage.bibtex` which needs no network."""
    return f"@software{{{self.key_},\n    title = {{{self.name}}},\n}}\n"


def _fake_compiler(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Stand in for the LaTeX compiler, which is not installed everywhere,
    by writing the files that a real compilation would leave behind.
    """

    def compile(self: pylatex.Document, filepath: pathlib.Path, **kwargs) -> None:
        filepath = pathlib.Path(filepath)
        filepath.with_suffix(".tex").write_text(self.dumps())
        filepath.with_suffix(".bbl").write_text("a formatted bibliography")

    monkeypatch.setattr(pylatex.Document, "generate_pdf", compile)
    monkeypatch.setattr(aastex.PythonPackage, "bibtex", _bibtex)


def _document(*names: "str | aastex.PythonPackage") -> aastex.Document:
    """A document which cites ``names`` in its software and bibliography."""
    doc = aastex.Document()
    doc.append(aastex.Software(list(names)))
    doc.append(aastex.Bibliography("software"))
    return doc


@pytest.mark.parametrize(
    argnames="a",
    argvalues=[
        aastex.PythonPackage("aastex"),
        aastex.PythonPackage("aastex", key="aastexPython", version="0.8.0"),
        aastex.PythonPackage("aastex", doi=_doi_concept, version="0.8.1.dev3"),
    ],
)
class TestPythonPackage:
    def test_key_(self, a: aastex.PythonPackage) -> None:
        if a.key is None:
            assert a.key_ == a.name
        else:
            assert a.key_ == a.key

    def test_version_(self, a: aastex.PythonPackage) -> None:
        if a.version is None:
            assert a.version_ == importlib.metadata.version(a.name)
        else:
            assert a.version_ == a.version

    def test_doi_(self, a: aastex.PythonPackage) -> None:
        assert a.doi_ == _doi_concept

    def test_url_docs(self, a: aastex.PythonPackage) -> None:
        assert a.url_docs.startswith("https://aastex.readthedocs.io/en/")

    def test_bibtex(self, a: aastex.PythonPackage) -> None:
        result = a.bibtex()
        assert result.startswith(f"@software{{{a.key_},\n")
        assert "    author = {Smart, Roy T.},\n" in result
        assert "    publisher = {Zenodo},\n" in result

    def test_dumps(self, a: aastex.PythonPackage) -> None:
        assert a.dumps() == rf"aastex \citep{{{a.key_}}}"


@pytest.mark.parametrize(
    argnames="version,url",
    argvalues=[
        ("0.8.0", "https://aastex.readthedocs.io/en/v0.8.0"),
        ("0.8.1.dev3+gabcdef0", "https://aastex.readthedocs.io/en/latest"),
        ("1.0.0rc1", "https://aastex.readthedocs.io/en/latest"),
    ],
)
def test_url_docs(version: str, url: str) -> None:
    """A release links to its own documentation, anything else to the latest."""
    assert aastex.PythonPackage("aastex", version=version).url_docs == url


def test_url_docs_elsewhere() -> None:
    """Documentation not on Read the Docs has no versions to choose from."""
    urls = importlib.metadata.metadata("numpy").get_all("Project-URL")
    declared = [u.split(",")[1].strip() for u in urls if u.lower().startswith("doc")]
    assert "readthedocs" not in declared[0]
    assert aastex.PythonPackage("numpy").url_docs == declared[0].rstrip("/")


def test_url_docs_undeclared() -> None:
    assert aastex.PythonPackage("pylatex").url_docs is None


def test_doi_undeclared() -> None:
    with pytest.raises(ValueError, match="does not declare a DOI"):
        _ = aastex.PythonPackage("pylatex").doi_


def test_doi_not_zenodo() -> None:
    with pytest.raises(ValueError, match="not a Zenodo DOI"):
        aastex.PythonPackage("aastex", doi="10.1000/182").bibtex()


@pytest.mark.parametrize(
    argnames="version,doi,version_cited",
    argvalues=[
        ("0.8.0", "10.5281/zenodo.23219209", "v0.8.0"),
        ("0.7.1", "10.5281/zenodo.23108303", "v0.7.1"),
        ("0.8.1.dev3+gabcdef0", _doi_concept, None),
    ],
)
def test_bibtex(version: str, doi: str, version_cited: None | str) -> None:
    """
    A release is cited by the archive of that release, and a development
    version by the concept DOI, without a version.
    """
    result = aastex.PythonPackage("aastex", version=version).bibtex()
    assert f"    doi = {{{doi}}},\n" in result
    assert f"    url = {{https://doi.org/{doi}}},\n" in result
    if version_cited is None:
        assert "    version = " not in result
    else:
        assert f"    version = {{{version_cited}}},\n" in result


def test_bibtex_unarchived() -> None:
    """aastex 0.7.0 was released before its releases were archived."""
    with pytest.raises(ValueError, match="has not been archived on Zenodo"):
        aastex.PythonPackage("aastex", version="0.7.0").bibtex()


def test_software_dumps() -> None:
    software = aastex.Software(
        [aastex.PythonPackage("aastex"), r"astropy \citep{astropy}"],
    )
    result = software.dumps()
    assert result == r"\software{aastex \citep{aastex}, astropy \citep{astropy}}"


def test_document_python_packages() -> None:
    """Packages are found wherever the software is, once each, in order."""
    a = aastex.PythonPackage("aastex")
    b = aastex.PythonPackage("numpy")
    section = aastex.Section("Software")
    section.append(aastex.Software([a, "IDL", b]))
    doc = aastex.Document()
    doc.append(section)
    doc.append(aastex.Software([b]))
    assert doc.python_packages == [a, b]


def test_document_python_packages_same_key() -> None:
    doc = _document(
        aastex.PythonPackage("aastex"),
        aastex.PythonPackage("numpy", key="aastex"),
    )
    with pytest.raises(ValueError, match="two different packages"):
        _ = doc.python_packages


def test_document_docs() -> None:
    r"""
    ``\docs`` is defined for each package with documentation,
    and only if there is one.
    """
    assert r"\docs" not in aastex.Document().dumps()
    assert r"\docs" not in _document(aastex.PythonPackage("pylatex")).dumps()

    result = _document(
        aastex.PythonPackage("aastex", version="0.8.0"),
        aastex.PythonPackage("pylatex"),
    ).dumps()
    assert r"\newcommand{\docs}[1]" in result
    assert (
        r"\expandafter\def\csname aastex@docs@aastex\endcsname"
        r"{https://aastex.readthedocs.io/en/v0.8.0}"
    ) in result
    assert "aastex@docs@pylatex" not in result


def test_generate_pdf_software(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The entry of every package is written beside the article."""
    _fake_compiler(monkeypatch)
    a = aastex.PythonPackage("aastex")
    b = aastex.PythonPackage("numpy")

    _document(a, b).generate_pdf(tmp_path / "article")

    result = (tmp_path / "software.bib").read_text(encoding="utf-8")
    assert result.endswith(_bibtex(a) + "\n" + _bibtex(b))

    # a second build rewrites the file it wrote the first time
    _document(a).generate_pdf(tmp_path / "article")
    assert "numpy" not in (tmp_path / "software.bib").read_text(encoding="utf-8")


def test_generate_pdf_software_without_packages(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_compiler(monkeypatch)
    _document("IDL").generate_pdf(tmp_path / "article")
    assert not (tmp_path / "software.bib").exists()


def test_generate_pdf_software_not_in_bibliography(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_compiler(monkeypatch)
    doc = aastex.Document()
    doc.append(aastex.Software([aastex.PythonPackage("aastex")]))
    doc.append(aastex.Bibliography("sources"))
    with pytest.raises(ValueError, match="sources of its bibliography"):
        doc.generate_pdf(tmp_path / "article")


def test_generate_pdf_software_not_overwritten(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ``software.bib`` of the author's own is never overwritten."""
    _fake_compiler(monkeypatch)
    path = tmp_path / "software.bib"
    path.write_text("@software{idl}")
    with pytest.raises(FileExistsError):
        _document(aastex.PythonPackage("aastex")).generate_pdf(tmp_path / "article")
    assert path.read_text() == "@software{idl}"


@pytest.mark.parametrize(
    argnames="key",
    argvalues=[
        "numpy",
        "pylatex",
    ],
)
def test_generate_pdf_docs_unknown(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    key: str,
) -> None:
    r"""
    Linking to the documentation of a package which is not cited, or which
    has none, would make a broken link.
    """
    _fake_compiler(monkeypatch)
    doc = _document(aastex.PythonPackage("aastex"), aastex.PythonPackage("pylatex"))
    doc.append(rf"\href{{\docs{{{key}}}}}{{{key}}}")
    with pytest.raises(ValueError, match=key):
        doc.generate_pdf(tmp_path / "article")


def test_generate_archive_software(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_compiler(monkeypatch)
    doc = _document(aastex.PythonPackage("aastex"))
    archive = doc.generate_archive(tmp_path / "article")
    with zipfile.ZipFile(archive) as f:
        assert "software.bib" in f.namelist()


@pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="LaTeX is not installed",
)
def test_generate_pdf_software_compiles(tmp_path: pathlib.Path) -> None:
    """The citation and the link to the documentation survive LaTeX."""
    doc = _document(aastex.PythonPackage("aastex", version="0.8.0"))
    doc.append(r"See \href{\docs{aastex}/_autosummary/aastex.html}{the docs}.")

    doc.generate_pdf(tmp_path / "article", clean=False, clean_tex=False)

    assert (tmp_path / "article.pdf").exists()
    bbl = (tmp_path / "article.bbl").read_text(encoding="utf-8")
    assert "10.5281/zenodo.23219209" in bbl
    assert "v0.8.0" in bbl
