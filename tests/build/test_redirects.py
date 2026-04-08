"""
Property-based tests for .htaccess redirect rules.

Feature: arpilf-website-rebuild

Tests:
  - P15: Redirecionamentos de URLs antigos do Joomla

Validates: Requirements 12.2, 12.3, 12.4
"""

import os
import re

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# .htaccess parsing helpers
# ---------------------------------------------------------------------------

HTACCESS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "static", ".htaccess")
)


def parse_rewrite_rules(htaccess_path):
    """Parse RewriteRule directives from .htaccess and return a list of
    (pattern, substitution, flags) tuples.

    Only captures simple RewriteRule lines (no preceding RewriteCond).
    """
    rules = []
    with open(htaccess_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    prev_line_is_cond = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("RewriteCond"):
            prev_line_is_cond = True
            continue
        if stripped.startswith("RewriteRule"):
            match = re.match(
                r"RewriteRule\s+(\S+)\s+(\S+)(?:\s+\[([^\]]*)\])?",
                stripped,
            )
            if match:
                pattern, substitution, flags = match.groups()
                flags = flags or ""
                rules.append((pattern, substitution, flags, prev_line_is_cond))
            prev_line_is_cond = False
        else:
            prev_line_is_cond = False

    return rules


def parse_fallback_rules(htaccess_path):
    """Parse RewriteRule directives that are preceded by RewriteCond lines
    (i.e. the fallback rules), excluding the HTTPS force rule.
    """
    all_rules = parse_rewrite_rules(htaccess_path)
    fallback = []
    for p, s, f, has_cond in all_rules:
        if not has_cond:
            continue
        # Skip the HTTPS force rule
        if "HTTP_HOST" in s or "%{REQUEST_URI}" in s:
            continue
        fallback.append((p, s, f))
    return fallback


def parse_direct_redirect_rules(htaccess_path):
    """Parse RewriteRule directives that are NOT preceded by RewriteCond
    (direct redirect rules), excluding the HTTPS force rule.
    """
    all_rules = parse_rewrite_rules(htaccess_path)
    direct = []
    for pattern, substitution, flags, has_cond in all_rules:
        if has_cond:
            continue
        # Skip the HTTPS force rule
        if "HTTP_HOST" in substitution or "%{REQUEST_URI}" in substitution:
            continue
        if "R=301" in flags:
            direct.append((pattern, substitution, flags))
    return direct


def apply_rewrite_rule(pattern, substitution, url):
    """Apply an Apache RewriteRule regex substitution to a URL path.

    Returns the redirect target or None if the pattern doesn't match.
    """
    m = re.match(pattern, url)
    if not m:
        return None

    # Perform backreference substitution ($1, $2, etc.)
    result = substitution
    for i, group in enumerate(m.groups(), start=1):
        result = result.replace(f"${i}", group if group is not None else "")

    return result


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating URLs matching redirect patterns
# ---------------------------------------------------------------------------

def safe_filename_chars():
    """Strategy for characters valid in filenames/URL paths."""
    return st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="-_",
    )


def publicacao_contas_url_strategy():
    """Generate URLs matching: images/Publicacao_contas_*.pdf"""
    suffix = st.text(
        alphabet=safe_filename_chars(),
        min_size=1,
        max_size=20,
    ).filter(lambda s: len(s.strip()) >= 1 and s.strip() == s)
    return suffix.map(lambda s: f"images/Publicacao_contas_{s}.pdf")


def regulamento_url_strategy():
    """Generate URLs matching: images/Regulamento*.pdf"""
    suffix = st.text(
        alphabet=safe_filename_chars(),
        min_size=1,
        max_size=30,
    ).filter(lambda s: len(s.strip()) >= 1 and s.strip() == s)
    return suffix.map(lambda s: f"images/Regulamento{s}.pdf")


def site2020_url_strategy():
    """Generate URLs matching: site2020/*"""
    path = st.text(
        alphabet=safe_filename_chars(),
        min_size=0,
        max_size=30,
    ).map(str.strip)
    return path.map(lambda p: f"site2020/{p}")


def stg_url_strategy():
    """Generate URLs matching: stg/*"""
    path = st.text(
        alphabet=safe_filename_chars(),
        min_size=0,
        max_size=30,
    ).map(str.strip)
    return path.map(lambda p: f"stg/{p}")


def joomla_component_url_strategy():
    """Generate URLs matching fallback: index.php/component/*"""
    path = st.text(
        alphabet=safe_filename_chars(),
        min_size=1,
        max_size=40,
    ).filter(lambda s: len(s.strip()) >= 1)
    return path.map(lambda p: f"index.php/component/{p}")


def administrator_url_strategy():
    """Generate URLs matching fallback: administrator*"""
    suffix = st.text(
        alphabet=safe_filename_chars(),
        min_size=0,
        max_size=30,
    ).map(str.strip)
    return suffix.map(lambda s: f"administrator{s}")


# ---------------------------------------------------------------------------
# Property 15: Redirecionamentos de URLs antigos do Joomla
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 15: Para qualquer URL antigo do
# Joomla que corresponda a um padrão definido no .htaccess (ex:
# /images/Publicacao_contas_*.pdf, /images/Regulamento*.pdf, /site2020/*),
# o servidor deve retornar um redirecionamento HTTP 301 para o URL
# correspondente no novo site. Para URLs antigos sem correspondência direta
# (ex: /index.php/component/*), deve redirecionar para a homepage.
#
# Validates: Requirements 12.2, 12.3, 12.4


class TestProperty15Redirects:
    """Property 15: Joomla URL redirects via .htaccess RewriteRules."""


    def setup_method(self):
        """Parse .htaccess rules once for each test method."""
        self.direct_rules = parse_direct_redirect_rules(HTACCESS_PATH)
        self.fallback_rules = parse_fallback_rules(HTACCESS_PATH)

    # --- Direct redirect: Publicacao_contas ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(url=publicacao_contas_url_strategy())
    def test_publicacao_contas_redirect(self, url):
        """
        **Validates: Requirements 12.2**

        Publicacao_contas PDFs redirect to /documentos/relatorios-financeiros/.
        """
        pattern = r"^images/Publicacao_contas_(.*)\.pdf$"
        substitution = r"/documentos/relatorios-financeiros/Publicacao_contas_$1.pdf"

        # Verify the rule exists in .htaccess
        rule_found = any(p == pattern for p, _, _ in self.direct_rules)
        # The actual .htaccess uses slightly different escaping; match by key part
        rule_found = any("Publicacao_contas" in p for p, _, _ in self.direct_rules)
        assert rule_found, "Publicacao_contas redirect rule not found in .htaccess"

        # Find the actual rule
        for p, s, _ in self.direct_rules:
            if "Publicacao_contas" in p:
                result = apply_rewrite_rule(p, s, url)
                if result is not None:
                    # Extract the suffix from the URL
                    m = re.match(r"images/Publicacao_contas_(.*)\.pdf", url)
                    assert m is not None
                    suffix = m.group(1)
                    expected = f"/documentos/relatorios-financeiros/Publicacao_contas_{suffix}.pdf"
                    assert result == expected, (
                        f"URL '{url}' should redirect to '{expected}', got '{result}'"
                    )
                    return

        pytest.fail(f"No redirect rule matched URL: {url}")

    # --- Direct redirect: Regulamento ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(url=regulamento_url_strategy())
    def test_regulamento_redirect(self, url):
        """
        **Validates: Requirements 12.2**

        Regulamento PDFs redirect to /documentos/regulamentos/.
        """
        rule_found = any("Regulamento" in p for p, _, _ in self.direct_rules)
        assert rule_found, "Regulamento redirect rule not found in .htaccess"

        for p, s, _ in self.direct_rules:
            if "Regulamento" in p:
                result = apply_rewrite_rule(p, s, url)
                if result is not None:
                    m = re.match(r"images/Regulamento(.*)\.pdf", url)
                    assert m is not None
                    suffix = m.group(1)
                    expected = f"/documentos/regulamentos/Regulamento{suffix}.pdf"
                    assert result == expected, (
                        f"URL '{url}' should redirect to '{expected}', got '{result}'"
                    )
                    return

        pytest.fail(f"No redirect rule matched URL: {url}")

    # --- Direct redirect: static PDF files ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(
        pdf=st.sampled_from([
            ("images/estatutos_arpilf.pdf", "/documentos/estatutos/estatutos_arpilf.pdf"),
            ("images/FichaCentroDia.pdf", "/documentos/fichas-inscricao/FichaCentroDia.pdf"),
            ("images/FichaInscricao.pdf", "/documentos/fichas-inscricao/FichaInscricao.pdf"),
            ("images/ProteccaoDeDados.pdf", "/documentos/outros/ProteccaoDeDados.pdf"),
        ])
    )
    def test_static_pdf_redirects(self, pdf):
        """
        **Validates: Requirements 12.2**

        Static PDF redirects (estatutos, fichas, protecao de dados) map to
        their exact new locations.
        """
        old_url, expected_target = pdf

        matched = False
        for p, s, _ in self.direct_rules:
            result = apply_rewrite_rule(p, s, old_url)
            if result is not None:
                assert result == expected_target, (
                    f"URL '{old_url}' should redirect to '{expected_target}', "
                    f"got '{result}'"
                )
                matched = True
                break

        assert matched, f"No redirect rule matched URL: {old_url}"

    # --- Direct redirect: site2020/* ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(url=site2020_url_strategy())
    def test_site2020_redirect(self, url):
        """
        **Validates: Requirements 12.3**

        site2020/* URLs redirect to /* (strip the site2020/ prefix).
        """
        rule_found = any("site2020" in p for p, _, _ in self.direct_rules)
        assert rule_found, "site2020 redirect rule not found in .htaccess"

        for p, s, _ in self.direct_rules:
            if "site2020" in p:
                result = apply_rewrite_rule(p, s, url)
                if result is not None:
                    # Extract the path after site2020/
                    suffix = url[len("site2020/"):]
                    expected = f"/{suffix}"
                    assert result == expected, (
                        f"URL '{url}' should redirect to '{expected}', got '{result}'"
                    )
                    return

        pytest.fail(f"No redirect rule matched URL: {url}")

    # --- Direct redirect: stg/* ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(url=stg_url_strategy())
    def test_stg_redirect(self, url):
        """
        **Validates: Requirements 12.3**

        stg/* URLs redirect to /* (strip the stg/ prefix).
        """
        rule_found = any("stg" in p for p, _, _ in self.direct_rules)
        assert rule_found, "stg redirect rule not found in .htaccess"

        for p, s, _ in self.direct_rules:
            if "stg/" in p:
                result = apply_rewrite_rule(p, s, url)
                if result is not None:
                    suffix = url[len("stg/"):]
                    expected = f"/{suffix}"
                    assert result == expected, (
                        f"URL '{url}' should redirect to '{expected}', got '{result}'"
                    )
                    return

        pytest.fail(f"No redirect rule matched URL: {url}")

    # --- Fallback: index.php/component/* → homepage ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(url=joomla_component_url_strategy())
    def test_joomla_component_fallback_to_homepage(self, url):
        """
        **Validates: Requirements 12.4**

        index.php/component/* URLs (no direct match) redirect to homepage.
        """
        # First check that no direct rule matches this URL
        for p, s, _ in self.direct_rules:
            direct_result = apply_rewrite_rule(p, s, url)
            if direct_result is not None:
                # A direct rule matched — that's fine, it's handled
                return

        # No direct rule matched, so the fallback should apply
        fallback_matched = False
        for p, s, _ in self.fallback_rules:
            result = apply_rewrite_rule(p, s, url)
            if result is not None:
                assert result == "/", (
                    f"Fallback for '{url}' should redirect to '/', got '{result}'"
                )
                fallback_matched = True
                break

        assert fallback_matched, (
            f"URL '{url}' should be caught by fallback rule but wasn't"
        )

    # --- Fallback: administrator* → homepage ---

    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(url=administrator_url_strategy())
    def test_administrator_fallback_to_homepage(self, url):
        """
        **Validates: Requirements 12.4**

        administrator* URLs redirect to homepage via fallback.
        """
        # First check that no direct rule matches
        for p, s, _ in self.direct_rules:
            direct_result = apply_rewrite_rule(p, s, url)
            if direct_result is not None:
                return

        # Fallback should catch it
        fallback_matched = False
        for p, s, _ in self.fallback_rules:
            result = apply_rewrite_rule(p, s, url)
            if result is not None:
                assert result == "/", (
                    f"Fallback for '{url}' should redirect to '/', got '{result}'"
                )
                fallback_matched = True
                break

        assert fallback_matched, (
            f"URL '{url}' should be caught by fallback rule but wasn't"
        )

    # --- Verify all redirect rules are 301 ---

    def test_all_redirects_are_301(self):
        """
        **Validates: Requirements 12.2**

        All Joomla redirect rules must use R=301 (permanent redirect).
        """
        for pattern, substitution, flags in self.direct_rules:
            assert "R=301" in flags, (
                f"Rule '{pattern}' → '{substitution}' must use R=301, "
                f"flags: [{flags}]"
            )

    # --- Verify .htaccess file exists and has redirect rules ---

    def test_htaccess_has_redirect_rules(self):
        """
        **Validates: Requirements 12.2**

        The .htaccess file must exist and contain redirect rules.
        """
        assert os.path.exists(HTACCESS_PATH), (
            f".htaccess not found at {HTACCESS_PATH}"
        )
        assert len(self.direct_rules) > 0, (
            ".htaccess must contain at least one direct redirect rule"
        )
        assert len(self.fallback_rules) > 0, (
            ".htaccess must contain at least one fallback redirect rule"
        )
