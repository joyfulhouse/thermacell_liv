# Development

How to set up a development environment for Thermacell LIV.

## Prerequisites

- Python 3.13+ and [`uv`](https://docs.astral.sh/uv/).

## Setup

```bash
git clone https://github.com/joyfulhouse/thermacell_liv.git
cd thermacell_liv
uv sync --extra dev --prerelease=allow
```

The `dev` extra installs Home Assistant (for typing) plus pytest, ruff, and
mypy.

## Quality Checks

```bash
uv run pytest tests/ -v                       # tests
uv run ruff check custom_components/thermacell_liv/   # lint
uv run ruff format custom_components/thermacell_liv/  # format
uv run mypy custom_components/thermacell_liv/         # type check (strict)
```

Run all of these before opening a pull request. The CI workflow
(`.github/workflows/ci.yaml`) runs lint, test, and type-check jobs plus the
Bronze→Platinum quality-scale gates; `validate.yaml` runs HassFest and HACS
validation.

Manual and integration tests under `tests/manual/`, `tests/integration/`, and
`tests/debug/` require real API credentials and are excluded from the default
test run.

## Architecture

This integration is built on the
[pythermacell](https://github.com/joyfulhouse/pythermacell) library, which
handles all Thermacell cloud API communication. See
[ARCHITECTURE.md](ARCHITECTURE.md) for the component breakdown and
[QUALITY_SCALE.md](QUALITY_SCALE.md) for quality-scale compliance.

## Releasing

1. Update the version in `custom_components/thermacell_liv/manifest.json`.
2. Move the `## [Unreleased]` notes in [CHANGELOG.md](../CHANGELOG.md) under a
   new version heading and update the compare links.
3. Tag the release `vX.Y.Z` and push the tag; the release workflow
   (`.github/workflows/release.yaml`) publishes it.

See
[CONTRIBUTING](https://github.com/joyfulhouse/.github/blob/main/CONTRIBUTING.md)
for the contribution workflow.
