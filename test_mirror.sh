#!/usr/bin/env bash

# Tests mirror functions and pipelines
# Requirements:
# - Environment configured sample.env 

set -eu

OUTPUT_DIR="<parent directory for all output>"
GITHUB_TOKEN="<your GitHub token>"
LANGUAGES_DIR="${MIRROR_OUTPUT}/clone"
MIRROR_CRAWL_INTERVAL_SECONDS=1
MIRROR_CRAWL_MIN_RATE_LIMIT=10
MIRROR_CRAWL_BATCH_SIZE=100
MIRROR_AMOUNT_OF_STARS=">2000"
MIRROR_CRAWL_DIR_SEARCH="${MIRROR_OUTPUT}/search"
MIRROR_CRAWL_DIR_ALL_REPOS="${MIRROR_OUTPUT}/all_repos"
MIRROR_CRAWL_DIR_COMMITS="${MIRROR_OUTPUT}/commits"
MIRROR_LANGUAGES_FILE="docs/languages.json"
MIRROR_SNIPPETS_DIR="${MIRROR_OUTPUT}/snippets"


# Workflow for generate snippets
echo "Collect repo metadata"
python -m mirror.cli search \
    -d "${MIRROR_CRAWL_DIR_SEARCH}" \
    -s "${MIRROR_AMOUNT_OF_STARS}" \
    -f "${MIRROR_LANGUAGES_FILE}" \
    -l $MIRROR_CRAWL_MIN_RATE_LIMIT

echo "Clone repos to local directory."
python -m mirror.cli clone \
    -d "${LANGUAGES_DIR}" \
    -r "${MIRROR_CRAWL_DIR_SEARCH}"

echo "Generate snippets sqlite db."
python -m mirror.cli generate_snippets \
    -d "${JOURNAL_ID}" \
    -r "${MIRROR_SNIPPETS_DIR}" \




# Workflow for extract commits from search
echo "Get commits."
python -m mirror.cli commits \
    -d "${LANGUAGES_DIR}" \
    -r "${MIRROR_CRAWL_DIR_SEARCH}"