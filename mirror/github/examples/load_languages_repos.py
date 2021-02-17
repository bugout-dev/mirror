import os

from mirror.github.clone_repos import clone_repos

language_ext = {
    "CoffeeScript": ".coffee",
    "CSS": ".css",
    "Dart": ".dart",
    "Elixir": ".ex",
    "Go": ".go",
    "Groovy": ".groovy",
    "HTML": ".html",
    "Java": ".java",
    "Kotlin": ".kt",
    "Objective-C": ".m",
    "Perl": ".pl",
    "PHP": ".php",
    "PowerShell": ".sh",
    "Ruby": ".rb",
    "JavaScript": ".js",
    "Python": ".py",
}

clone_repos.callback(
    crawldir="D:\\languages",
    stars_expression=">500",
    languages=tuple(language_ext.keys()),
    token="",
    amount=50,
)
