"""
Property-based tests for Hugo build output.

Feature: arpilf-website-rebuild

Tests:
  - P1: Consistência da navegação em todas as páginas
  - P2: Geração de artigos de notícias a partir de Markdown
  - P3: Ordenação cronológica inversa das notícias
  - P4: Limite de notícias na homepage
  - P5: Renderização do catálogo de documentos com links de download
  - P10: Completude de metadados em todas as páginas
"""

import os
import sys
import re
import glob

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st
from bs4 import BeautifulSoup

# Ensure the conftest helpers are importable
sys.path.insert(0, os.path.dirname(__file__))

from conftest import (
    HUGO_SITE_DIR,
    CONTENT_NOTICIAS_DIR,
    PUBLIC_DIR,
    run_hugo_build,
    parse_html,
    create_news_markdown,
    remove_news_file,
    get_news_article_page,
    get_news_listing_page,
    get_homepage,
    extract_article_titles_from_listing,
    extract_article_dates_from_listing,
    extract_homepage_news_titles,
    extract_homepage_news_dates,
)


# ---------------------------------------------------------------------------
# Hypothesis strategies for generating valid news content
# ---------------------------------------------------------------------------

def slug_strategy():
    """Generate valid Hugo slugs: lowercase ASCII letters and hyphens."""
    return st.from_regex(r"[a-z]{3,8}(-[a-z]{3,8}){1,3}", fullmatch=True)


def title_strategy():
    """Generate non-empty titles with printable characters safe for YAML."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "Zs"),
            whitelist_characters="-",
        ),
        min_size=3,
        max_size=60,
    ).map(str.strip).filter(lambda t: len(t) >= 3)


def date_strategy():
    """Generate dates between 2020-01-01 and today (Hugo skips future dates)."""
    from conftest import TODAY
    return st.dates(
        min_value=__import__("datetime").date(2020, 1, 1),
        max_value=TODAY,
    )


def description_strategy():
    """Generate non-empty descriptions safe for YAML frontmatter."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "Zs"),
            whitelist_characters=".,!?-",
        ),
        min_size=5,
        max_size=120,
    ).map(str.strip).filter(lambda d: len(d) >= 5)


def body_strategy():
    """Generate non-empty Markdown body text with safe characters."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N", "Zs"),
        ),
        min_size=10,
        max_size=300,
    ).map(str.strip).filter(lambda b: len(b) >= 10 and any(c.isalpha() for c in b))


def image_strategy():
    """Optionally generate an image path."""
    return st.one_of(
        st.none(),
        st.just("/images/noticias/test-image.jpg"),
    )


# ---------------------------------------------------------------------------
# Helper: clean up all test-generated news files
# ---------------------------------------------------------------------------

TEST_FILE_PREFIX = "test-pbt-"


def cleanup_test_news_files():
    """Remove all test-generated news Markdown files."""
    pattern = os.path.join(CONTENT_NOTICIAS_DIR, f"{TEST_FILE_PREFIX}*.md")
    for f in glob.glob(pattern):
        os.remove(f)


# ---------------------------------------------------------------------------
# Property 2: Geração de artigos de notícias a partir de Markdown
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 2: Para qualquer ficheiro Markdown
# válido na pasta content/noticias/ com frontmatter contendo title, date,
# description e corpo não vazio, o Hugo deve gerar uma página HTML que contenha
# o título, a data formatada, o corpo do artigo e, se especificada, a imagem.
#
# Validates: Requirements 3.2


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    title=title_strategy(),
    date=date_strategy(),
    description=description_strategy(),
    body=body_strategy(),
    image=image_strategy(),
    slug_suffix=st.integers(min_value=1000, max_value=9999),
)
def test_property_2_news_article_generation(title, date, description, body, image, slug_suffix):
    """
    **Validates: Requirements 3.2**

    Property 2: For any valid Markdown file in content/noticias/ with
    frontmatter containing title, date, description and non-empty body,
    Hugo must generate an HTML page containing the title, formatted date,
    article body, and if specified, the image.
    """
    slug = f"{TEST_FILE_PREFIX}{slug_suffix}"
    date_str = date.isoformat()
    created_file = None

    try:
        created_file = create_news_markdown(
            slug=slug,
            title=title,
            date_str=date_str,
            description=description,
            body=body,
            image=image,
        )

        public_dir = run_hugo_build()
        article_path = get_news_article_page(public_dir, slug)

        assert os.path.exists(article_path), (
            f"Hugo did not generate page for slug '{slug}'"
        )

        soup = parse_html(article_path)

        # Title must appear in an <h1>
        h1 = soup.find("h1")
        assert h1 is not None, "Article page must have an <h1>"
        assert title in h1.get_text(), (
            f"Title '{title}' not found in <h1>: '{h1.get_text()}'"
        )

        # Date must appear in a <time> element with correct datetime attribute
        time_el = soup.find("time")
        assert time_el is not None, "Article page must have a <time> element"
        assert time_el.get("datetime") == date_str, (
            f"Expected datetime='{date_str}', got '{time_el.get('datetime')}'"
        )

        # Body content must appear in the prose div
        prose_div = soup.select_one("div.prose")
        assert prose_div is not None, "Article page must have a div.prose"
        # Check that at least one significant alphabetic word from the body appears
        body_words = [w for w in body.split() if len(w) > 3 and w.isalpha()]
        if body_words:
            prose_text = prose_div.get_text()
            assert any(word in prose_text for word in body_words[:5]), (
                f"Body content not found in article prose section"
            )

        # If image was specified, it must appear as an <img> in a <figure>
        if image:
            figure = soup.find("figure")
            assert figure is not None, "Article with image must have a <figure>"
            img = figure.find("img")
            assert img is not None, "Figure must contain an <img>"
            assert img.get("src") == image, (
                f"Expected img src='{image}', got '{img.get('src')}'"
            )

    finally:
        if created_file:
            remove_news_file(created_file)


# ---------------------------------------------------------------------------
# Property 3: Ordenação cronológica inversa das notícias
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 3: Para qualquer conjunto de
# artigos de notícias com datas distintas, a página de listagem de notícias
# deve apresentá-los ordenados da data mais recente para a mais antiga.
#
# Validates: Requirements 3.3


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    dates=st.lists(
        date_strategy(),
        min_size=2,
        max_size=8,
        unique=True,
    ),
)
def test_property_3_reverse_chronological_order(dates):
    """
    **Validates: Requirements 3.3**

    Property 3: For any set of news articles with distinct dates, the news
    listing page must present them ordered from most recent to oldest.
    """
    created_files = []

    try:
        for i, d in enumerate(dates):
            slug = f"{TEST_FILE_PREFIX}order-{i}"
            created_files.append(
                create_news_markdown(
                    slug=slug,
                    title=f"Noticia Ordem {i}",
                    date_str=d.isoformat(),
                    description=f"Descricao da noticia {i}",
                    body=f"Corpo da noticia de teste numero {i} para verificar ordenacao.",
                )
            )

        public_dir = run_hugo_build()
        listing_path = get_news_listing_page(public_dir)
        assert os.path.exists(listing_path), "News listing page must exist"

        soup = parse_html(listing_path)
        displayed_dates = extract_article_dates_from_listing(soup)

        # Filter to only our test articles' dates
        test_date_strs = sorted(
            [d.isoformat() for d in dates], reverse=True
        )
        # The displayed dates should contain all our test dates
        # and they should appear in reverse chronological order
        displayed_test_dates = [
            d for d in displayed_dates if d in test_date_strs
        ]

        assert len(displayed_test_dates) == len(dates), (
            f"Expected {len(dates)} test articles in listing, "
            f"found {len(displayed_test_dates)}"
        )

        # Verify reverse chronological order
        for j in range(len(displayed_test_dates) - 1):
            assert displayed_test_dates[j] >= displayed_test_dates[j + 1], (
                f"Articles not in reverse chronological order: "
                f"{displayed_test_dates[j]} should be >= {displayed_test_dates[j + 1]}"
            )

    finally:
        for f in created_files:
            remove_news_file(f)


# ---------------------------------------------------------------------------
# Property 4: Limite de notícias na homepage
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 4: Para qualquer número de artigos
# de notícias publicados (0, 1, 2, 3 ou mais), a homepage deve apresentar no
# máximo 3 artigos, e esses devem ser os mais recentes.
#
# Validates: Requirements 3.4


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    num_articles=st.integers(min_value=0, max_value=8),
)
def test_property_4_homepage_news_limit(num_articles):
    """
    **Validates: Requirements 3.4**

    Property 4: For any number of published news articles (0, 1, 2, 3 or more),
    the homepage must show at most 3 articles, and those must be the most recent.
    """
    created_files = []
    # Remove existing non-index news files to control the exact count
    existing_news = glob.glob(os.path.join(CONTENT_NOTICIAS_DIR, "*.md"))
    backed_up = {}
    for f in existing_news:
        if os.path.basename(f) != "_index.md":
            with open(f, "r", encoding="utf-8") as fh:
                backed_up[f] = fh.read()
            os.remove(f)

    try:
        import datetime

        base_date = datetime.date(2025, 1, 1)
        for i in range(num_articles):
            d = base_date + datetime.timedelta(days=i * 30)
            slug = f"{TEST_FILE_PREFIX}home-{i}"
            created_files.append(
                create_news_markdown(
                    slug=slug,
                    title=f"Homepage Noticia {i}",
                    date_str=d.isoformat(),
                    description=f"Descricao homepage noticia {i}",
                    body=f"Corpo da noticia homepage teste numero {i} para verificar limite.",
                )
            )

        public_dir = run_hugo_build()
        homepage_path = get_homepage(public_dir)
        assert os.path.exists(homepage_path), "Homepage must exist"

        soup = parse_html(homepage_path)
        homepage_titles = extract_homepage_news_titles(soup)
        homepage_dates = extract_homepage_news_dates(soup)

        expected_count = min(num_articles, 3)
        assert len(homepage_titles) == expected_count, (
            f"Homepage should show {expected_count} articles "
            f"(from {num_articles} total), but shows {len(homepage_titles)}"
        )

        if num_articles > 0:
            # The displayed articles must be the most recent ones
            all_dates = sorted(
                [(base_date + datetime.timedelta(days=i * 30)).isoformat()
                 for i in range(num_articles)],
                reverse=True,
            )
            expected_dates = all_dates[:3]

            assert len(homepage_dates) == expected_count
            for hd in homepage_dates:
                assert hd in expected_dates, (
                    f"Homepage date '{hd}' is not among the "
                    f"{expected_count} most recent: {expected_dates}"
                )

            # Verify they are in reverse chronological order
            for j in range(len(homepage_dates) - 1):
                assert homepage_dates[j] >= homepage_dates[j + 1], (
                    f"Homepage articles not in reverse chronological order: "
                    f"{homepage_dates[j]} should be >= {homepage_dates[j + 1]}"
                )

    finally:
        for f in created_files:
            remove_news_file(f)
        # Restore backed-up files
        for path, content in backed_up.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)


# ---------------------------------------------------------------------------
# Property 5: Renderização do catálogo de documentos com links de download
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 5: Para qualquer entrada de
# documento no ficheiro data/documentos.yaml com título, ficheiro, data e
# categoria, a página de Documentos gerada deve apresentar esse documento
# agrupado na categoria correta, com o nome, data e um link de download
# direto para o ficheiro PDF.
#
# Validates: Requirements 4.2, 4.3, 4.4

import yaml


def load_documentos_yaml():
    """Load and return the documentos.yaml data file."""
    yaml_path = os.path.join(HUGO_SITE_DIR, "data", "documentos.yaml")
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_documentos_page(public_dir):
    """Get the path to the generated documentos page."""
    return os.path.join(public_dir, "documentos", "index.html")


def document_entry_strategy():
    """Strategy that samples a single (category, document) pair from documentos.yaml.

    Reads the real YAML data and picks one document entry at random,
    returning a dict with categoria_nome, categoria_slug, titulo, ficheiro, data.
    """
    data = load_documentos_yaml()
    entries = []
    for cat in data.get("categorias", []):
        for doc in cat.get("documentos", []):
            entries.append({
                "categoria_nome": cat["nome"],
                "categoria_slug": cat["slug"],
                "titulo": doc["titulo"],
                "ficheiro": doc["ficheiro"],
                "data": doc["data"],
            })
    if not entries:
        pytest.skip("No document entries found in documentos.yaml")
    return st.sampled_from(entries)


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(
    entry=document_entry_strategy(),
)
def test_property_5_document_catalog_rendering(entry):
    """
    **Validates: Requirements 4.2, 4.3, 4.4**

    Property 5: For any document entry in data/documentos.yaml with title,
    file, date and category, the generated Documents page must display that
    document grouped under the correct category, with the name, date and a
    direct download link to the PDF file.
    """
    public_dir = run_hugo_build()
    documentos_path = get_documentos_page(public_dir)

    assert os.path.exists(documentos_path), "Documents page must exist"

    soup = parse_html(documentos_path)

    # Find the category section by its slug id
    cat_div = soup.find("div", id=entry["categoria_slug"])
    assert cat_div is not None, (
        f"Category section with id='{entry['categoria_slug']}' not found on documents page"
    )

    # Verify the category heading contains the category name
    cat_h2 = cat_div.find("h2")
    assert cat_h2 is not None, (
        f"Category '{entry['categoria_slug']}' must have an <h2> heading"
    )
    assert entry["categoria_nome"] in cat_h2.get_text(), (
        f"Category heading must contain '{entry['categoria_nome']}', "
        f"got '{cat_h2.get_text(strip=True)}'"
    )

    # Verify the document title appears within this category section
    title_spans = cat_div.find_all("span", class_="text-lg")
    found_titles = [s.get_text(strip=True) for s in title_spans]
    assert entry["titulo"] in found_titles, (
        f"Document title '{entry['titulo']}' not found in category "
        f"'{entry['categoria_nome']}'. Found: {found_titles}"
    )

    # Find the specific <li> containing this document
    doc_li = None
    for li in cat_div.find_all("li"):
        span = li.find("span", class_="text-lg")
        if span and span.get_text(strip=True) == entry["titulo"]:
            doc_li = li
            break

    assert doc_li is not None, (
        f"Could not find <li> for document '{entry['titulo']}'"
    )

    # Verify the date is displayed in a <time> element
    date_str = str(entry["data"])
    time_el = doc_li.find("time")
    assert time_el is not None, (
        f"Document '{entry['titulo']}' must have a <time> element"
    )
    assert time_el.get("datetime") == date_str, (
        f"Expected datetime='{date_str}', got '{time_el.get('datetime')}'"
    )

    # Verify the download link points to the correct PDF file
    download_link = doc_li.find("a", attrs={"download": True})
    assert download_link is not None, (
        f"Document '{entry['titulo']}' must have a download link (a[download])"
    )
    assert download_link.get("href") == entry["ficheiro"], (
        f"Download link href must be '{entry['ficheiro']}', "
        f"got '{download_link.get('href')}'"
    )


# ---------------------------------------------------------------------------
# Helpers for P1 and P10: collect all HTML pages from Hugo build output
# ---------------------------------------------------------------------------

# The 7 main menu pages defined in hugo.toml
EXPECTED_MENU_ITEMS = [
    {"name": "Início", "url": "/"},
    {"name": "Sobre Nós", "url": "/sobre/"},
    {"name": "Serviços", "url": "/servicos/"},
    {"name": "Notícias", "url": "/noticias/"},
    {"name": "Documentos", "url": "/documentos/"},
    {"name": "Contactos", "url": "/contactos/"},
    {"name": "Donativos", "url": "/donativos/"},
]


def collect_html_pages():
    """Build Hugo and collect all generated HTML page paths from public/.

    Returns a list of absolute paths to .html files in the public/ directory.
    Excludes XML feeds and non-page files.
    """
    public_dir = run_hugo_build()
    html_files = []
    for root, _dirs, files in os.walk(public_dir):
        for fname in files:
            if fname.endswith(".html"):
                html_files.append(os.path.join(root, fname))
    if not html_files:
        pytest.skip("No HTML files found in Hugo build output")
    return html_files


def html_page_strategy():
    """Strategy that samples a random HTML page from the Hugo build output."""
    pages = collect_html_pages()
    return st.sampled_from(pages)


# ---------------------------------------------------------------------------
# Property 1: Consistência da navegação em todas as páginas
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 1: Para qualquer página HTML
# gerada pelo Hugo, o output deve conter um elemento <nav> com links para
# todas as páginas do menu principal (Início, Sobre Nós, Serviços, Notícias,
# Documentos, Contactos, Donativos) e um <footer> com informações de contacto
# da ARPILF.
#
# Validates: Requirements 1.5, 7.4


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(page_path=html_page_strategy())
def test_property_1_navigation_consistency(page_path):
    """
    **Validates: Requirements 1.5, 7.4**

    Property 1: For any HTML page generated by Hugo, the output must contain
    a nav element with links to all 7 main menu pages and a footer with
    ARPILF contact info.
    """
    soup = parse_html(page_path)
    rel_path = os.path.relpath(page_path, PUBLIC_DIR)

    # --- Nav element must exist ---
    nav = soup.find("nav")
    assert nav is not None, (
        f"Page '{rel_path}' must contain a <nav> element"
    )

    # --- Nav must contain links to all 7 main menu pages ---
    nav_links = nav.find_all("a")
    nav_hrefs = [a.get("href", "") for a in nav_links]
    nav_texts = [a.get_text(strip=True) for a in nav_links]

    for menu_item in EXPECTED_MENU_ITEMS:
        # Check that the URL appears in at least one nav link
        assert any(menu_item["url"] == href or href.endswith(menu_item["url"]) for href in nav_hrefs), (
            f"Page '{rel_path}': nav missing link to '{menu_item['url']}' "
            f"({menu_item['name']}). Found hrefs: {nav_hrefs}"
        )
        # Check that the menu item name appears in at least one nav link text
        assert any(menu_item["name"] in text for text in nav_texts), (
            f"Page '{rel_path}': nav missing text '{menu_item['name']}'. "
            f"Found texts: {nav_texts}"
        )

    # --- Footer must exist ---
    footer = soup.find("footer")
    assert footer is not None, (
        f"Page '{rel_path}' must contain a <footer> element"
    )

    # --- Footer must contain ARPILF contact info ---
    footer_text = footer.get_text()

    # Footer must mention ARPILF
    assert "ARPILF" in footer_text, (
        f"Page '{rel_path}': footer must mention 'ARPILF'"
    )

    # Footer must contain a telephone link (tel:)
    tel_link = footer.find("a", href=lambda h: h and h.startswith("tel:"))
    assert tel_link is not None, (
        f"Page '{rel_path}': footer must contain a telephone link (tel:)"
    )

    # Footer must contain an email link (mailto:)
    email_link = footer.find("a", href=lambda h: h and h.startswith("mailto:"))
    assert email_link is not None, (
        f"Page '{rel_path}': footer must contain an email link (mailto:)"
    )

    # Footer must contain address info (Morada section)
    assert "Morada" in footer_text or "morada" in footer_text.lower(), (
        f"Page '{rel_path}': footer must contain address information (Morada)"
    )


# ---------------------------------------------------------------------------
# Property 10: Completude de metadados em todas as páginas
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 10: Para qualquer página HTML
# gerada pelo Hugo, o output deve conter: um <title> não vazio, uma meta tag
# description, meta tags Open Graph (og:title, og:description, og:url),
# hierarquia correta de headings (exatamente um <h1>), e todas as <img>
# devem ter atributo alt não vazio.
#
# Validates: Requirements 8.1, 8.5


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(page_path=html_page_strategy())
def test_property_10_metadata_completeness(page_path):
    """
    **Validates: Requirements 8.1, 8.5**

    Property 10: For any HTML page generated by Hugo, the output must contain:
    a non-empty title, a meta description, Open Graph tags (og:title,
    og:description, og:url), correct heading hierarchy (exactly one h1),
    and all img elements must have non-empty alt attributes.
    """
    soup = parse_html(page_path)
    rel_path = os.path.relpath(page_path, PUBLIC_DIR)

    # --- Non-empty <title> ---
    title_el = soup.find("title")
    assert title_el is not None, (
        f"Page '{rel_path}' must have a <title> element"
    )
    title_text = title_el.get_text(strip=True)
    assert len(title_text) > 0, (
        f"Page '{rel_path}': <title> must not be empty"
    )

    # --- Meta description ---
    meta_desc = soup.find("meta", attrs={"name": "description"})
    assert meta_desc is not None, (
        f"Page '{rel_path}' must have a <meta name='description'> tag"
    )
    desc_content = meta_desc.get("content", "")
    assert len(desc_content.strip()) > 0, (
        f"Page '{rel_path}': meta description content must not be empty"
    )

    # --- Open Graph tags ---
    og_title = soup.find("meta", attrs={"property": "og:title"})
    assert og_title is not None, (
        f"Page '{rel_path}' must have an og:title meta tag"
    )
    assert len(og_title.get("content", "").strip()) > 0, (
        f"Page '{rel_path}': og:title content must not be empty"
    )

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    assert og_desc is not None, (
        f"Page '{rel_path}' must have an og:description meta tag"
    )
    assert len(og_desc.get("content", "").strip()) > 0, (
        f"Page '{rel_path}': og:description content must not be empty"
    )

    og_url = soup.find("meta", attrs={"property": "og:url"})
    assert og_url is not None, (
        f"Page '{rel_path}' must have an og:url meta tag"
    )
    assert len(og_url.get("content", "").strip()) > 0, (
        f"Page '{rel_path}': og:url content must not be empty"
    )

    # --- Exactly one <h1> ---
    h1_elements = soup.find_all("h1")
    assert len(h1_elements) == 1, (
        f"Page '{rel_path}' must have exactly one <h1>, "
        f"found {len(h1_elements)}: "
        f"{[h.get_text(strip=True) for h in h1_elements]}"
    )

    # --- All <img> must have non-empty alt ---
    images = soup.find_all("img")
    for img in images:
        alt = img.get("alt", "")
        assert len(alt.strip()) > 0, (
            f"Page '{rel_path}': <img src='{img.get('src', '')}' > "
            f"must have a non-empty alt attribute"
        )


# ---------------------------------------------------------------------------
# Helpers for P11: sitemap.xml parsing
# ---------------------------------------------------------------------------

import xml.etree.ElementTree as ET
from urllib.parse import urlparse, unquote


SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def parse_sitemap_locs(public_dir):
    """Parse sitemap.xml and return the set of <loc> URLs."""
    sitemap_path = os.path.join(public_dir, "sitemap.xml")
    assert os.path.exists(sitemap_path), "sitemap.xml must exist in public/"
    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    locs = set()
    for url_el in root.findall("sm:url", SITEMAP_NS):
        loc_el = url_el.find("sm:loc", SITEMAP_NS)
        if loc_el is not None and loc_el.text:
            locs.add(loc_el.text.strip())
    return locs


def collect_public_page_urls(public_dir, base_url):
    """Collect expected URLs for all public HTML pages (excluding 404).

    Walks the public/ directory, finds index.html files, and converts
    their paths to absolute URLs using the baseURL from hugo.toml.
    """
    urls = set()
    for root_dir, _dirs, files in os.walk(public_dir):
        for fname in files:
            if fname != "index.html":
                continue
            full_path = os.path.join(root_dir, fname)
            # Convert filesystem path to URL path
            rel = os.path.relpath(full_path, public_dir)
            # rel is like "contactos/index.html" or "index.html"
            rel = rel.replace(os.sep, "/")
            # Remove trailing index.html to get the directory URL
            if rel == "index.html":
                url_path = "/"
            else:
                url_path = "/" + rel.replace("/index.html", "/")
            url = base_url.rstrip("/") + url_path
            urls.add(url)
    return urls


# ---------------------------------------------------------------------------
# Property 11: Completude do sitemap.xml
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 11: Para qualquer build do Hugo,
# o ficheiro sitemap.xml gerado deve conter uma entrada <url> para cada
# página pública do site (excluindo drafts), e cada entrada deve ter um
# <loc> com URL absoluto válido.
#
# Validates: Requirements 8.2


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(page_path=html_page_strategy())
def test_property_11_sitemap_completeness(page_path):
    """
    **Validates: Requirements 8.2**

    Property 11: For any Hugo build, the sitemap.xml must contain a URL
    entry for each public page (excluding drafts), and each entry must
    have a loc with a valid absolute URL.
    """
    public_dir = run_hugo_build()
    rel_path = os.path.relpath(page_path, PUBLIC_DIR)

    # Skip 404.html — it is not a public page in the sitemap sense
    if "404.html" in rel_path:
        assume(False)

    # Derive the expected URL for this page
    base_url = "https://arpilf.pt"
    rel_unix = rel_path.replace(os.sep, "/")
    if rel_unix == "index.html":
        expected_url = base_url + "/"
    elif rel_unix.endswith("/index.html"):
        url_path = "/" + rel_unix.replace("/index.html", "/")
        expected_url = base_url + url_path
    else:
        # Non-index HTML files (like 404.html) are skipped above
        assume(False)
        return

    # Parse sitemap and verify this page is listed
    sitemap_locs = parse_sitemap_locs(public_dir)

    assert expected_url in sitemap_locs, (
        f"Page '{rel_path}' (URL: {expected_url}) not found in sitemap.xml. "
        f"Sitemap contains {len(sitemap_locs)} entries."
    )

    # Verify the loc is a valid absolute URL
    parsed = urlparse(expected_url)
    assert parsed.scheme in ("http", "https"), (
        f"Sitemap loc '{expected_url}' must use http or https scheme"
    )
    assert parsed.netloc, (
        f"Sitemap loc '{expected_url}' must have a valid hostname"
    )


# ---------------------------------------------------------------------------
# Property 12: URLs amigáveis em português
# ---------------------------------------------------------------------------
# Feature: arpilf-website-rebuild, Property 12: Para qualquer página gerada
# pelo Hugo, o URL deve ser composto exclusivamente por caracteres minúsculos,
# hífens e barras (sem espaços, underscores, caracteres especiais ou extensões
# .html), e deve utilizar slugs em português.
#
# Validates: Requirements 8.4

# Pattern: only lowercase a-z, digits 0-9, hyphens, and slashes allowed
FRIENDLY_URL_PATTERN = re.compile(r"^[a-z0-9/\-]*$")


@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(page_path=html_page_strategy())
def test_property_12_friendly_portuguese_urls(page_path):
    """
    **Validates: Requirements 8.4**

    Property 12: For any page generated by Hugo, the URL must be composed
    exclusively of lowercase characters, hyphens and slashes (no spaces,
    underscores, special characters or .html extensions), and must use
    Portuguese slugs.
    """
    rel_path = os.path.relpath(page_path, PUBLIC_DIR)

    # Skip 404.html — it's a special page, not a navigable URL
    if "404.html" in rel_path:
        assume(False)

    # Convert filesystem path to URL path
    rel_unix = rel_path.replace(os.sep, "/")
    if rel_unix == "index.html":
        url_path = "/"
    elif rel_unix.endswith("/index.html"):
        url_path = "/" + rel_unix.replace("/index.html", "/")
    else:
        assume(False)
        return

    # URL-decode the path for checking (Hugo may percent-encode accented chars)
    decoded_path = unquote(url_path)

    # Must not contain .html extension
    assert ".html" not in decoded_path, (
        f"URL '{decoded_path}' must not contain .html extension"
    )

    # Must not contain spaces
    assert " " not in decoded_path, (
        f"URL '{decoded_path}' must not contain spaces"
    )

    # Must not contain underscores
    assert "_" not in decoded_path, (
        f"URL '{decoded_path}' must not contain underscores"
    )

    # Must be composed of lowercase chars, digits, hyphens, and slashes only
    assert FRIENDLY_URL_PATTERN.match(decoded_path), (
        f"URL '{decoded_path}' contains invalid characters. "
        f"Only lowercase a-z, digits 0-9, hyphens and slashes are allowed."
    )

    # Must not contain consecutive slashes
    assert "//" not in decoded_path, (
        f"URL '{decoded_path}' must not contain consecutive slashes"
    )
