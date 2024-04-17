import argparse
import config
import json
import sys
import urllib.request
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


def check_latest(incident_id: str, incident_status: str) -> bool:
    """Check if the latest incident has already been posted."""
    with open(config.STATE_FILE, "r") as f:
        return f.read() == f"{incident_id} : {incident_status}"


def update_latest(incident_id: str, incident_status: str) -> None:
    """Update the latest incident hash."""
    with open(config.STATE_FILE, "w") as f:
        f.write(f"{incident_id} : {incident_status}")


def get_latest_incident():
    with urllib.request.urlopen(config.STATUS_API) as url:
        data = json.load(url)
        return data["incidents"][0]


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

    latest_incident = get_latest_incident()

    incident_id = latest_incident["id"]
    page_id = latest_incident["page_id"]
    incident_name = latest_incident["name"]
    incident_status = latest_incident["status"]
    short_link = latest_incident["shortlink"]
    started_at = latest_incident["started_at"]
    updated_at = latest_incident["updated_at"]

    if check_latest(incident_id, incident_status):
        print(
            f"Already posted this incident ({incident_id}) at state ({incident_status}). Exiting."
        )
        sys.exit(0)
    else:
        post = f"[{incident_status}]: [{incident_name}]({short_link}) ({updated_at})"
        if args.dry_run:
            print(f"[Dry]: {post}")
        else:
            update_latest(incident_id, incident_status)
            write_status(post, args.dry_run, args.visibility)
            print(f"Posted: {post}")
