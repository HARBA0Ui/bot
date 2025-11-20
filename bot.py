import os
import json
import requests
import instaloader
from datetime import datetime

# Configuration
IG_USERNAME = os.environ.get('IG_USERNAME')
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
STATE_FILE = 'latest_post.json'

def get_latest_post(username):
    """Fetches the latest post from a public Instagram profile."""
    L = instaloader.Instaloader()
    
    # Optional: Load session if you have one to avoid login limits
    # L.load_session_from_file(username) 

    try:
        profile = instaloader.Profile.from_username(L.context, username)
        posts = profile.get_posts()
        # Get the most recent post
        post = next(posts)
        return post
    except Exception as e:
        print(f"Error fetching Instagram posts: {e}")
        return None

def send_to_discord(post):
    """Sends the post to Discord via Webhook."""
    data = {
        "content": f"**New Post from {post.owner_username}!** 📸\n{post.caption[:100]}...\n\nhttps://www.instagram.com/p/{post.shortcode}/"
    }
    result = requests.post(DISCORD_WEBHOOK_URL, json=data)
    try:
        result.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"Discord Webhook Error: {err}")
    else:
        print("Post sent to Discord successfully.")

def main():
    # 1. Load previous state
    last_shortcode = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            try:
                data = json.load(f)
                last_shortcode = data.get('shortcode')
            except json.JSONDecodeError:
                pass

    # 2. Get current latest post
    latest_post = get_latest_post(IG_USERNAME)
    
    if not latest_post:
        print("No posts found or error occurred.")
        return

    # 3. Compare and Send
    if latest_post.shortcode != last_shortcode:
        print(f"New post found: {latest_post.shortcode}")
        send_to_discord(latest_post)
        
        # 4. Save new state
        with open(STATE_FILE, 'w') as f:
            json.dump({'shortcode': latest_post.shortcode, 'timestamp': str(datetime.now())}, f)
    else:
        print("No new posts since last check.")

if __name__ == "__main__":
    if not IG_USERNAME or not DISCORD_WEBHOOK_URL:
        print("Error: Environment variables IG_USERNAME or DISCORD_WEBHOOK_URL not set.")
    else:
        main()
