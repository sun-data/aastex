import re
import json
import datetime
import dataclasses
import importlib.metadata
import urllib.parse
import urllib.request

import pylatex

__all__ = [
    "PythonPackage",
]


def _is_release(version: str) -> bool:
    """
    Whether a version of a package is a release.

    A release, such as ``2.11.1``, is only numbers, while a development
    version, a release candidate, or a build of a modified checkout carries
    letters or a local label, such as ``2.11.2.dev14+g7d61a68ed``.
    Only a release has documentation and an archive of its own.

    Parameters
    ----------
    version
        The version of the package.
    """
    return re.fullmatch(r"\d+(\.\d+)*", version) is not None


def _zenodo(path: str, **params: str) -> dict:
    """
    Query the REST API of Zenodo.

    Parameters
    ----------
    path
        The path of the endpoint, relative to ``https://zenodo.org/api/``.
    params
        The parameters of the query.
    """
    url = f"https://zenodo.org/api/{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


@dataclasses.dataclass
class PythonPackage(pylatex.base_classes.LatexObject):
    r"""
    A Python package used to produce an article.

    An article which is a program is built with particular versions of the
    packages it uses, and later versions rename and remove what the article
    describes.
    So the article should cite the version it was built with, and link to
    the documentation of that version, and both should follow when the
    version is changed.
    Everything needed is read from the metadata of the installed package,
    so the citation and the links always match the version the article was
    built with.

    Listing a package in :class:`Software` is what cites it:

    - The ``\software`` command names it as ``name \citep{key}``.
    - :meth:`Document.generate_pdf` writes its BibTeX entry,
      from :meth:`bibtex`, into ``software.bib`` beside the article,
      so the :class:`Bibliography` must list ``software`` among its sources.
    - The macro ``\docs{key}`` expands to :attr:`url_docs`,
      so the prose can link to the documentation of the version used, as in
      ``\href{\docs{optika}/_autosummary/optika.sensors.html}{...}``.

    The package should declare where its documentation is, and the concept
    DOI it is archived under on Zenodo, in the ``[project.urls]`` table of
    its ``pyproject.toml``:

    .. code-block:: toml

        [project.urls]
        Documentation = "https://optika.readthedocs.io/en/latest"
        DOI = "https://doi.org/10.5281/zenodo.23074621"

    Examples
    --------

    Cite this package, and link to its documentation.

    .. jupyter-execute::

        import aastex

        package = aastex.PythonPackage("aastex")

        print(package.dumps())
        print(package.url_docs)
        print(package.bibtex())
    """

    name: str
    """The name of the package, as given to ``pip install``."""

    key: None | str = None
    """
    The BibTeX key the article cites the package by.
    If :obj:`None`, :attr:`name` is used.
    """

    doi: None | str = None
    """
    The concept DOI of the package on Zenodo, which every release is
    archived as a version of.
    If :obj:`None`, the ``DOI`` URL in the metadata of the package is used.
    Packages which do not declare one, and releases made before they did,
    need it given here.
    """

    version: None | str = None
    """
    The version of the package to cite.
    If :obj:`None`, the installed version is used, which is the version the
    article is built with.
    """

    @property
    def key_(self) -> str:
        """
        The BibTeX key the article cites the package by, :attr:`key` if given
        and :attr:`name` otherwise.
        """
        if self.key is None:
            return self.name
        return self.key

    @property
    def version_(self) -> str:
        """
        The version of the package to cite, :attr:`version` if given and the
        installed version otherwise.
        """
        if self.version is None:
            return importlib.metadata.version(self.name)
        return self.version

    def _urls(self) -> dict[str, str]:
        """
        The URLs in the metadata of the installed package, keyed by their
        lowercase label, since packages capitalize the labels differently.
        """
        entries = importlib.metadata.metadata(self.name).get_all("Project-URL")
        result = {}
        for entry in entries or []:
            label, url = entry.split(",", maxsplit=1)
            result[label.strip().lower()] = url.strip()
        return result

    @property
    def doi_(self) -> str:
        """
        The concept DOI of the package on Zenodo, :attr:`doi` if given and the
        ``DOI`` URL in the metadata of the package otherwise.
        """
        if self.doi is not None:
            return self.doi
        url = self._urls().get("doi")
        if url is None:
            raise ValueError(
                f"{self.name} does not declare a DOI in its metadata, "
                f"so it needs to be given as `doi`."
            )
        return url.removeprefix("https://doi.org/")

    @property
    def url_docs(self) -> None | str:
        """
        The URL of the documentation of this version of the package,
        or :obj:`None` if it does not declare any.

        Read the Docs keeps the documentation of every release which is
        activated, under a version named after its tag, so a release
        ``X.Y.Z``, tagged ``vX.Y.Z``, is linked to ``/en/vX.Y.Z``.
        A development version has no documentation of its own,
        so it is linked to ``/en/latest``.
        Documentation hosted anywhere else has no versions to choose from,
        so its URL is used as it is declared.
        """
        url = self._urls().get("documentation")
        if url is None:
            return None

        parts = urllib.parse.urlsplit(url)
        if not parts.netloc.endswith(".readthedocs.io"):
            return url.rstrip("/")

        version = self.version_
        if _is_release(version):
            slug = f"v{version}"
        else:
            slug = "latest"

        return f"{parts.scheme}://{parts.netloc}/en/{slug}"

    def bibtex(self) -> str:
        """
        A BibTeX entry, with the key :attr:`key_`, citing this version of the
        package by its archive on Zenodo.

        A release is cited by the DOI of its own archive, so the citation
        names the version the article was built with.
        A development version has no archive of its own,
        so it is cited by the concept DOI, which resolves to the latest
        release, and the version is left out.

        A release which has not been archived raises an error rather than
        being cited wrongly.
        Zenodo usually archives a release within a minute of it being
        published on GitHub.
        """
        doi = self.doi_
        match = re.fullmatch(r"10\.5281/zenodo\.(\d+)", doi)
        if match is None:
            raise ValueError(f"{doi!r} is not a Zenodo DOI.")
        conceptrecid = match.group(1)

        version = self.version_
        is_release = _is_release(version)

        if is_release:
            records = _zenodo(
                "records",
                q=(
                    f"conceptrecid:{conceptrecid} AND "
                    f'metadata.version:("v{version}" OR "{version}")'
                ),
                all_versions="true",
            )["hits"]["hits"]
            if not records:
                raise ValueError(
                    f"{self.name} {version} has not been archived on Zenodo, "
                    f"so there is no DOI to cite it by."
                )
            (record,) = records
            doi_cited = record["doi"]
        else:
            record = _zenodo(f"records/{conceptrecid}/versions/latest")
            doi_cited = record["conceptdoi"]

        metadata = record["metadata"]

        fields = dict(
            author=" and ".join(c["name"] for c in metadata["creators"]),
            title=metadata["title"],
            year=datetime.date.fromisoformat(metadata["publication_date"]).year,
            publisher="Zenodo",
        )
        if is_release:
            fields["version"] = metadata["version"]
        fields["doi"] = doi_cited
        fields["url"] = f"https://doi.org/{doi_cited}"

        lines = [f"    {key} = {{{value}}}," for key, value in fields.items()]

        return "\n".join([f"@software{{{self.key_},", *lines, "}"]) + "\n"

    def dumps(self) -> str:
        """
        The package as an entry of the ``\\software`` command, its name
        followed by its citation.
        """
        return rf"{self.name} \citep{{{self.key_}}}"
