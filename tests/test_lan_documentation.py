"""Published guidance must preserve the boundary between LAN and cloud."""

from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("path", ["README.md", "docs/CONFIGURATION.md", "docs/NATIVE_CONTROLS.md"])
def test_operation_boundaries_are_explicit(path):
    text = (ROOT / path).read_text().lower()
    assert "no local api" not in text
    assert "offline restart" in text and "unsupported" in text
    assert "cloud-only" in text
    if path == "docs/CONFIGURATION.md":
        assert "physical-hub" in text and "outstanding" in text
    else:
        assert "#live-hub-status" in text
        if path == "docs/NATIVE_CONTROLS.md":
            assert "### live hub status" in text
            assert "unverified on physical hubs" in " ".join(text.split())


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


@pytest.mark.parametrize("path", ["docs/NATIVE_CONTROLS.md", "docs/TROUBLESHOOTING.md"])
def test_diagnostic_availability_matches_pinned_library(path):
    text = " ".join((ROOT / path).read_text().lower().split())
    assert "pythermacell pr #73 / the next pythermacell release" in text
    assert "0.3.0b3" in text
    assert "not included" in text or "not in" in text


def test_live_evidence_does_not_assume_hub_vlan():
    text = " ".join((ROOT / "docs/NATIVE_CONTROLS.md").read_text().lower().split())
    assert "homelab host (server0)" in text
    assert "hub vlan co-location was not independently established" in text
    assert "no local handshake, local read, or local led write was performed" in text


def test_secret_exposure_response_distinguishes_cloud_and_local_credentials():
    text = " ".join((ROOT / "docs/TROUBLESHOOTING.md").read_text().lower().split())
    assert "if you shared a secret" in text and "remove the upload" in text
    assert "change the thermacell cloud password and reauthenticate" in text
    assert "remaining lifetime" in text
    assert "vendor-provisioned and not user-rotatable" in text
    assert "does **not** rotate pop" in text
    assert "disable local preference" in text and "network segment as exposed" in text
    assert "vendor reprovisions" in text and "no automated leak detection" in text


def test_live_status_checks_allow_new_observation_dates(monkeypatch):
    original = Path.read_text

    def updated_observations(path, *args, **kwargs):
        return re.sub(r"\d{4}-\d{2}-\d{2}", "2099-12-31", original(path, *args, **kwargs))

    monkeypatch.setattr(Path, "read_text", updated_observations)
    for path in ("README.md", "docs/CONFIGURATION.md", "docs/NATIVE_CONTROLS.md"):
        test_operation_boundaries_are_explicit(path)


def test_unreleased_records_lan_and_privacy_changes():
    text = (ROOT / "CHANGELOG.md").read_text().lower().split("## [unreleased]", 1)[1].split("\n## [", 1)[0]
    assert all(term in text for term in ("unknown", "diagnostics", "anonymous", "reads", "writes", "announcements"))


def test_live_status_anchor_links_resolve():
    target = ROOT / "docs/NATIVE_CONTROLS.md"
    assert re.search(r"^### Live hub status$", target.read_text(), re.MULTILINE)
    links = []
    for source in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md")]:
        for link in re.findall(r"\]\(([^)\s]*#live-hub-status[^)\s]*)\)", source.read_text()):
            path, anchor = link.rsplit("#", 1)
            destination = source.parent / path if path else source
            assert destination.resolve() == target
            assert anchor == "live-hub-status", (source, link)
            links.append((source, link))
    assert links


def test_live_status_anchor_scan_does_not_require_git(tmp_path, monkeypatch):
    monkeypatch.setattr(f"{__name__}.ROOT", tmp_path)
    (tmp_path / "docs/nested").mkdir(parents=True)
    (tmp_path / "README.md").write_text("[live](docs/NATIVE_CONTROLS.md#live-hub-status)")
    (tmp_path / "docs/NATIVE_CONTROLS.md").write_text("### Live hub status\n")
    monkeypatch.setenv("PATH", "")
    test_live_status_anchor_links_resolve()
    extra = tmp_path / "docs/nested/new.md"
    extra.write_text("[live](../NATIVE_CONTROLS.md#live-hub-status-2026-10-18)")
    with pytest.raises(AssertionError):
        test_live_status_anchor_links_resolve()
    extra.write_text("[live](../NATIVE_CONTROLS.md#live-hub-status)")
    test_live_status_anchor_links_resolve()
