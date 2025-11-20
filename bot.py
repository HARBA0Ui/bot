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
    """Downloads the image and uploads it to Discord."""
    try:
        # 1. Identify the image URL (uses display_url to ensure we get an image, even for videos)
        image_url = post.url if not post.is_video else post.display_url
        
        # 2. Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            # 3. Send to Discord as a file attachment
            files = {
                "file": ("post_image.jpg", response.content, "image/jpeg")
            }
            payload = {
                "content": f"**New Post from {post.owner_username}!** 📸\n{post.caption}\n\nhttps://www.instagram.com/p/{post.shortcode}/"
            }
            # Note: We use 'data' instead of 'json' when sending files
            requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
            print("Post sent with image attached.")
        else:
            print("Failed to download image. Status code:", response.status_code)
            # Fallback: Send text only if image download fails
            raise Exception("Image download failed")

    except Exception as e:
        print(f"Error sending image: {e}. Sending link only.")
        # Fallback: Original text-only method
        data = {
            "content": f"**New Post from {post.owner_username}!** 📸\n{post.caption}\n\nhttps://www.instagram.com/p/{post.shortcode}/"
        }
        requests.post(DISCORD_WEBHOOK_URL, json=data)

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
