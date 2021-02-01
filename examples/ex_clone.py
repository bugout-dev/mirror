import os
from mirror.github.clone_repos import clone_repos

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
    "Python",
)

LANGUAGES_DIR = os.environ.get("LANGUAGES_DIR")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def main() -> None:
    repos_per_language = 50

    clone_repos.callback(
        crawldir=LANGUAGES_DIR,
        stars_expression=">500",
        languages=languages,
        token=GITHUB_TOKEN,
        amount=repos_per_language,
        languages_file="languages.json",
    )


if __name__ == "__main__":
    main()
