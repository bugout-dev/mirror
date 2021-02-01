# mirror - Tools for software project analysis

## Setup
- Prepare python environment and install package
- For development please use `pip install -r requirements.dev.txt`
- Copy `sample.env` to `dev.env`, fill it with required variables and source it
```bash
export GITHUB_TOKEN="<your github token>"
export LANGUAGES_DIR="<directory with languages>"
```

- To avoid block from GitHub prepare Rate Limit watcher
```bash
watch -d -n 5 'curl https://api.github.com/rate_limit -s -H "Authorization: Bearer $GITHUB_TOKEN" "Accept: application/vnd.github.v3+json"'
```

### Modules commands

```
python -m mirror.cli --help

clone     Clone repos from search api to output dir.
commits   Read repos json file and upload all commits for that repos one...
crawl     Processes arguments as parsed from the command line and uses...
nextid    Prints ID of most recent repository crawled and written to the...
sample    Writes repositories sampled from a crawl directory to an output...
search    Crawl via search api.
validate  Prints ID of most recent repository crawled and written to the...
```

### Extract all repos metadata

For get all repos metadata need call `crawl` command that generate full amount of github repso metadata as big pack of json files.

```
python -m mirror.cli crawl \
        --crawldir $MIRROR_CRAWL_DIR \
        --interval $MIRROR_CRAWL_INTERVAL_SECONDS \
        --min-rate-limit $MIRROR_CRAWL_MIN_RATE_LIMIT \
        --batch-size $MIRROR_CRAWL_BATCH_SIZE
```

### Extract repos metadata via search api

Say you need extract only a small pool of repositories for analisys then you can set more precise criteria that you need via `search` command.

```
python -m mirror.cli search --crawldir $SEARCH_CRAWL_DIR -l "python" -st ">500"
```

That give you one big json file with repos data


### Clone repos from search to local for analize source

For that we use `clone` command it use search endpoint for download search result repos to local using simple git clone.
```
python -m mirror.cli clone --crawldir $CLONE_DIR -s ">500" -ls "python"
```

That return next output structure.

```
    > crawldir
      > language 1
        > repo 1
        > repo 2
        ...
      > language 2
        > repo 1
        > repo 2
        ...
      ...
```

Or from python code. As example upload most popular repos:
```python
from mirror.github.clone_repos import clone_repos

import os 

languages = (
    "CoffeeScript",
    "CSS",
    "Dart",
    "Elixir",
    "Go",
    "Groovy",
    "HTML",
    "Java",
    "Kotlin",
    "Objective-C",
    "Perl",
    "PHP",
    "PowerShell",
    "Ruby",
    "JavaScript",
    "Python"
)


crawldir = os.environ.get('LANGUAGES_DIR')
token = os.environ.get('GITHUB_TOKEN')
repos_per_language = 50

clone_repos.callback(crawldir=crawldir,
                     stars_expression='>500',
                     languages=languages,
                     token=token,
                     amount=repos_per_language)
```

### Create commits from repo search

For extract commts you can use "commits"
That command read input file with repos and return you are jsons files with commits for each repos 

```
python -m mirror.cli commits \
            --crawldir $MIRROR_CRAWL_DIR \
            --repos-file $MIRROR_CRAWL_INTERVAL_SECONDS \
```


### Convert json data to csv for analize

That utils create csv file and flatting json structure for that

```
python -m mirror.github.utils --json-files-folder $CRAWL_dir --output-csv $CSV_DATASET --command commits
```