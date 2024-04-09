import argparse
import config
import feedparser
import sys
from enum import Enum
from mastodon import Mastodon
from pathlib import Path


class Visibility(Enum):
    """The possible visibilities for a post according to the mastodon client"""

    private = "private"
    direct = "direct"
    unlisted = "unlisted"
    public = "public"

    def __str__(self: "Visibility") -> str:
        return self.value


def check_latest(link_hash: str) -> bool:
    """Check if the latest incident has already been posted."""
    with open(config.STATE_FILE, "r") as f:
        return f.read() == link_hash


def update_latest(link_hash: str) -> None:
    """Update the latest incident hash."""
    with open(config.STATE_FILE, "w") as f:
        f.write(link_hash)


def write_status(
    status: str, dry_run: bool = False, visibility: Visibility = Visibility("unlisted")
) -> None:
    """Write a status to Mastodon"""
    mastodon = Mastodon(access_token=config.ACCESS_TOKEN, api_base_url=config.API_URL)
    if dry_run is False:
        # Post
        mastodon.status_post(status=status, visibility=str(visibility))
        print(f"Posted {status}")
    else:
        print(f"Dry run, would have posted {status}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="awawawa")
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Post nothing, don't update state file",
    )
    parser.add_argument(
        "--visibility",
        type=Visibility,
        choices=list(Visibility),
        action="store",
        default="unlisted",
    )
    args = parser.parse_args()

    # Part of my brain is screaming at me for this, but I'm going to ignore it
    Path(config.STATE_FILE).touch(exist_ok=True)

    feed = feedparser.parse(config.RSS_FEED)

    entry = feed.entries[0]  # latest incident
    link_hash = entry.link.split("/")[-1]
    post = f"New incident: [{entry.title}]({entry.link}) ({entry.published})"

    if check_latest(link_hash):
        print(f"Already posted this incident ({link_hash}). Exiting.")
        sys.exit(0)
    else:
        print(f"New incident detected ({link_hash}). Posting.")
        write_status(post, args.dry_run, args.visibility)
        if args.dry_run is False:
            update_latest(link_hash)
