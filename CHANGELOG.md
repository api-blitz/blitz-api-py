# Changelog

## [4.0.0](https://github.com/api-blitz/blitz-api-py/compare/v3.0.0...v4.0.0) (2026-09-22)


### ⚠ BREAKING CHANGES

* `search.companies(company=...)` no longer type-checks a dict literal containing `linkedin_url`. The endpoint never honoured it, so drop the key. On `search.people` and `company.tam_by_people` it keeps working, now typed as `PeopleCompanyFilter` (exported from `blitz_api` and `blitz_api.types`).
* `Company.slogan`, `Company.revenue` and `Company.employee_growth` are removed, as is the `EmployeeGrowth` model and its `blitz_api.types` export -- the API never returned any of them. `Company.specialties` is now `list[str]` defaulting to `[]` rather than `list[str] | None`; code branching on `specialties is None` should check for an empty list instead.
* `InsufficientCreditsError` is removed. Catch `InsufficientRecordsError` instead.
* `Education.field_of_study` is removed — the API folded it into `degree` ("Bachelor of Science, Industrial Engineering").

### Features

* add the Industry.UNKNOWN bucket and document the range-filter 422 ([5f2d944](https://github.com/api-blitz/blitz-api-py/commit/5f2d944427b631b4b668af0bc99f614161b00425))
* remove the deprecated InsufficientCreditsError alias ([0c9be23](https://github.com/api-blitz/blitz-api-py/commit/0c9be232268cb68cfa36d7352e1304608bed32cc))
* split PeopleCompanyFilter out of the shared CompanyFilter ([fc6983e](https://github.com/api-blitz/blitz-api-py/commit/fc6983eef696c058620a799ec4b4f476ed32701d)), closes [#25](https://github.com/api-blitz/blitz-api-py/issues/25)
* sync SDK to the 2026-09-11 / 2026-09-15 API releases ([81460ed](https://github.com/api-blitz/blitz-api-py/commit/81460edbcff5f985fd3e1498d70b282ce11d7550))


### Bug Fixes

* remove phantom Company fields and the redundant _drop_none layer ([52b5ec5](https://github.com/api-blitz/blitz-api-py/commit/52b5ec5ec7241d2ea7dd6aacf2a3d0bbcc73dec2))


### Documentation

* correct the profile_min_connections default to 0, not 200 ([6ee2893](https://github.com/api-blitz/blitz-api-py/commit/6ee2893c7082b075f9d83ab5dc68943a8126a965)), closes [#26](https://github.com/api-blitz/blitz-api-py/issues/26)
* correct the README headline example and route to enrichment.person ([7051afb](https://github.com/api-blitz/blitz-api-py/commit/7051afb1fa362621e23ae8ed25f2ae20a842006e)), closes [#30](https://github.com/api-blitz/blitz-api-py/issues/30)
* correct the stale rate-limit and spec-version facts ([10615d5](https://github.com/api-blitz/blitz-api-py/commit/10615d58b6f6d4905e1f00033032fd5fbf13a350))
* correct the stale response-schema rule and link the JS mirror PR ([1f1381f](https://github.com/api-blitz/blitz-api-py/commit/1f1381f164c0bc02b46a20ec94cec4c079375f44))
* guard the optional linkedin_url in the README enrichment example ([cdcfb71](https://github.com/api-blitz/blitz-api-py/commit/cdcfb71171131bf9400e99737b455ef7676c4b70))
* name the legacy 50 req/s rate limit instead of "more on legacy ones" ([f4974a1](https://github.com/api-blitz/blitz-api-py/commit/f4974a123ad869f3f1e9aa28293dede6ce24648b)), closes [#29](https://github.com/api-blitz/blitz-api-py/issues/29)
* the /changelog/ trailing slash is not load-bearing ([891d5b7](https://github.com/api-blitz/blitz-api-py/commit/891d5b7e1c04583c14997ff9ad7fc39e3f8d4245)), closes [#28](https://github.com/api-blitz/blitz-api-py/issues/28)

## [3.0.0](https://github.com/api-blitz/blitz-api-py/compare/v2.2.0...v3.0.0) (2026-09-02)


### ⚠ BREAKING CHANGES

* `KeyInfo.remaining_credits` is renamed to `KeyInfo.records_remaining`.

### Features

* records vocabulary rename + fair_usage envelope on every response ([698fd6d](https://github.com/api-blitz/blitz-api-py/commit/698fd6dc95bbe6120c55064255820898b708da42))

## [2.2.0](https://github.com/api-blitz/blitz-api-py/compare/v2.1.0...v2.2.0) (2026-08-13)


### Features

* add company and changelog resources with new endpoints ([0dd4ae0](https://github.com/api-blitz/blitz-api-py/commit/0dd4ae0df510352c72143f00431e66b947409758))

## [2.1.0](https://github.com/api-blitz/blitz-api-py/compare/v2.0.0...v2.1.0) (2026-07-23)


### Features

* add jobs resource with search and company endpoints ([c96e67a](https://github.com/api-blitz/blitz-api-py/commit/c96e67ad9812f6f6c46b3aa095f7ba6792ec4a81))

## [2.0.0](https://github.com/api-blitz/blitz-api-py/compare/v1.0.0...v2.0.0) (2026-06-19)


### ⚠ BREAKING CHANGES

* spec-faithful type names for funding enum + distribution responses ([#17](https://github.com/api-blitz/blitz-api-py/issues/17)) (#18)

### Features

* spec-faithful type names for funding enum + distribution responses ([#17](https://github.com/api-blitz/blitz-api-py/issues/17)) ([#18](https://github.com/api-blitz/blitz-api-py/issues/18)) ([95370bd](https://github.com/api-blitz/blitz-api-py/commit/95370bdcd8771a40d9a6bdf921a609dca038bad5))

## [1.0.0](https://github.com/api-blitz/blitz-api-py/compare/v0.5.0...v1.0.0) (2026-06-19)


### ⚠ BREAKING CHANGES

* funding/HQ-state search filters + relocate distribution endpoints ([#15](https://github.com/api-blitz/blitz-api-py/issues/15))

### Features

* funding/HQ-state search filters + relocate distribution endpoints ([#15](https://github.com/api-blitz/blitz-api-py/issues/15)) ([f711ee8](https://github.com/api-blitz/blitz-api-py/commit/f711ee81a9e046bd7e354b593eda9e8d978768e3))

## [0.5.0](https://github.com/api-blitz/blitz-api-py/compare/v0.4.0...v0.5.0) (2026-06-18)


### Features

* scope client-side rate limiting per endpoint ([#13](https://github.com/api-blitz/blitz-api-py/issues/13)) ([de5308b](https://github.com/api-blitz/blitz-api-py/commit/de5308b6995edc68dd1e43a8554296b7de095df2))

## [0.4.0](https://github.com/api-blitz/blitz-api-py/compare/v0.3.0...v0.4.0) (2026-06-17)


### Features

* add company department distribution endpoint and response models ([b64a6d9](https://github.com/api-blitz/blitz-api-py/commit/b64a6d9bada069206c77ee11c9f86fae01ef6baa))


### Documentation

* port JS SDK README upgrade (badges, billing note, TOC, example) ([#11](https://github.com/api-blitz/blitz-api-py/issues/11)) ([2276513](https://github.com/api-blitz/blitz-api-py/commit/2276513cdae4c23d4a1b50f59366e7156bf81019))

## [0.3.0](https://github.com/api-blitz/blitz-api-py/compare/v0.2.0...v0.3.0) (2026-06-04)


### Features

* generate enums from the live OpenAPI spec with offline drift guard ([#9](https://github.com/api-blitz/blitz-api-py/issues/9)) ([fee865c](https://github.com/api-blitz/blitz-api-py/commit/fee865c4d8f7c685330794fa79921dccd7556e37))

## [0.2.0](https://github.com/api-blitz/blitz-api-py/compare/v0.1.0...v0.2.0) (2026-06-02)


### Features

* cursor guard, page.collect(), and typed waterfall-icp fields ([#7](https://github.com/api-blitz/blitz-api-py/issues/7)) ([b77cdff](https://github.com/api-blitz/blitz-api-py/commit/b77cdffc99c680c2a37d36c8d22ee4c5381e8c68))

## [0.1.0](https://github.com/api-blitz/blitz-api-py/compare/v0.1.0...v0.1.0) (2026-06-02)


### Features

* typed Python SDK for the Blitz API with automated releases ([5641a51](https://github.com/api-blitz/blitz-api-py/commit/5641a51b405108029bc701988e08d6210a1255f6))

## Changelog

All notable changes to this project are documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
and the changelog is maintained automatically by
[release-please](https://github.com/googleapis/release-please) from
[Conventional Commits](https://www.conventionalcommits.org/).
