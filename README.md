# mirror - Tools for software project analysis

## Setup
- Prepare python environment and install package
- For development please use `pip install -r requirements.dev.txt`
- Copy `sample.env` to `dev.env`, fill it with required variables and source it
```bash
export GITHUB_TOKEN="<your GitHub token>"
export LANGUAGES_DIR="<prepared directory with languages>"
export MIRROR_CRAWL_INTERVAL_SECONDS=1
export MIRROR_CRAWL_MIN_RATE_LIMIT=500
export MIRROR_CRAWL_BATCH_SIZE="<how often save data>"
export MIRROR_CRAWL_DIR="<where to save crawled data>"
```

- To avoid block from GitHub prepare Rate Limit watcher
```bash
watch -d -n 5 'curl https://api.github.com/rate_limit -s -H "Authorization: Bearer $GITHUB_TOKEN" "Accept: application/vnd.github.v3+json"'
```

### Module commands

```
python -m mirror.cli --help

clone     Clone repos from search api to output dir.
commits   Read repos json file and upload all commits for that repos one.
crawl     Processes arguments as parsed from the command line and uses.
nextid    Prints ID of most recent repository crawled and written to the.
sample    Writes repositories sampled from a crawl directory to an output.
search    Crawl via search api.
validate  Prints ID of most recent repository crawled and written to the.
```

### Extract all repos metadata

Run the `crawl` command to extract all repositories metadata and save in a `.json` file.

```bash
python -m mirror.cli crawl \
  --crawldir $MIRROR_CRAWL_DIR \
  --interval $MIRROR_CRAWL_INTERVAL_SECONDS \
  --min-rate-limit $MIRROR_CRAWL_MIN_RATE_LIMIT \
  --batch-size $MIRROR_CRAWL_BATCH_SIZE
```

### Extract repos metadata via search api

Say you need to extract only a small pool of repositories for analysis then you can set more precise criteria that you need via `search` command. 

```bash
python -m mirror.cli search --crawldir "$MIRROR_CRAWL_DIR/search" -l "python" -st ">500" -r 5
```

### Clone repos to local machine for analysis

The `clone` command uses the standard `git clone` to extract search results of repositories and clones to local machine.

```bash
python -m mirror.cli clone --crawldir "$LANGUAGES_DIR" -s ">500" -ls "python"
```

Structure of `$LANGUAGES_DIR` directory:

```
> $LANGUAGES_DIR
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

Also, there is possibility to upload popular repositories with python code. See example in [ex_clone.py](https://github.com/bugout-dev/mirror/examples/ex_clone.py)

### Create commits from repo search

Command `commits` extract all commits from repository and save `.json` files with commits for each repository.

```bash
python -m mirror.cli commits \
  --crawldir $MIRROR_CRAWL_DIR \
  --repos-file $MIRROR_CRAWL_INTERVAL_SECONDS \
```


### Convert json data to csv for analysis

It creates `.csv` file with flat json structure.

```bash
python -m mirror.github.utils --json-files-folder "$MIRROR_CRAWL_DIR" --output-csv "$MIRROR_CRAWL_DIR/output.csv" --command commits
```
