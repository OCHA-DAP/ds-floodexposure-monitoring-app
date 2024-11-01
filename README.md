# Flood exposure monitoring app

## About

App showing estimated flood exposure based on WorldPop and Floodscan.

## Usage

Running the app locally:

1. Install the dependencies with `pip install -r requirements.txt`
2. Install the local package with `pip install -e .`
3. Set environment variables `DEV_BLOB_SAS` and `PROD_BLOB_SAS` to the SAS
token for the blob storage account.
4. Run the app with `python app.py` for debugging, or
`gunicorn -w 4 -b 127.0.0.1:8000 app:server` for production.

## Structure
<!-- markdownlint-disable -->
```plaintext
.
├── .github/
│   └── workflows/
│       └── ...          # build and deploy workflow
├── assets/
│   └── ...              # images, icon, CSS
├── callbacks/
│   └── callbacks.py     # single function to register all callbacks
├── components/
│   ├── alerts.py        # alerts at top of app
│   ├── dropdowns.py     # dropdown menus (options usually populated by callback)
│   ├── plots.py         # initialization of dcc.Graph components, content populated by callback
│   └── text.py          # text in app
├── data/
│   ├── data/
│   │   └── ...          # local data used in app (CODABs only)
│   └── load_data.py     # functions to load data into app, and migrate data from blob to repo
├── endpoints/
│   └── endpoints.py     # single endpoint to reload data
├── layouts/
│   ├── content.py       # main body of app
│   └── navbar.py        # just the top navbar
├── src/
│   ├── datasources/
│   │   ├── codab.py     # loading CODABs from blob
│   │   └── floodscan.py # loading Floodscan from blob
│   ├── utils/
│   │   └── blob.py      # loading data from blob
│   └── constants.py     # list of countries, other constants
├── app.py               # entrypoint for app
└── index.py             # initializes app layout
```
<!-- markdownlint-enable -->

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
