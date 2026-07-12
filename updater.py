"""
updater.py

Checks GitHub for a newer released version of Voise.

Privacy contract: this is the ONLY place Voise ever touches the
network beyond this Mac, it requests release metadata and nothing
more, it runs only if the user leaves the toggle on in Settings (or
clicks "Check for updates"), and it sends no data about the user -
audio and text never leave the device.
"""

import re

import requests

from config import APP_VERSION, GITHUB_REPO


def _version_tuple(text: str):
    """'v0.4.1' -> (0, 4, 1) so versions compare sensibly."""
    return tuple(int(n) for n in re.findall(r"\d+", text)[:3])


def check_for_update() -> str:
    """Returns 'version|download-url' if a newer release exists,
    '' otherwise. Designed to run in a background thread."""
    if "CHANGE_ME" in GITHUB_REPO:
        return ""
    response = requests.get(
        f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
        timeout=6,
    )
    response.raise_for_status()
    data = response.json()
    tag = data.get("tag_name", "")
    url = data.get("html_url", "")
    if tag and _version_tuple(tag) > _version_tuple(APP_VERSION):
        return f"{tag}|{url}"
    return ""
