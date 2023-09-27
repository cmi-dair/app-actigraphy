# App Actigraphy

[![Build](https://github.com/cmi-dair/app-actigraphy/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/cmi-dair/app-actigraphy/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/cmi-dair/app-actigraphy/branch/main/graph/badge.svg?token=22HWWFWPW5)](https://codecov.io/gh/cmi-dair/app-actigraphy)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![stability-wip](https://img.shields.io/badge/stability-work_in_progress-lightgrey.svg)
[![L-GPL License](https://img.shields.io/badge/license-L--GPL-blue.svg)](https://github.com/cmi-dair/app-actigraphy/blob/main/LICENSE)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://cmi-dair.github.io/app-actigraphy)

This webapp is an application designed for annotating sleep data. This repository contains the source code and related files for the application.

## Getting Started

The app may be installed either through Poetry or through Docker (recommended), see the instructions for each below. Whichever method you use to launch the app, the app will be available at http://localhost:8051.

### Running the App through Poetry

1. Ensure you have [Poetry](https://python-poetry.org/docs/) installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/cmi-dair/app-actigraphy.git
   cd app-actigraphy
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```
4. Run the app:
   ```bash
   poetry run actigraphy {DATA_DIR}
   ```

### Running the App through Docker

1. Ensure you have Docker installed.
2. Run the Docker image from our GitHub Container Registry. Note that you may have to login to GHCR first with `docker login`.
   ```bash
   docker run -p 8051:8051 ghcr.io/cmi-dair/app-actigraphy:main {DATA_DIR}
   ```

## Developer notes

The Actigraphy app is designed to annotate sleep data. While traditional Dash apps might not scale to complex applications, this repository employs a custom Dash architecture to address this:

- `app.py` contains the main Dash app, which is responsible for the layout of the app and the navigation between pages.
- `components/` directory houses the components utilized by the app. Each component is tasked with its specific layout and logic. Some of the components include file selection, day slider, and graph visualization.
- `core/` contains the core tools of the app, including configurations, utilities, command line interface and the callback manager.
- `core/callback_manager.py` is responsible for registering callbacks for the app. It is also responsible for registering callbacks for the components. This file allows the callbacks to be placed across multiple files by defining a global manager.
- `io/` contains the tools for loading and saving data.
- `plotting` contains the tools for plotting data.
