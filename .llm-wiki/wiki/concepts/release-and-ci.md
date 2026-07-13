---
type: concept
title: Release and CI pipeline
slug: release-and-ci
created: 2026-07-13
updated: 2026-07-13
tags: ["ci", "release", "github-actions", "pypi", "semantic-release", "poetry"]
---

# Release and CI pipeline

CI and release are driven by GitHub Actions workflows in `.github/workflows/`,
most of which reuse shared workflows from the `cape-ph/.github` repo.

## release.yml (Semantic Versioning Release)

- Triggers on push to `main` and on `pull_request_target` events.
- Calls the reusable
  `cape-ph/.github/.github/workflows/semantic_release.yml@main` with
  `release-type: python`.
- `is_production` is true only on push to `main`.
- Implies Conventional Commits drive version bumps and `CHANGELOG.md` entries.
  The current `CHANGELOG.md` reflects release `0.3.0`.

## cape.yml (CAPE)

- Triggers on push to `main`, on pull requests, and on release `created`.
- `python` job: reuses
  `cape-ph/.github/.github/workflows/poetry_python_checks.yml@sphinx` with
  `python_version: "3.10"`. Currently `pytest: false` and `sphinx: false` - a
  TODO says to enable tests and docs once an MVP schema is settled.
- `general` job: reuses `.../general_checks.yml@v1`.
- `publish` job: on release `created`, builds with `poetry build` and publishes
  to PyPI (`pypi.org/p/cape_cod_db`) via `pypa/gh-action-pypi-publish` using
  trusted publishing (OIDC `id-token: write`, `pypi` environment).

## Release flow summary

1. Merge Conventional-Commit changes to `main`.
2. semantic-release computes the next version, updates `CHANGELOG.md`, and
   creates a GitHub release/tag.
3. The release event triggers the `publish` job, which builds and uploads the
   wheel/sdist to PyPI.

A schema change (for example the planned ABAC rework) warrants a minor version
bump; downstream consumers such as `cape-cod-env` must then pin the new version.
See [[concepts/abac-authorization-design]].

## Related pages

- [[concepts/development-workflow]]
- [[concepts/abac-authorization-design]]
- [[entities/cape-cod-db]]
