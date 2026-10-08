import pathlib
import shutil
import subprocess
import zipfile
import importlib.metadata

import pytest
import pylatex
import aastex
import aastex._python_packages

_doi_concept = "10.5281/zenodo.23108302"
"""The concept DOI of :mod:`aastex`, which its metadata declares."""

_latexmk = pytest.mark.skipif(
    shutil.which("latexmk") is None,
    reason="LaTeX is not installed",
)
"""Skips a test which compiles a document where LaTeX is not installed."""


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


def _declare(
    monkeypatch: pytest.MonkeyPatch,
    urls: dict[str, str],
) -> None:
    """Pretend that every package declares ``urls`` in its metadata."""
    monkeypatch.setattr(aastex.PythonPackage, "_urls", lambda self: urls)


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
        assert "    title = {{aastex}},\n" in result
        assert "    publisher = {Zenodo},\n" in result

    def test_dumps(self, a: aastex.PythonPackage) -> None:
        assert a.dumps() == rf"aastex \citep{{{a.key_}}}"


@pytest.mark.parametrize("version", ["v0.8.0", "V0.8.0", "0.8.0"])
def test_version_prefixed(version: str) -> None:
    """A version written like its tag is the same version."""
    assert aastex.PythonPackage("aastex", version=version).version_ == "0.8.0"


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


@pytest.mark.parametrize(
    argnames="declared,version,tag_prefix,url",
    argvalues=[
        (
            "https://parent.readthedocs.io/projects/child/en/latest/",
            "1.0.0",
            "v",
            "https://parent.readthedocs.io/projects/child/en/v1.0.0",
        ),
        (
            "https://parent.readthedocs.io/projects/child",
            "1.0.0",
            "v",
            "https://parent.readthedocs.io/projects/child/en/v1.0.0",
        ),
        (
            "https://example.readthedocs.io/ja/stable",
            "1.0.0",
            "v",
            "https://example.readthedocs.io/ja/v1.0.0",
        ),
        (
            "https://example.readthedocs.io",
            "1.4.2",
            "",
            "https://example.readthedocs.io/en/1.4.2",
        ),
        (
            "https://docs.astropy.org/en/stable/",
            "7.0.0",
            "v",
            "https://docs.astropy.org/en/v7.0.0",
        ),
        (
            "https://docs.astropy.org",
            "7.0.0",
            "v",
            "https://docs.astropy.org",
        ),
        (
            "https://github.com/someone/something#readme",
            "1.0.0",
            "v",
            "https://github.com/someone/something#readme",
        ),
    ],
)
def test_url_docs_layouts(
    monkeypatch: pytest.MonkeyPatch,
    declared: str,
    version: str,
    tag_prefix: str,
    url: str,
) -> None:
    """
    Documentation laid out by version is linked to the version of the tag,
    keeping the rest of the path, and anything else is used as declared.
    """
    _declare(monkeypatch, dict(documentation=declared))
    package = aastex.PythonPackage("x", version=version, tag_prefix=tag_prefix)
    assert package.url_docs == url


def test_url_docs_elsewhere() -> None:
    """Documentation not on Read the Docs has no versions to choose from."""
    urls = importlib.metadata.metadata("numpy").get_all("Project-URL")
    declared = [u.split(",")[1].strip() for u in urls if u.lower().startswith("doc")]
    assert "readthedocs" not in declared[0]
    assert aastex.PythonPackage("numpy").url_docs == declared[0].rstrip("/")


def test_url_docs_undeclared() -> None:
    assert aastex.PythonPackage("pylatex").url_docs is None


def test_not_installed() -> None:
    """A package used elsewhere can be cited by giving its version and DOI."""
    package = aastex.PythonPackage(
        name="not-an-installed-package",
        version="1.0.0",
        doi=_doi_concept,
    )
    assert package.url_docs is None
    assert package.doi_ == _doi_concept
    assert "not-an-installed-package" in _document(package).dumps()


@pytest.mark.parametrize(
    argnames="doi",
    argvalues=[
        _doi_concept,
        f"https://doi.org/{_doi_concept}",
        f"https://doi.org/{_doi_concept}/",
        f"http://dx.doi.org/{_doi_concept}",
        f"doi:{_doi_concept}",
        f"https://zenodo.org/doi/{_doi_concept}",
    ],
)
def test_doi_spellings(doi: str) -> None:
    """A DOI is understood however it is commonly written."""
    assert aastex.PythonPackage("aastex", doi=doi).doi_ == _doi_concept


def test_doi_undeclared() -> None:
    with pytest.raises(ValueError, match="does not declare a DOI"):
        _ = aastex.PythonPackage("pylatex").doi_


def test_doi_not_a_doi() -> None:
    with pytest.raises(ValueError, match="is not a DOI"):
        _ = aastex.PythonPackage("aastex", doi="https://example.org").doi_


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


def _record(doi: str, created: str) -> dict:
    """A stand-in for a record on Zenodo."""
    return dict(
        doi=doi,
        created=created,
        metadata=dict(
            title="org/my_pkg & friends: 50% of #1",
            creators=[dict(name="Doe, Jane"), dict(name="Smith and Sons Lab")],
            publication_date="2026-01-02",
            version="v1.0.0",
        ),
    )


def test_bibtex_escaped(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    What Zenodo says is written so that LaTeX prints it, and an organization
    is kept as one author.
    """
    record = _record("10.5281/zenodo.2", "2026-01-02T00:00:00")
    hits = dict(hits=dict(hits=[record]))
    monkeypatch.setattr(aastex._python_packages, "_zenodo", lambda *a, **k: hits)

    result = aastex.PythonPackage("x", version="1.0.0", doi="10.5281/zenodo.1").bibtex()

    assert r"    title = {{org/my\_pkg \& friends: 50\% of \#1}}," in result
    assert "    author = {Doe, Jane and {Smith and Sons Lab}}," in result


def test_bibtex_archived_twice(monkeypatch: pytest.MonkeyPatch) -> None:
    """A release archived twice is cited by its latest archive."""
    records = [
        _record("10.5281/zenodo.2", "2026-01-02T00:00:00"),
        _record("10.5281/zenodo.3", "2026-01-03T00:00:00"),
    ]
    hits = dict(hits=dict(hits=records))
    monkeypatch.setattr(aastex._python_packages, "_zenodo", lambda *a, **k: hits)

    result = aastex.PythonPackage("x", version="1.0.0", doi="10.5281/zenodo.1").bibtex()

    assert "    doi = {10.5281/zenodo.3}," in result


def test_dumps_escaped() -> None:
    package = aastex.PythonPackage("my_package")
    assert package.dumps() == r"my\_package \citep{my_package}"


def test_software_dumps() -> None:
    software = aastex.Software(
        [
            aastex.PythonPackage("aastex"),
            r"astropy \citep{astropy}",
            pylatex.Command("ascl", "1234"),
        ],
    )
    result = software.dumps()
    assert result == (
        r"\software{aastex \citep{aastex}, astropy \citep{astropy}, \ascl{1234}}"
    )


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
    ``\docs`` is defined once a package is cited, and knows the documentation
    of each package which has some.
    """
    assert r"\docs" not in aastex.Document().dumps()
    assert r"\docs" not in _document("IDL").dumps()

    result = _document(aastex.PythonPackage("pylatex")).dumps()
    assert r"\cs_new:Npn \docs" in result
    assert r"aastex@docs@pylatex" not in result

    result = _document(
        aastex.PythonPackage("aastex", version="0.8.0"),
        aastex.PythonPackage("pylatex"),
    ).dumps()
    assert (
        r"\expandafter\gdef\csname aastex@docs@aastex\endcsname"
        r"{https://aastex.readthedocs.io/en/v0.8.0}"
    ) in result
    assert r"aastex@docs@pylatex" not in result


def test_document_docs_unwritable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A URL which LaTeX cannot hold as text is refused."""
    _declare(monkeypatch, dict(documentation="https://example.org/a b"))
    with pytest.raises(ValueError, match="is not a URL"):
        _document(aastex.PythonPackage("x", version="1.0.0")).dumps()


def test_generate_pdf_software(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The entry of every package is written beside the article."""
    _fake_compiler(monkeypatch)
    a = aastex.PythonPackage("aastex")
    b = aastex.PythonPackage("numpy", doi=_doi_concept)

    _document(a, b).generate_pdf(tmp_path / "article")

    result = (tmp_path / "software.bib").read_text(encoding="utf-8")
    assert f"% {a._identity()}\n{_bibtex(a)}" in result
    assert f"% {b._identity()}\n{_bibtex(b)}" in result

    # a second build rewrites the file it wrote the first time
    _document(a).generate_pdf(tmp_path / "article")
    assert "numpy" not in (tmp_path / "software.bib").read_text(encoding="utf-8")


def test_generate_pdf_software_reused(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Zenodo is only asked for the entries which changed."""
    _fake_compiler(monkeypatch)
    asked = []

    def bibtex(self: aastex.PythonPackage) -> str:
        asked.append(self.version_)
        return _bibtex(self)

    monkeypatch.setattr(aastex.PythonPackage, "bibtex", bibtex)

    a = aastex.PythonPackage("aastex", version="0.7.1")
    b = aastex.PythonPackage("numpy", version="2.0.0", doi=_doi_concept)

    _document(a, b).generate_pdf(tmp_path / "article")
    assert asked == ["0.7.1", "2.0.0"]

    _document(a, b).generate_pdf(tmp_path / "article")
    assert asked == ["0.7.1", "2.0.0"]

    a = aastex.PythonPackage("aastex", version="0.8.0")
    _document(a, b).generate_pdf(tmp_path / "article")
    assert asked == ["0.7.1", "2.0.0", "0.8.0"]

    result = (tmp_path / "software.bib").read_text(encoding="utf-8")
    assert "0.7.1" not in result
    assert f"% {b._identity()}\n{_bibtex(b)}" in result


def test_generate_pdf_software_without_packages(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_compiler(monkeypatch)
    _document("IDL").generate_pdf(tmp_path / "article")
    assert not (tmp_path / "software.bib").exists()


@pytest.mark.parametrize(
    argnames="bibliography",
    argvalues=[
        aastex.Bibliography("sources, software"),
        aastex.NoEscape(r"\bibliography{sources,software.bib}"),
        pylatex.Command("bibliography", "software"),
    ],
)
def test_generate_pdf_software_in_bibliography(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    bibliography: "aastex.Bibliography | str | pylatex.Command",
) -> None:
    """The bibliography is found however it is written."""
    _fake_compiler(monkeypatch)
    doc = aastex.Document()
    doc.append(aastex.Software([aastex.PythonPackage("aastex")]))
    doc.append(bibliography)
    doc.generate_pdf(tmp_path / "article")
    assert (tmp_path / "software.bib").exists()


@pytest.mark.parametrize(
    argnames="bibliography",
    argvalues=[
        aastex.Bibliography("sources"),
        aastex.NoEscape("% \\bibliography{software}\n\\bibliography{sources}"),
    ],
)
def test_generate_pdf_software_not_in_bibliography(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    bibliography: "aastex.Bibliography | str",
) -> None:
    _fake_compiler(monkeypatch)
    doc = aastex.Document()
    doc.append(aastex.Software([aastex.PythonPackage("aastex")]))
    doc.append(bibliography)
    with pytest.raises(ValueError, match="sources of its bibliography"):
        doc.generate_pdf(tmp_path / "article")


@pytest.mark.parametrize(
    argnames="key,used",
    argvalues=[
        (None, True),
        ("aastexPython", False),
    ],
)
def test_generate_pdf_software_key_used(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    key: None | str,
    used: bool,
) -> None:
    """A key already used by the other sources of the bibliography is refused."""
    _fake_compiler(monkeypatch)
    (tmp_path / "sources.bib").write_text("@ARTICLE{ AASTeX ,\n  title = {AASTeX},\n}")
    doc = aastex.Document()
    doc.append(aastex.Software([aastex.PythonPackage("aastex", key=key)]))
    doc.append(aastex.Bibliography("sources,software"))
    if used:
        with pytest.raises(ValueError, match="already used in"):
            doc.generate_pdf(tmp_path / "article")
    else:
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


def test_generate_archive_software(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _fake_compiler(monkeypatch)
    doc = _document(aastex.PythonPackage("aastex"))
    archive = doc.generate_archive(tmp_path / "article")
    with zipfile.ZipFile(archive) as f:
        assert "software.bib" in f.namelist()


@_latexmk
def test_generate_pdf_software_compiles(tmp_path: pathlib.Path) -> None:
    """The citation and the link to the documentation survive LaTeX."""
    doc = _document(aastex.PythonPackage("aastex", version="0.8.0"))
    doc.append(r"See \href{\docs{aastex}/_autosummary/aastex.html}{the docs}.")

    doc.generate_pdf(tmp_path / "article", clean=False, clean_tex=False)

    assert (tmp_path / "article.pdf").exists()
    bbl = (tmp_path / "article.bbl").read_text(encoding="utf-8")
    assert "10.5281/zenodo.23219209" in bbl
    assert "v0.8.0" in bbl


@_latexmk
@pytest.mark.parametrize(
    argnames="prose",
    argvalues=[
        r"\href{\docs{x}/_autosummary/x.html}{x}",
        r"\url{\docs{x}}",
        r"\newcommand{\api}[1]{\href{\docs{#1}/_autosummary/#1.html}{#1}}\api{x}",
    ],
)
def test_generate_pdf_docs_compiles(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    prose: str,
) -> None:
    r"""
    ``\docs`` expands to a URL with the characters LaTeX treats specially,
    including inside a macro of the author's own.
    """
    monkeypatch.setattr(aastex.PythonPackage, "bibtex", _bibtex)
    _declare(monkeypatch, dict(documentation="https://example.org/a_b#c%20d~e&f"))
    doc = _document(aastex.PythonPackage("x", version="1.0.0", doi=_doi_concept))
    doc.append(prose)

    doc.generate_pdf(tmp_path / "article")

    assert (tmp_path / "article.pdf").exists()


@_latexmk
def test_generate_pdf_docs_unknown(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    r"""
    Linking to the documentation of a package which is not cited stops LaTeX,
    rather than making a broken link.
    """
    monkeypatch.setattr(aastex.PythonPackage, "bibtex", _bibtex)
    doc = _document(aastex.PythonPackage("aastex", version="0.8.0"))
    doc.append(r"\href{\docs{numpy}/index.html}{numpy}")

    with pytest.raises(subprocess.CalledProcessError) as error:
        doc.generate_pdf(tmp_path / "article", clean=False)

    log = (tmp_path / "article.log").read_text(encoding="utf-8", errors="replace")
    assert "The documentation of 'numpy' is not" in log
    assert error.value.returncode != 0
