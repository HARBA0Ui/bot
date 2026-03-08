import os
import json
import time
import random
import requests
import instaloader
from datetime import datetime

# Environment variables
IG_USERNAME = os.environ.get("IG_USERNAME")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

STATE_FILE = "latest_post.json"


def create_loader():
    """Create Instaloader instance"""

    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False
    )

    # Try loading login session (optional but recommended)
    try:
        loader.load_session_from_file(IG_USERNAME)
        print("Instagram session loaded.")
    except Exception:
        print("No session file found. Running without login (more rate limits).")

    return loader


def get_latest_post(username):
    """Fetch latest Instagram post with retries"""

    loader = create_loader()

    retries = 3

    for attempt in range(retries):

        try:

            print(f"Fetching posts (attempt {attempt+1})")

            profile = instaloader.Profile.from_username(
                loader.context,
                username
            )

            posts = profile.get_posts()

            latest_post = next(posts)

            return latest_post

        except Exception as e:

            print("Error:", e)

            if "429" in str(e):

                wait_time = 900
                print(f"Rate limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)

            else:
                time.sleep(60)

    return None


def send_to_discord(post):
    """Send Instagram post to Discord"""

    try:

        image_url = post.url if not post.is_video else post.display_url

        response = requests.get(image_url, timeout=20)

        if response.status_code == 200:

            files = {
                "file": ("post.jpg", response.content, "image/jpeg")
            }

            payload = {
                "content": f"**New Post from {post.owner_username}!** 📸\n\nhttps://www.instagram.com/p/{post.shortcode}/"
            }

            requests.post(
                DISCORD_WEBHOOK_URL,
                data=payload,
                files=files
            )

            print("Post sent with image.")

        else:
            raise Exception("Image download failed")

    except Exception as e:

        print("Image failed:", e)

        payload = {
            "content": f"**New Post from {post.owner_username}!** 📸\n\nhttps://www.instagram.com/p/{post.shortcode}/"
        }

        requests.post(DISCORD_WEBHOOK_URL, json=payload)


def load_last_post():
    """Load previous post state"""

    if os.path.exists(STATE_FILE):

        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)
                return data.get("shortcode")

        except Exception:
            return None

    return None


def save_last_post(shortcode):
    """Save latest post state"""

    with open(STATE_FILE, "w") as f:

        json.dump(
            {
                "shortcode": shortcode,
                "timestamp": str(datetime.now())
            },
            f
        )


def main():

    if not IG_USERNAME or not DISCORD_WEBHOOK_URL:
        print("Missing environment variables.")
        return

    # Random delay to reduce bot detection
    delay = random.randint(10, 30)
    print(f"Sleeping {delay} seconds before starting...")
    time.sleep(delay)

    last_shortcode = load_last_post()

    latest_post = get_latest_post(IG_USERNAME)

    if not latest_post:
        print("Could not fetch posts.")
        return

    if latest_post.shortcode != last_shortcode:

        print("New post detected:", latest_post.shortcode)

        send_to_discord(latest_post)

        save_last_post(latest_post.shortcode)

    else:
        print("No new posts.")


if __name__ == "__main__":
    main()
