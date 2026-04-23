from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings
from app.utils.filenames import filename_from_url


class GuardrailViolation(ValueError):
    pass


@dataclass
class HtmlDocument:
    url: str
    html: str
    title: str | None


def validate_outbound_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise GuardrailViolation(f"Unsupported URL scheme: {parsed.scheme}")
    hostname = parsed.hostname or ""
    lowered = hostname.lower()
    if lowered in settings.suspicious_domain_set:
        raise GuardrailViolation(f"Blocked hostname: {hostname}")
    try:
        for info in socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM):
            address = info[4][0]
            ip = ipaddress.ip_address(address)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                raise GuardrailViolation(f"Blocked private address for host: {hostname}")
    except socket.gaierror:
        return


class PageFetcher:
    def fetch_html(self, url: str) -> HtmlDocument:
        validate_outbound_url(url)
        with httpx.Client(timeout=settings.request_timeout_seconds, follow_redirects=True, max_redirects=settings.redirect_limit) as client:
            response = client.get(url, headers={"User-Agent": "agentic-material-search-v2"})
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "text/html" not in content_type:
                raise GuardrailViolation(f"Expected HTML but got {content_type}")
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.string.strip() if soup.title and soup.title.string else None
            return HtmlDocument(url=str(response.url), html=response.text, title=title)

    def extract_document_links(self, document: HtmlDocument) -> list[dict[str, str]]:
        soup = BeautifulSoup(document.html, "lxml")
        links: list[dict[str, str]] = []
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "").strip()
            if not href:
                continue
            target = urljoin(document.url, href)
            label = " ".join(anchor.stripped_strings) or filename_from_url(target)
            links.append({"url": target, "label": label})
        return links

