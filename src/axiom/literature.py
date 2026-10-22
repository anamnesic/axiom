"""zbMATH Open literature search and citation resolution for AXIOM.

Motivated by arXiv:2106.04664 ("zbMATH Open: API Solutions and Research
Challenges", Petrera et al., CEUR-WS Vol. 2976, 2021), which describes the
machine interfaces zbMATH Open exposes to automated tools. This module uses the
public REST API (``https://api.zbmath.org/v1``) for:

1. document search          (``GET /document/_search``)
2. MSC 2020 classification  (``GET /classification/_search``)
3. swMATH research software (``GET /software/_search``)
4. citation resolution: does a cited DOI / arXiv id / title resolve to an
   indexed record, and do the claimed authors match it?

Epistemic contract (fail-closed):

* Every result here is a *catalog lookup*, never a mathematical claim. A
  resolved citation proves only that a bibliographic record exists; it says
  nothing about whether the cited paper's theorems are correct. Results carry
  ``Guarantee.CATALOG_LOOKUP`` (or ``UNVERIFIED``) and therefore an
  ``INCONCLUSIVE`` epistemic state.
* An unresolved citation is **not** a refutation. zbMATH does not index every
  venue (many CS proceedings, recent preprints, theses, textbooks), so absence
  is reported as ``citation_status="unresolved"`` with
  ``hallucination_suspected=True`` - a flag for human review, not a disproof.
* A resolved record is accepted only on an exact identifier match (DOI / arXiv)
  or a strong normalized-title match, never merely because it was the top hit
  of a fuzzy search.

The offline catalog is a curated snapshot, with provenance on each record;
some works are cited by zbMATH but are not indexed documents themselves.
``tests/test_literature.py`` checks this local contract without network access.
Passing those tests does not certify the current contents of a live registry.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import ssl
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from axiom.contract import Evidence, Guarantee, MathResult, Verification, error_result

ZBMATH_API_BASE = "https://api.zbmath.org/v1"
USER_AGENT = "axiom-agent/0.3.0 (+https://github.com/chronokairo/axiom)"
ENGINE_VERSION = "zbmath-open-rest-v1"

# Minimum normalized-title similarity for a free-text citation to resolve.
TITLE_MATCH_THRESHOLD = 0.88

# ---------------------------------------------------------------------------
# Offline catalog — every identifier below was verified against the live
# zbMATH Open API on 2026-10-21. ``zbmath_id`` is the internal document id
# (https://zbmath.org/<zbmath_id>); ``zbl`` is the Zbl / JFM number.
# ---------------------------------------------------------------------------

_OFFLINE_LITERATURE: tuple[dict[str, Any], ...] = (
    {
        # arXiv:2106.04664 itself is cited in zbMATH reference lists
        # (CEUR Workshop Proceedings 2976, 4-13) but is not indexed as a
        # zbMATH document, so it carries no zbmath_id / zbl.
        "zbmath_id": None,
        "zbl": None,
        "title": "zbMATH Open: API solutions and research challenges",
        "authors": [
            "Petrera, Matteo", "Trautwein, Dennis", "Beckenbach, Isabel", "Ehsani, Dariush",
            "Müller, Fabian", "Teschke, Olaf", "Gipp, Bela", "Schubotz, Moritz",
        ],
        "year": 2021,
        "msc": [],
        "doi": None,
        "arxiv": "2106.04664",
        "venue": "CEUR Workshop Proceedings 2976, 4-13 (2021)",
        "url": "https://arxiv.org/abs/2106.04664",
        "provenance": "arXiv listing + zbMATH reference string (not a zbMATH document)",
        "keywords": "zbmath open api digital mathematics library scholix links",
    },
    {
        "zbmath_id": "7877233", "zbl": "1544.01042",
        "title": "API solutions at zbMATH Open",
        "authors": ["Petrera, Matteo", "Müller, Fabian", "Schubotz, Moritz"],
        "year": 2024, "msc": ["68V35", "01A74"], "doi": "10.4171/ZBL90/16", "arxiv": None,
        "venue": "90 years of zbMATH, EMS Press, 55-73 (2024)",
        "url": "https://zbmath.org/7877233", "provenance": "zbMATH Open",
        "keywords": "zbmath open api rest oai-pmh links digital library",
    },
    {
        "zbmath_id": "7706766", "zbl": "1514.68312",
        "title": "The integration of OEIS links in zbMATH Open",
        "authors": ["Ehsani, Dariush", "Petrera, Matteo", "Teschke, Olaf"],
        "year": 2023, "msc": ["68V35"], "doi": "10.4171/MAG/132", "arxiv": None,
        "venue": "Eur. Math. Soc. Mag. 128, 60-64 (2023)",
        "url": "https://zbmath.org/7706766", "provenance": "zbMATH Open",
        "keywords": "zbmath open oeis links api integer sequences",
    },
    {
        "zbmath_id": "3400443", "zbl": "0253.68020",
        "title": "The complexity of theorem-proving procedures",
        "authors": ["Cook, Stephen A."],
        "year": 1971, "msc": ["68T15"], "doi": "10.1145/800157.805047", "arxiv": None,
        "venue": "Proc. 3rd Ann. ACM Symp. Theory of Computing, 151-158 (1971)",
        "url": "https://zbmath.org/3400443", "provenance": "zbMATH Open",
        "keywords": "p vs np cook satisfiability np-complete complexity",
    },
    {
        "zbmath_id": "2539174", "zbl": "60.0726.05",
        "title": "On the movement of a space-filling viscous liquid",
        "authors": ["Leray, Jean"],
        "year": 1934, "msc": ["76Dxx"], "doi": "10.1007/BF02547354", "arxiv": None,
        "venue": "Acta Math. 63, 193-248 (1934)",
        "url": "https://zbmath.org/2539174", "provenance": "zbMATH Open (JFM)",
        "keywords": "navier stokes leray weak solutions viscous fluid "
                    "sur le mouvement d'un liquide visqueux emplissant l'espace",
    },
    {
        "zbmath_id": "5050939", "zbl": "1130.53001",
        "title": "The entropy formula for the Ricci flow and its geometric applications",
        "authors": ["Perelman, Grisha"],
        "year": 2002, "msc": ["53-02", "53C44", "53C21", "57M40", "57R60"],
        "doi": None, "arxiv": "math/0211159",
        "venue": "Preprint, arXiv:math/0211159 [math.DG] (2002)",
        "url": "https://zbmath.org/5050939", "provenance": "zbMATH Open",
        "keywords": "poincare conjecture ricci flow perelman geometrization",
    },
    {
        "zbmath_id": "3236938", "zbl": "0147.02506",
        "title": "Notes on elliptic curves. II",
        "authors": ["Birch, B. J.", "Swinnerton-Dyer, H. P. F."],
        "year": 1965, "msc": ["11G40", "11G05"], "doi": "10.1515/crll.1965.218.79", "arxiv": None,
        "venue": "J. Reine Angew. Math. 218, 79-108 (1965)",
        "url": "https://zbmath.org/3236938", "provenance": "zbMATH Open",
        "keywords": "birch swinnerton-dyer bsd elliptic curves l-functions",
    },
    {
        "zbmath_id": "3076397", "zbl": "0048.41701",
        "title": "The topological invariants of algebraic varieties",
        "authors": ["Hodge, W. V. D."],
        "year": 1952, "msc": [], "doi": None, "arxiv": None,
        "venue": "Proc. ICM (Cambridge, Mass., 1950) 1, 182-192 (1952)",
        "url": "https://zbmath.org/3076397", "provenance": "zbMATH Open",
        "keywords": "hodge conjecture algebraic cycles cohomology",
    },
    {
        "zbmath_id": "6538052", "zbl": "1378.81075",
        "title": "Conservation of isotopic spin and isotopic gauge invariance",
        "authors": ["Yang, C. N.", "Mills, R. L."],
        "year": 1954, "msc": ["81T13"], "doi": "10.1103/PhysRev.96.191", "arxiv": None,
        "venue": "Phys. Rev., II. Ser. 96, 191-195 (1954)",
        "url": "https://zbmath.org/6538052", "provenance": "zbMATH Open",
        "keywords": "yang-mills mass gap gauge theory",
    },
    {
        "zbmath_id": "3221502", "zbl": "0136.32301",
        "title": "Disquisitiones arithmeticae. (Translated by Arthur A. Clarke)",
        "authors": ["Gauss, Carl Friedrich"],
        "year": 1966, "msc": ["01A75", "11-03"], "doi": None, "arxiv": None,
        "venue": "Yale University Press, xx+472 p. (1966)",
        "url": "https://zbmath.org/3221502", "provenance": "zbMATH Open",
        "keywords": "gauss congruences fundamental theorem of arithmetic quadratic reciprocity",
    },
)

# MSC 2020 entries verified via GET /classification/{code}.
_OFFLINE_MSC: tuple[dict[str, Any], ...] = (
    {"code": "11-XX", "long_title": "Number theory", "parent": None},
    {"code": "11Axx", "long_title": "Elementary number theory", "parent": "11-XX"},
    {"code": "11A05", "long_title": "Multiplicative structure; Euclidean algorithm; greatest common divisors", "parent": "11Axx"},
    {"code": "11A07", "long_title": "Congruences; primitive roots; residue systems", "parent": "11Axx"},
    {"code": "11A41", "long_title": "Primes", "parent": "11Axx"},
    {"code": "11M06", "long_title": "zeta(s) and L(s, chi)", "parent": "11Mxx"},
    {"code": "11M26", "long_title": "Nonreal zeros of zeta(s) and L(s, chi); Riemann and other hypotheses", "parent": "11Mxx"},
    {"code": "11G05", "long_title": "Elliptic curves over global fields", "parent": "11Gxx"},
    {"code": "11G40", "long_title": "L-functions of varieties over global fields; Birch-Swinnerton-Dyer conjecture", "parent": "11Gxx"},
    {"code": "14C30", "long_title": "Transcendental methods, Hodge theory (algebro-geometric aspects), Hodge conjecture", "parent": "14Cxx"},
    {"code": "35Q30", "long_title": "Navier-Stokes equations", "parent": "35Qxx"},
    {"code": "76D05", "long_title": "Navier-Stokes equations for incompressible viscous fluids", "parent": "76Dxx"},
    {"code": "68Q15", "long_title": "Complexity classes (hierarchies, relations among complexity classes, etc.)", "parent": "68Qxx"},
    {"code": "81T13", "long_title": "Yang-Mills and other gauge theories in quantum field theory", "parent": "81Txx"},
    {"code": "68V35", "long_title": "Digital mathematics libraries and repositories", "parent": "68Vxx"},
    {"code": "01A75", "long_title": "Collected or selected works; reprintings or translations of classics", "parent": "01Axx"},
)

# swMATH ids verified via GET /software/_search.
_OFFLINE_SOFTWARE: tuple[dict[str, Any], ...] = (
    {"id": "15148", "name": "Lean", "keywords": "lean theorem prover dependent type theory formal verification"},
    {"id": "940", "name": "SymPy", "keywords": "sympy computer algebra symbolic python"},
    {"id": "3312", "name": "MPFR", "keywords": "mpfr multiple precision floating point correct rounding"},
    {"id": "297", "name": "FLINT", "keywords": "flint fast library number theory"},
    {"id": "680", "name": "PARI/GP", "keywords": "pari gp number theory computer algebra"},
)


# ---------------------------------------------------------------------------
# Normalization & matching helpers
# ---------------------------------------------------------------------------

_DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\"'<>]+)", re.IGNORECASE)
_ARXIV_NEW_RE = re.compile(r"(?<![\d.])(\d{4}\.\d{4,5})(?:v\d+)?(?![\d])")
_ARXIV_OLD_RE = re.compile(r"\b([a-z][a-z\-]*(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?\b", re.IGNORECASE)


def _norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    d = doi.strip().lower()
    d = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", d)
    return d.rstrip(".,;)") or None


def _norm_arxiv(ax: str | None) -> str | None:
    if not ax:
        return None
    a = ax.strip().lower()
    a = re.sub(r"^(https?://arxiv\.org/(abs|pdf)/|arxiv:\s*)", "", a)
    a = re.sub(r"v\d+$", "", a)
    return a or None


def _norm_text(text: str) -> str:
    t = unicodedata.normalize("NFKD", text)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower()
    return " ".join(re.findall(r"[a-z0-9]+", t))


def _title_similarity(candidate: str, citation_text: str) -> float:
    """Similarity of a record title to a citation; containment scores 1.0."""
    ct, cc = _norm_text(candidate), _norm_text(citation_text)
    if not ct or not cc:
        return 0.0
    if ct in cc:
        return 1.0
    return difflib.SequenceMatcher(None, ct, cc).ratio()


def _surnames(authors: list[str]) -> set[str]:
    out: set[str] = set()
    for a in authors:
        head = a.split(",")[0] if "," in a else (a.split()[-1] if a.split() else "")
        for tok in _norm_text(head).split():
            if len(tok) >= 3:
                out.add(tok)
    return out


def extract_identifiers(text: str) -> dict[str, str | None]:
    """Extract a DOI and/or arXiv identifier from free citation text."""
    doi_m = _DOI_RE.search(text)
    doi = _norm_doi(doi_m.group(1)) if doi_m else None
    stripped = _DOI_RE.sub(" ", text)  # avoid reading DOI digits as an arXiv id
    ax_m = _ARXIV_NEW_RE.search(stripped) or _ARXIV_OLD_RE.search(stripped)
    return {"doi": doi, "arxiv": _norm_arxiv(ax_m.group(1)) if ax_m else None}


# ---------------------------------------------------------------------------
# HTTP layer (TLS is verified; never silently downgraded)
# ---------------------------------------------------------------------------

class ZbmathUnavailable(Exception):
    """Raised when the live API cannot be reached; the reason is surfaced to the user."""


def _ssl_context() -> ssl.SSLContext:
    """TLS context honoring AXIOM_CA_BUNDLE; verification is disabled only by explicit opt-in."""
    if os.environ.get("AXIOM_ZBMATH_INSECURE_TLS") == "1":
        return ssl._create_unverified_context()  # explicit user opt-in only
    cafile = os.environ.get("AXIOM_CA_BUNDLE") or None
    return ssl.create_default_context(cafile=cafile)


def _fetch(endpoint: str, params: dict[str, Any], timeout: int) -> list[dict[str, Any]]:
    """Query the zbMATH Open REST API. HTTP 404 means "no results"."""
    qs = urllib.parse.urlencode({k: str(v) for k, v in params.items() if v is not None})
    url = f"{ZBMATH_API_BASE}/{endpoint}?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, context=_ssl_context(), timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return []
        raise ZbmathUnavailable(f"HTTP {exc.code} from zbMATH Open") from exc
    except ssl.SSLError as exc:
        raise ZbmathUnavailable(
            f"TLS verification failed ({exc}); set AXIOM_CA_BUNDLE to your CA bundle "
            "or AXIOM_ZBMATH_INSECURE_TLS=1 to opt out"
        ) from exc
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            raise ZbmathUnavailable(
                f"TLS verification failed ({reason}); set AXIOM_CA_BUNDLE to your CA bundle "
                "or AXIOM_ZBMATH_INSECURE_TLS=1 to opt out"
            ) from exc
        raise ZbmathUnavailable(f"network error: {reason}") from exc
    except (TimeoutError, OSError, ValueError) as exc:
        raise ZbmathUnavailable(f"{type(exc).__name__}: {exc}") from exc
    result = payload.get("result", [])
    if isinstance(result, dict):
        result = [result]
    return result if isinstance(result, list) else []


def _record_from_api(item: dict[str, Any]) -> dict[str, Any]:
    title_obj = item.get("title")
    title = title_obj.get("title") if isinstance(title_obj, dict) else title_obj
    links = [lk for lk in item.get("links", []) if isinstance(lk, dict)]
    doi = next((lk.get("identifier") for lk in links if str(lk.get("type", "")).lower() == "doi"), None)
    arxiv = next((lk.get("identifier") for lk in links if str(lk.get("type", "")).lower() == "arxiv"), None)
    zid = item.get("id")
    year = item.get("year")
    return {
        "zbmath_id": str(zid) if zid is not None else None,
        "zbl": item.get("identifier"),
        "title": title or "Untitled",
        "authors": [a.get("name") for a in item.get("contributors", {}).get("authors", []) if a.get("name")],
        "year": int(year) if str(year or "").isdigit() else year,
        "msc": [m.get("code") for m in item.get("msc", []) if isinstance(m, dict) and m.get("code")],
        "doi": doi,
        "arxiv": arxiv,
        "venue": (item.get("source") or {}).get("source"),
        "url": item.get("zbmath_url") or (f"https://zbmath.org/{zid}" if zid else None),
        "provenance": "zbMATH Open (live)",
    }


def _offline_search(query: str, max_results: int) -> list[dict[str, Any]]:
    ids = extract_identifiers(query)
    hits: list[tuple[float, dict[str, Any]]] = []
    terms = [t for t in _norm_text(query).split() if len(t) >= 3]
    for entry in _OFFLINE_LITERATURE:
        if ids["doi"] and _norm_doi(entry["doi"]) == ids["doi"]:
            hits.append((100.0, entry)); continue
        if ids["arxiv"] and _norm_arxiv(entry["arxiv"]) == ids["arxiv"]:
            hits.append((100.0, entry)); continue
        hay = _norm_text(" ".join([entry["title"], " ".join(entry["authors"]), entry["keywords"]]))
        score = sum(1 for t in terms if t in hay)
        if score:
            hits.append((float(score), entry))
    hits.sort(key=lambda p: p[0], reverse=True)
    return [dict(e, provenance=e["provenance"] + " [offline catalog]") for _, e in hits[:max_results]]


def _catalog_result(
    kind: str, query: str, matches: list[dict[str, Any]], *, engine: str, method: str,
    summary: str, reproducible: str, warnings: list[str], limitations: list[str],
) -> MathResult:
    found = bool(matches)
    return MathResult(
        kind=kind,
        input=query,
        ok=True,
        value={"query": query, "count": len(matches), "matches": matches},
        value_str=summary,
        guarantee=Guarantee.CATALOG_LOOKUP if found else Guarantee.UNVERIFIED,
        evidence=Evidence(
            engine=engine, engine_version=ENGINE_VERSION, method=method,
            steps=[f"query: {query}", f"matches: {len(matches)}"],
            limitations=limitations, reproducible_with=reproducible,
        ),
        verification=Verification(
            kind="catalog-lookup", passed=found,
            detail=f"{len(matches)} record(s) retrieved" if found else "no records matched",
            checks=len(matches),
        ),
        warnings=warnings,
    )


_CATALOG_LIMITATION = (
    "Bibliographic catalog lookup only: a matching record says nothing about the "
    "mathematical correctness of the cited work."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_literature(query: str, *, max_results: int = 8, online: bool = True, timeout: int = 10) -> MathResult:
    """Search mathematical literature via zbMATH Open (offline catalog fallback)."""
    q = query.strip()
    if not q:
        return error_result("search_literature", query, "query must not be empty", engine="zbmath-open")
    warnings: list[str] = []
    matches: list[dict[str, Any]] = []
    method = "zbMATH Open REST API GET /document/_search"
    if online:
        try:
            matches = [_record_from_api(it) for it in _fetch(
                "document/_search", {"search_string": q, "results_per_page": max_results}, timeout)][:max_results]
        except ZbmathUnavailable as exc:
            warnings.append(f"zbMATH Open unavailable ({exc}); using offline catalog")
            online = False
    if not online:
        matches = _offline_search(q, max_results)
        method = "AXIOM offline zbMATH catalog (verified subset)"
    lines = [f"{len(matches)} record(s):"] if matches else [f"No records matched {q!r}."]
    for i, m in enumerate(matches, 1):
        au = ", ".join(m["authors"][:3]) + (" et al." if len(m["authors"]) > 3 else "")
        ref = f"Zbl {m['zbl']}" if m.get("zbl") else (f"arXiv:{m['arxiv']}" if m.get("arxiv") else "")
        lines.append(f"  {i}. {au} ({m.get('year')}). {m['title']}. {ref} {m.get('url') or ''}".rstrip())
    return _catalog_result(
        "search_literature", q, matches, engine="zbmath-open", method=method, summary="\n".join(lines),
        reproducible=f'axiom literature "{q}"', warnings=warnings, limitations=[_CATALOG_LIMITATION],
    )


def lookup_msc(code_or_query: str, *, max_results: int = 5, online: bool = True, timeout: int = 10) -> MathResult:
    """Look up MSC 2020 classification codes by code or topic."""
    q = code_or_query.strip()
    if not q:
        return error_result("lookup_msc", code_or_query, "MSC code or query must not be empty", engine="zbmath-msc")
    warnings: list[str] = []
    matches: list[dict[str, Any]] = []
    method = "zbMATH Open REST API GET /classification/_search"
    if online:
        try:
            for it in _fetch("classification/_search", {"search_string": q, "results_per_page": max_results}, timeout):
                matches.append({"code": it.get("code"), "long_title": it.get("long_title"),
                                "parent": it.get("parent"), "url": it.get("zbmath_url")})
        except ZbmathUnavailable as exc:
            warnings.append(f"zbMATH Open unavailable ({exc}); using offline catalog")
            online = False
    if not online:
        ql = q.lower()
        exact = [e for e in _OFFLINE_MSC if e["code"].lower() == ql]
        fuzzy = [e for e in _OFFLINE_MSC if e not in exact and (ql in e["code"].lower() or ql in e["long_title"].lower())]
        matches = [dict(e, url=f"https://zbmath.org/classification/?q=cc:{e['code']}") for e in (exact + fuzzy)[:max_results]]
        method = "AXIOM offline MSC 2020 catalog (verified subset)"
    lines = [f"{len(matches)} MSC 2020 code(s):"] if matches else [f"No MSC 2020 code matched {q!r}."]
    lines += [f"  {i}. [{m['code']}] {m['long_title']}" for i, m in enumerate(matches, 1)]
    return _catalog_result(
        "lookup_msc", q, matches, engine="zbmath-msc", method=method, summary="\n".join(lines),
        reproducible=f'axiom msc "{q}"', warnings=warnings, limitations=[],
    )


def search_software(query: str, *, max_results: int = 5, online: bool = True, timeout: int = 10) -> MathResult:
    """Search mathematical research software indexed by swMATH / zbMATH Open."""
    q = query.strip()
    if not q:
        return error_result("search_software", query, "software query must not be empty", engine="zbmath-swmath")
    warnings: list[str] = []
    matches: list[dict[str, Any]] = []
    method = "zbMATH Open REST API GET /software/_search"
    if online:
        try:
            for it in _fetch("software/_search", {"search_string": q, "results_per_page": max_results}, timeout):
                sid = it.get("id")
                matches.append({"id": str(sid), "name": it.get("name"), "url": f"https://zbmath.org/software/{sid}"})
        except ZbmathUnavailable as exc:
            warnings.append(f"zbMATH Open unavailable ({exc}); using offline catalog")
            online = False
    if not online:
        ql = q.lower()
        matches = [
            {"id": e["id"], "name": e["name"], "url": f"https://zbmath.org/software/{e['id']}"}
            for e in _OFFLINE_SOFTWARE if ql in e["name"].lower() or ql in e["keywords"]
        ][:max_results]
        method = "AXIOM offline swMATH catalog (verified subset)"
    lines = [f"{len(matches)} software record(s):"] if matches else [f"No software matched {q!r}."]
    lines += [f"  {i}. {m['name']} (swMATH {m['id']}) {m['url']}" for i, m in enumerate(matches, 1)]
    return _catalog_result(
        "search_software", q, matches, engine="zbmath-swmath", method=method, summary="\n".join(lines),
        reproducible=f'axiom software "{q}"', warnings=warnings, limitations=[],
    )


def _resolve(candidates: list[dict[str, Any]], ids: dict[str, str | None], title: str, text: str) -> tuple[dict[str, Any] | None, str]:
    """Pick a candidate only on an exact identifier match or a strong title match."""
    for c in candidates:
        if ids["doi"] and _norm_doi(c.get("doi")) == ids["doi"]:
            return c, "doi-exact"
        if ids["arxiv"] and _norm_arxiv(c.get("arxiv")) == ids["arxiv"]:
            return c, "arxiv-exact"
    if ids["doi"] or ids["arxiv"]:
        return None, "identifier-not-found"
    best, best_score = None, 0.0
    for c in candidates:
        score = _title_similarity(c.get("title", ""), title or text)
        if score > best_score:
            best, best_score = c, score
    if best is not None and best_score >= TITLE_MATCH_THRESHOLD:
        return best, f"title-match({best_score:.2f})"
    return None, f"no-title-match(best={best_score:.2f})"


def verify_citation(citation: str | dict[str, Any], *, online: bool = True, timeout: int = 10) -> MathResult:
    """Resolve a citation against zbMATH Open and check author attribution.

    ``citation_status`` is one of ``resolved``, ``attribution_mismatch`` or
    ``unresolved``. Only ``resolved`` passes verification. None of these is a
    mathematical claim, and ``unresolved`` is never reported as a refutation.
    """
    if isinstance(citation, dict):
        input_str = json.dumps(citation, ensure_ascii=False)
        title = str(citation.get("title") or "")
        authors_raw = citation.get("authors") or citation.get("author") or []
        claimed_authors = authors_raw if isinstance(authors_raw, list) else re.split(r"\s+and\s+|;", str(authors_raw))
        ids = {"doi": _norm_doi(citation.get("doi")), "arxiv": _norm_arxiv(citation.get("arxiv") or citation.get("eprint"))}
        text = " ".join(filter(None, [title, " ".join(map(str, claimed_authors))]))
    else:
        input_str = str(citation).strip()
        title, claimed_authors, text = "", [], input_str
        ids = extract_identifiers(input_str)
    if not input_str or input_str in ("{}", '""'):
        return error_result("verify_citation", input_str, "citation must not be empty", engine="zbmath-open")

    query = ids["doi"] or ids["arxiv"] or title or text
    warnings: list[str] = []
    candidates: list[dict[str, Any]] = []
    source = "zbMATH Open (live)"
    if online:
        try:
            candidates = [_record_from_api(it) for it in _fetch(
                "document/_search", {"search_string": query, "results_per_page": 10}, timeout)]
        except ZbmathUnavailable as exc:
            warnings.append(f"zbMATH Open unavailable ({exc}); using offline catalog")
            online = False
    record, how = _resolve(candidates, ids, title, text) if candidates else (None, "no-candidates")
    if record is None:
        # The offline catalog also covers works cited but not indexed (e.g. arXiv:2106.04664).
        offline_record, offline_how = _resolve(list(_OFFLINE_LITERATURE), ids, title, text)
        if offline_record is not None:
            record, how, source = dict(offline_record), offline_how, "AXIOM offline catalog"

    steps = [f"query: {query}", f"identifiers: {ids}", f"resolution: {how} via {source if record else 'none'}"]
    if record is None:
        return MathResult(
            kind="verify_citation", input=input_str, ok=True,
            value={"citation_status": "unresolved", "hallucination_suspected": True,
                   "identifiers": ids, "resolution": how},
            value_str=(f"[UNRESOLVED] {query!r} did not resolve to an indexed record. This is not "
                       "proof the work is fabricated (zbMATH does not index every venue); verify manually."),
            guarantee=Guarantee.UNVERIFIED,
            evidence=Evidence(engine="zbmath-open", engine_version=ENGINE_VERSION,
                              method="citation resolution (exact identifier or title >= "
                                     f"{TITLE_MATCH_THRESHOLD})", steps=steps,
                              limitations=["Absence from zbMATH Open is not evidence of falsity."],
                              reproducible_with=f'axiom verify-citation "{query}"'),
            verification=Verification(kind="citation-resolution", passed=False,
                                      detail=f"unresolved ({how})", checks=1),
            warnings=warnings,
        )

    record_surnames = _surnames(record.get("authors", []))
    claimed_surnames = _surnames([str(a) for a in claimed_authors])
    if not claimed_surnames and not isinstance(citation, dict):
        # free text: any surname of the record that appears counts as a claimed author
        cited = set(_norm_text(input_str).split())
        claimed_surnames = record_surnames & cited
    missing = sorted(claimed_surnames - record_surnames) if isinstance(citation, dict) else []
    attribution_ok = not missing
    status = "resolved" if attribution_ok else "attribution_mismatch"
    steps.append(f"author check: claimed={sorted(claimed_surnames)} record={sorted(record_surnames)}")
    label = "[RESOLVED]" if attribution_ok else "[ATTRIBUTION MISMATCH]"
    ref = f"Zbl {record['zbl']}" if record.get("zbl") else (f"arXiv:{record['arxiv']}" if record.get("arxiv") else "")
    return MathResult(
        kind="verify_citation", input=input_str, ok=True,
        value={"citation_status": status, "hallucination_suspected": not attribution_ok,
               "resolution": how, "record": record, "missing_authors": missing},
        value_str=(f"{label} {', '.join(record['authors'][:3])} ({record.get('year')}). "
                   f"{record['title']}. {ref} {record.get('url') or ''}").rstrip()
                  + ("" if attribution_ok else f" | claimed author(s) not on record: {missing}"),
        guarantee=Guarantee.CATALOG_LOOKUP if attribution_ok else Guarantee.UNVERIFIED,
        evidence=Evidence(engine="zbmath-open", engine_version=ENGINE_VERSION,
                          method="citation resolution (exact identifier or title >= "
                                 f"{TITLE_MATCH_THRESHOLD}) + author attribution check",
                          steps=steps, limitations=[_CATALOG_LIMITATION],
                          reproducible_with=f'axiom verify-citation "{query}"'),
        verification=Verification(kind="citation-resolution", passed=attribution_ok,
                                  detail=f"{status} ({how})", checks=2,
                                  data={"zbmath_id": record.get("zbmath_id"), "zbl": record.get("zbl")}),
        warnings=warnings,
    )
