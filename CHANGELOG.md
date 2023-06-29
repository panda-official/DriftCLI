# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Rise an error if --with-metadata used with --csv, [PR-14](https://github.com/panda-official/DriftCLI/pull/14)

## 0.7.0 - 2023-06-26

### Added

- DRIFT-684: `--with-metadata` flag for `export raw` command, [PR-13](https://github.com/panda-official/DriftCLI/pull/13)

## 0.6.1 - 2023-06-19

### Fixed

- DRIFT-613: Use new `Client.walk` method to improve performance, [PR-12](https://github.com/panda-official/DriftCLI/pull/12)

## 0.6.0 - 2023-04-12

## Added

- Add support for stacked images, [PR-11](https://github.com/panda-official/DriftCLI/pull/11)

## 0.5.0 - 2023-04-06

### Added

- Add `--debug` flag to see stack of exceptions, [PR-7](https://github.com/panda-official/DriftCLI/pull/7)

### Changed

- Minimal version of DriftPythonClient 0.5.0, [PR-9](https://github.com/panda-official/DriftCLI/pull/9)

### Fixed

- Skip packages with bad status during the export to JPEG, [PR-8](https://github.com/panda-official/DriftCLI/pull/8)

## [0.4.0] - 2023-03-15

### Added

- Optimisation of data download, [PR-6](https://github.com/panda-official/DriftCLI/pull/6)

## [0.3.0] - 2023-03-10

### Added

- Option `--jpeg` to `export raw`command, [PR-4](https://github.com/panda-official/DriftCLI/pull/4)

## [0.2.0] - 2023-02-22

### Added

- Option `--topics`to `export raw` command, [PR-3](https://github.com/panda-official/DriftCLI/pull/3)

## [0.1.0] - 2023-02-20

### Added

- `drift-cli alias` command to manage aliases, [PR-1](https://github.com/panda-official/DriftCLI/pull/1)
- `drift-cli export raw` command to export data from blob
  storage, [PR-2](https://github.com/panda-official/DriftCLI/pull/2)
