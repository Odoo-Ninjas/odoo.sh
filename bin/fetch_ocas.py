#!/usr/bin/env python3
import click
import subprocess
import json
from pathlib import Path
import yaml
import os

gimera_file = Path("gimera.yml")
gimera = yaml.safe_load(gimera_file.read_text())
root = Path(os.getcwd())

versions = [12.0, 13.0, 14.0, 15.0, 16.0]

repos = json.loads(
    subprocess.check_output(
        ["gh", "repo", "list", "--limit", "9999", "OCA", "--json", "name,url"], encoding="utf8"
    )
)

for repo in repos:
    for version in versions:
        subfolder = root / "OCA" / repo["name"] / str(version)

        existing = [
            x for x in gimera['repos'] if x["url"] == repo["url"] and x["branch"] == str(version)
        ]
        if not existing:
            click.secho(f"Adding OCA: {repo['name']}#{version}")
            gimera["repos"].append(
                {
                    "url": repo["url"],
                    "path": str(subfolder.relative_to(root)),
                    "branch": str(version),
                    "type": "integrated",
                }
            )


gimera_file.write_text(yaml.dump(gimera))
