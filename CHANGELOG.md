# Changelog

## [0.1.3](https://github.com/rubicon/rubicon-marketing-board/compare/v0.1.2...v0.1.3) (2026-10-19)


### Features

* **evals:** add a scripted eval runner with a judge and a pause eval ([#57](https://github.com/rubicon/rubicon-marketing-board/issues/57)) ([4f96d60](https://github.com/rubicon/rubicon-marketing-board/commit/4f96d6026c63b78a62560d49e0c8a3d3d17e7b22)), closes [#44](https://github.com/rubicon/rubicon-marketing-board/issues/44)
* **skill:** admit user-supplied evidence through a disclosed table ([#60](https://github.com/rubicon/rubicon-marketing-board/issues/60)) ([f873b27](https://github.com/rubicon/rubicon-marketing-board/commit/f873b27add56f92acc3ecdf0bc5bb867199f9b9f)), closes [#42](https://github.com/rubicon/rubicon-marketing-board/issues/42)
* **skill:** emit a structured handoff block in the chair's synthesis ([#53](https://github.com/rubicon/rubicon-marketing-board/issues/53)) ([c166eb7](https://github.com/rubicon/rubicon-marketing-board/commit/c166eb70a23df366230fa0e3ef3d48f58d063bc1)), closes [#45](https://github.com/rubicon/rubicon-marketing-board/issues/45)


### Bug Fixes

* **evals:** grant the plugin directory and refuse to grade a blocked run ([#62](https://github.com/rubicon/rubicon-marketing-board/issues/62)) ([03a4bf8](https://github.com/rubicon/rubicon-marketing-board/commit/03a4bf855e190ce32c4c2220b60957ae59672825)), closes [#61](https://github.com/rubicon/rubicon-marketing-board/issues/61)

## [0.1.2](https://github.com/rubicon/rubicon-marketing-board/compare/v0.1.1...v0.1.2) (2026-09-02)


### Bug Fixes

* **ci:** repair the broken release-please 1Password reference ([#51](https://github.com/rubicon/rubicon-marketing-board/issues/51)) ([50eb799](https://github.com/rubicon/rubicon-marketing-board/commit/50eb799c139274be8e9bfea316bdf3a8a289b807)), closes [#50](https://github.com/rubicon/rubicon-marketing-board/issues/50)

## [0.1.1](https://github.com/rubicon/rubicon-marketing-board/compare/v0.1.0...v0.1.1) (2026-07-12)

v0.1.1 is a maintenance release: two CI fixes, no change to the board's content or behavior. The commitlint config shipped in v0.1.0 blocked every Dependabot PR on an unwrappable body-length rule, and a one-time version pin meant to force the first release was never removed, so release-please kept re-targeting v0.1.0 instead of computing the next version. Both are fixed; dependency updates and future releases should flow normally again.


### Bug Fixes

* **ci:** allow long body lines in commitlint ([#34](https://github.com/rubicon/rubicon-marketing-board/issues/34)) ([f420e17](https://github.com/rubicon/rubicon-marketing-board/commit/f420e174265fae6c8fb31ac4b5acb20e91769677)), closes [#33](https://github.com/rubicon/rubicon-marketing-board/issues/33)
* **ci:** stop re-pinning release-please to v0.1.0 ([#37](https://github.com/rubicon/rubicon-marketing-board/issues/37)) ([42a62bc](https://github.com/rubicon/rubicon-marketing-board/commit/42a62bcfb0119d03de608bb7b1dff2361d9733eb)), closes [#36](https://github.com/rubicon/rubicon-marketing-board/issues/36)

## 0.1.0 (2026-07-09)

Rubicon Marketing Board v0.1.0 is the first release: nine seat agents, forty source dossiers, an orchestrator skill, four commands, and an eval suite that was actually run against the shipped agents before this tag went out, not just written and left on the shelf. Every seat argues from a real, published framework, not a vibe, and every full session seats at least one advisor whose job is to disagree with you. This is a first release, not a finished one: the eval suite covers the load-bearing paths, not every path, and the bench is going to grow. Nothing here was smoothed over to read better than it works.

### Features

* add orchestrator skill, references, and commands ([#24](https://github.com/rubicon/rubicon-marketing-board/issues/24)) ([fffaa31](https://github.com/rubicon/rubicon-marketing-board/commit/fffaa312d1459ae55867b1c6a38d73a41ba89a67))
* add plugin manifests, validation, CI, and release automation ([#6](https://github.com/rubicon/rubicon-marketing-board/issues/6)) ([84c91f5](https://github.com/rubicon/rubicon-marketing-board/commit/84c91f5ac7901350a1bf7d85741835681d33f4e1))
* add the forty source dossiers ([#20](https://github.com/rubicon/rubicon-marketing-board/issues/20)) ([b50a349](https://github.com/rubicon/rubicon-marketing-board/commit/b50a3498d6e6e2fe3dfb515dbbca127d4f06e5b6))
* add the nine board-seat agents ([#22](https://github.com/rubicon/rubicon-marketing-board/issues/22)) ([6528368](https://github.com/rubicon/rubicon-marketing-board/commit/65283685bbac4fdb8aec2c762666178c3eb743c1))

## Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
