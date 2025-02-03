# Flood exposure monitoring app

## About

App showing estimated flood exposure based on WorldPop and Floodscan.

## Usage

Running the app locally:

1. Install the dependencies with `pip install -r requirements.txt`
2. Install the local package with `pip install -e .`
3. Create a local `.env` file with the variables:

```bash
PROD_BLOB_SAS=<provided-on-request>
DEV_BLOB_SAS=<provided-on-request>
AZURE_DB_PW_DEV=<provided-on-request>
AZURE_DB_UID=<provided-on-request>
STAGE=<"dev" or "prod">
```

token for the blob storage account.
4. Run the app with `python app.py` for debugging, or
`gunicorn -w 4 -b 127.0.0.1:8000 app:server` for production.

### To add a new ISO3 code

Changes need to be made in this repo so that flood exposure data from a new ISO3
can be displayed in the app. Once there is new data in the Postgres database
(as output from [here](https://github.com/OCHA-DAP/ds-floodexposure-monitoring)):

1. Pull this code locally and create a new branch
2. Add the new ISO3 code to the list of `ISO3S`
[here](https://github.com/OCHA-DAP/ds-floodexposure-monitoring-app/blob/ddd1a840f32687d45e18b52172f9a5bd65a1ffd0/constants.py#L9)
3. Run `python download_geodata.py` to update the boundary files in `assets/geo/`
and the `adm` database table. Note that both the `dev` and `prod` databases will
need to be updated. This can be configured via the `STAGE` environment variable.
4. Commit the changes and open a PR on GitHub for review

## Development

All code is formatted according to black and flake8 guidelines.
The repo is set-up to use pre-commit.
Before you start developing in this repository, you will need to run

```shell
pre-commit install
```

The `markdownlint` hook will require
[Ruby](https://www.ruby-lang.org/en/documentation/installation/)
to be installed on your computer.

You can run all hooks against all your files using

```shell
pre-commit run --all-files
```

It is also **strongly** recommended to use `jupytext`
to convert all Jupyter notebooks (`.ipynb`) to Markdown files (`.md`)
before committing them into version control. This will make for
cleaner diffs (and thus easier code reviews) and will ensure that cell outputs aren't
committed to the repo (which might be problematic if working with sensitive data).
