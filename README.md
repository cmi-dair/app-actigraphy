# App Actigraphy

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
    poetry run python src/actigraphy/app.py {DATA_DIR}
   ```

### Running the App through Docker

1. Ensure you have Docker installed.
2. Run the Docker image from our GitHub Container Registry. Note that you may have to login to GHCR first with `docker login`.
   ```bash
   docker run -p 8051:8051 ghcr.io/cmi-dair/app-actigraphy:main {DATA_DIR}
   ```
