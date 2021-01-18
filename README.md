# mirror - Tools for software project analysis




___

## Github

### Base usage example

For correct usage github access token is requared.


#### Modules commands
```
  clone     
  crawl     
  nextid    
  sample    
  search    
  validate  
```



#### Extract all repos metadata

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

### Extract commits

