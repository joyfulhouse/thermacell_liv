"""Published guidance must preserve the boundary between LAN and cloud."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", ["README.md", "docs/CONFIGURATION.md", "docs/NATIVE_CONTROLS.md"])
def test_operation_boundaries_are_explicit(path):
    text = (ROOT / path).read_text().lower()
    assert "no local api" not in text
    assert "offline restart" in text and "unsupported" in text
    assert "cloud-only" in text
    assert "physical-hub" in text and "outstanding" in text


@pytest.mark.parametrize(
    "path",
    [
        "docs/ARCHITECTURE.md",
        "docs/ENTITIES.md",
        "docs/DEVELOPMENT.md",
        "docs/QUALITY_SCALE.md",
        "docs/TROUBLESHOOTING.md",
    ],
)
def test_lan_is_not_omitted_from_transport_guidance(path):
    text = (ROOT / path).read_text().lower()
    assert "no local or push channel" not in text
    assert any(term in text for term in ("local-control", "rainmaker lan", "mdns"))


def test_troubleshooting_distinguishes_discovery_from_success():
    text = (ROOT / "docs/TROUBLESHOOTING.md").read_text().lower()
    assert all(term in text for term in ("vlan", "ipv6", "capability", "fallback", "handshake", "pop"))
    assert "not proof" in text
