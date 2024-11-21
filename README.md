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
```

token for the blob storage account.
4. Run the app with `python app.py` for debugging, or
`gunicorn -w 4 -b 127.0.0.1:8000 app:server` for production.

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
