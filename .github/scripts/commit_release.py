import argparse
import subprocess
from typing import Final

COMMITTER_NAME: Final[str] = "github-actions[bot]"
COMMITTER_EMAIL: Final[str] = "41898282+github-actions[bot]@users.noreply.github.com"


def main() -> None:
    """Commit the version bump and push it atomically with its tag."""

    parser = argparse.ArgumentParser()

    parser.add_argument("version")

    arguments = parser.parse_args()

    commands = (
        (
            "-c",
            f"user.name={COMMITTER_NAME}",
            "-c",
            f"user.email={COMMITTER_EMAIL}",
            "commit",
            "pyproject.toml",
            "-m",
            f"chore(release): bump version to {arguments.version}",
        ),
        ("tag", arguments.version),
        ("push", "--atomic", "origin", "HEAD", f"refs/tags/{arguments.version}"),
    )

    for command in commands:
        subprocess.run(["git", *command], check=True)


if __name__ == "__main__":
    main()
