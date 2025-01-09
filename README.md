# App Actigraphy

[![Build](https://github.com/childmindresearch/app-actigraphy/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/childmindresearch/app-actigraphy/actions/workflows/test.yaml?query=branch%3Amain)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-wip](https://img.shields.io/badge/stability-work_in_progress-lightgrey.svg)
[![L-GPL License](https://img.shields.io/badge/license-L--GPL-blue.svg)](https://github.com/childmindresearch/app-actigraphy/blob/main/LICENSE)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://childmindresearch.github.io/app-actigraphy)

This webapp is an application designed for annotating sleep data. This repository contains the source code and related files for the application.

## Getting Started

The app may be installed either through Docker (recommended for users) or Poetry (recommended for developers), see the instructions for each below. Whichever method you use to launch the app, the app will be available at http://localhost:8051.

### Running the App through Docker

1. Ensure you have Docker installed.
2. Run the Docker image:
   ```bash
   docker run \
      -p 127.0.0.1:8051:8051 \
      --volume ${LOCAL_DATA_DIR}:/data \
      --volume `pwd`/assets:/app/assets \
      cmidair/actigraphy:main
   ```

### Running the App through Poetry

1. Ensure you have [Poetry](https://python-poetry.org/docs/) installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/childmindresearch/app-actigraphy.git
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

## Preprocessing the data

To batch preprocess GGIR data for the app, use the `actigraphy_preprocess` entrypoint as follows:

```bash
   docker run \
      --volume ${LOCAL_DATA_DIR}:/data \
      cmidair/actigraphy:latest \
      actigraphy_preprocess \
```

This may also be done with Poetry through:

```bash
   poetry run actigraphy_preprocess {DATA_DIR}
```

## Developer notes

The Actigraphy app is developed to annotate sleep data, and for this project, we've utilized the Dash framework. It's important to note that Dash apps usually aren't geared towards full-stack applications, but given the project requirements, adopting it was a pragmatic necessity. In this repository, we've implemented a custom Dash architecture to address some typical challenges associated with a full-stack Dash app, particularly through the introduction of a custom callback manager. The organization of the project is structured as follows:

- `app.py` contains the main Dash app, which is responsible for the layout of the app.
- `components/` houses the components utilized by the app. Each component is tasked with its specific layout and logic. Some of the components include file selection, day slider, and graph visualization.
- `core/` contains the core tools of the app, including configurations, utilities, command line interface and the callback manager.
- `core/callback_manager.py` is responsible for registering callbacks for the app. It is also responsible for registering callbacks for the components. This file allows the callbacks to be placed across multiple files by defining a global manager.
- `database/` contains the tools for interacting with the database.
- `io/` contains the tools for loading and saving data.
- `plotting` contains the tools for plotting data.

That being said, the callback architecture has grown complex, especially in the graph component where chains of callbacks can cause the app to slow down.
