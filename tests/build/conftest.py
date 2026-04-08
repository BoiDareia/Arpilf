"""
Fixtures and helpers for Hugo build property-based tests.

Provides:
- hugo_public_dir: fixture that runs Hugo build and returns the path to public/
- Helper functions for parsing HTML with BeautifulSoup
"""

import os
import subprocess
import shutil
import glob
import datetime

import pytest
from bs4 import BeautifulSoup


HUGO_SITE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONTENT_NOTICIAS_DIR = os.path.join(HUGO_SITE_DIR, "content", "noticias")
PUBLIC_DIR = os.path.join(HUGO_SITE_DIR, "public")

# Hugo does not publish pages with future dates by default.
# Use today as the upper bound for date generation.
TODAY = datetime.date.today()


def run_hugo_build():
    """Run Hugo build and return the path to public/."""
    result = subprocess.run(
        ["hugo", "--gc", "--cleanDestinationDir"],
        cwd=HUGO_SITE_DIR,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Hugo build failed:\n{result.stderr}")
    return PUBLIC_DIR


def parse_html(filepath):
    """Parse an HTML file and return a BeautifulSoup object."""
    with open(filepath, "r", encoding="utf-8") as f:
        return BeautifulSoup(f.read(), "lxml")


def create_news_markdown(slug, title, date_str, description, body, image=None, draft=False):
    """Create a news Markdown file in content/noticias/ and return its path."""
    frontmatter_lines = [
        "---",
        f'title: "{title}"',
        f"date: {date_str}",
        f'description: "{description}"',
    ]
    if image:
        frontmatter_lines.append(f'image: "{image}"')
    frontmatter_lines.append(f"draft: {'true' if draft else 'false'}")
    frontmatter_lines.append("---")
    frontmatter_lines.append("")
    frontmatter_lines.append(body)
    frontmatter_lines.append("")

    content = "\n".join(frontmatter_lines)
    filepath = os.path.join(CONTENT_NOTICIAS_DIR, f"{slug}.md")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def remove_news_file(filepath):
    """Remove a news Markdown file."""
    if os.path.exists(filepath):
        os.remove(filepath)


def get_news_article_page(public_dir, slug):
    """Get the path to a generated news article HTML page."""
    return os.path.join(public_dir, "noticias", slug, "index.html")


def get_news_listing_page(public_dir):
    """Get the path to the news listing page."""
    return os.path.join(public_dir, "noticias", "index.html")


def get_homepage(public_dir):
    """Get the path to the homepage."""
    return os.path.join(public_dir, "index.html")


def extract_article_titles_from_listing(soup):
    """Extract article titles in order from the news listing page.

    The listing page uses news-card.html partial which renders each article
    inside an <article> tag with an <h3> containing the title link.
    """
    articles = soup.select("article h3 a")
    return [a.get_text(strip=True) for a in articles]


def extract_article_dates_from_listing(soup):
    """Extract article dates in order from the news listing page.

    Each article card has a <time datetime="YYYY-MM-DD"> element.
    """
    times = soup.select("article time")
    return [t.get("datetime", "") for t in times]


def extract_homepage_news_titles(soup):
    """Extract news article titles from the homepage 'Últimas Notícias' section.

    The homepage renders news articles as <article> elements inside the
    news section, each with an <h3> containing the title link.
    """
    # The news section is identified by the heading "Últimas Notícias"
    news_section = None
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Notícias" in h2.get_text():
            news_section = section
            break

    if news_section is None:
        return []

    articles = news_section.select("article h3 a")
    return [a.get_text(strip=True) for a in articles]


def extract_homepage_news_dates(soup):
    """Extract news article dates from the homepage news section."""
    news_section = None
    for section in soup.find_all("section"):
        h2 = section.find("h2")
        if h2 and "Notícias" in h2.get_text():
            news_section = section
            break

    if news_section is None:
        return []

    times = news_section.select("article time")
    return [t.get("datetime", "") for t in times]
