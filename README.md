# Drift CLI

[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/panda-official/DriftCLI)](https://pypi.org/project/drift-cli)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/drift-cli)](https://pypi.org/project/drift-cli)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/panda-oficial/DriftCLI/ci.yml?branch=main)](https://github.com/pannda-official/DriftCLI/actions)

Drift CLI is a command line client for [PANDA|Drift](https://driftpythonclient.readthedocs.io/en/latest/docs/panda_drift/) platform.

## Features

* Export data from Drift Blob Storage

## Requirements

* Python >= 3.8
* pip

## Installing

To install the Drift CLI, simply use pip:

```
pip install drift-cli
```
##

```
drift-cli --help
drift-cli alias add drift-device --address 127.0.0.1 --password SOME_PASSWORD
drift-cli export raw drift-device ./tmp --start 2021-01-01 --end 2021-01-02[export.md](..%2F..%2Freduct%2Freduct-cli%2Fdocs%2Fexport.md)[export.md](..%2F..%2Freduct%2Freduct-cli%2Fdocs%2Fexport.md)
```
## Links

* [Documentation](https://driftcli.readthedocs.io/en/latest/)
