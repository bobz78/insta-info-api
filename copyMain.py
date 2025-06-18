import json
import codecs
import uuid
import requests
import os
from flask import Flask, jsonify
from datetime import datetime
from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError, ClientCompatPatch)

app = Flask(__name__)


# -----------------------Avoid re-login----------------------
def to_json(python_object):
    if isinstance(python_object, bytes):
        return {
            '__class__': 'bytes',
            '__value__': codecs.encode(python_object, 'base64').decode()
        }
    raise TypeError(repr(python_object) + ' is not JSON serializable')


def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object


def on_login_callback(api, new_settings_file):
    cache_settings = api.settings
    with open(new_settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('SAVED: {0!s}'.format(new_settings_file))


# Users Login info
username = 'bob_z78'
password = 'Babakzeini1378@'
# --------------------------
settings_file = 'ig_settings.json'

device_id = None
api = None

try:
    if not os.path.isfile(settings_file):
        print(f"Settings file not found. Logging in as {username}...")
        api = Client(username, password, on_login=lambda x: on_login_callback(x, settings_file))
    else:
        with open(settings_file) as file_data:
            cached_settings = json.load(file_data, object_hook=from_json)
        print(f"Using cached settings from {settings_file}")
        device_id = cached_settings.get('device_id')
        api = Client(username, password, settings=cached_settings)
except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
    print(f"Session expired. Re-logging in... ({e})")
    api = Client(username, password, device_id=device_id, on_login=lambda x: on_login_callback(x, settings_file))
except ClientLoginError as e:
    print(f"Login error: {e}")
    exit(9)
except ClientError as e:
    print(f"Client error: {e.msg} (Code: {e.code}, Response: {e.error_response})")
    exit(9)
except Exception as e:
    print(f"Unexpected error: {e}")
    exit(99)

cookie_expiry = api.cookie_jar.auth_expires
print('Cookie Expiry:', datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ'))
# -----------------------Avoid re-login----------------------


# -----------------------set up private API-------------------
results = api.feed_timeline()
items = [item for item in results.get('feed_items', []) if item.get('media_or_ad')]
for item in items:
    ClientCompatPatch.media(item['media_or_ad'])
    print(item['media_or_ad']['code'])


# -----------------------set up private API-------------------

# -----------------------Variables----------------------------


# -----------------------Fetch Data Methods-------------------
def get_own_number_of_followers():
    try:
        user_info = api.current_user()
        number_of_followers = user_info['user']['follower_count']
        return number_of_followers
    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_number_of_followers(target_username):
    try:
        user_info = api.username_info(target_username)
        number_of_followers = user_info['user']['follower_count']
        return number_of_followers
    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_own_number_of_following():
    try:
        user_info = api.current_user()
        number_of_followers = user_info['user']['follower_count']
        return number_of_followers
    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_number_of_following(target_username):
    try:
        user_info = api.username_info(target_username)
        number_of_followers = user_info['user']['follower_count']
        return number_of_followers
    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_own_followers():
    try:
        user_info = api.current_user()
        user_id = user_info['user']['pk']
        rank_token = str(uuid.uuid4())
        followers = api.user_followers(user_id, rank_token=rank_token)
        return followers
    except Exception as e:
        print(f"Error: {e}")
        return {}


def get_followers(target_username):
    try:
        user_info = api.username_info(target_username)
        user_id = user_info['user']['pk']
        rank_token = str(uuid.uuid4())
        followers = api.user_followers(user_id, rank_token=rank_token)
        return followers
    except Exception as e:
        print(f"Error: {e}")
        return {}


def get_own_bio_text():
    try:
        user_info = api.current_user()
        bio = user_info.get('user', {}).get('biography', '')
        return bio
    except Exception as e:
        print(f"Error: {e}")
        return ''


def get_instagram_bio(target_username):
    try:
        user_info = api.username_info(target_username)
        bio = user_info.get('user', {}).get('biography', '')
        return bio
    except Exception as e:
        print(f"Error: {e}")
        return ''


def get_own_post_count():
    try:
        user_info = api.current_user()
        post_count = user_info.get('user', {}).get('media_count', 0)
        return post_count
    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_own_profile_pic_url():
    try:
        user_info = api.current_user()
        profile_pic_url = user_info.get('user', {}).get('hd_profile_pic_url_info', {}).get('url', '')
        return profile_pic_url
    except Exception as e:
        print(f"Error: {e}")
        return ''


def get_profile_pic_url_of_user(target_username):
    try:
        user_info = api.username_info(target_username)
        profile_pic_url = user_info.get('user', {}).get('hd_profile_pic_url_info', {}).get('url', '')
        return profile_pic_url
    except Exception as e:
        print(f"Error: {e}")
        return ''


def get_full_name_of_user(target_username):
    try:
        user_info = api.username_info(target_username)
        full_name = user_info.get('user', {}).get('full_name', '')
        return full_name
    except Exception as e:
        print(f"Error: {e}")
        return ''


def is_user_verified(target_username):
    try:
        user_info = api.username_info(target_username)
        return user_info.get('user', {}).get('is_verified', False)
    except Exception as e:
        print(f"Error: {e}")
        return False


def is_user_private(target_username):
    try:
        user_info = api.username_info(target_username)
        return user_info.get('user', {}).get('is_private', False)
    except Exception as e:
        print(f"Error: {e}")
        return False


# -----------------------Fetch Data Methods-------------------


def download_profile_picture(url, filename='profile_pic.jpg'):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"Profile picture saved as '{filename}'")
        else:
            print(f"Failed to download image. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error downloading profile picture: {e}")


def save_followers_snapshot(time_interval):
    try:
        followers = get_own_followers()
        data = {
            'timestamp': datetime.now().isoformat(),
            'followers': followers
        }
        filename = f"followers_{time_interval}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Saved snapshot as '{filename}'")
    except Exception as e:
        print(f"Error saving followers snapshot: {e}")


def compare_followers(snapshot1_path, snapshot2_path):
    try:
        with open(snapshot1_path) as f1, open(snapshot2_path) as f2:
            data1 = json.load(f1)
            data2 = json.load(f2)

        followers1 = set(data1['followers'])
        followers2 = set(data2['followers'])

        new_followers = followers2 - followers1
        lost_followers = followers1 - followers2

        return {
            'new_followers': list(new_followers),
            'lost_followers': list(lost_followers)
        }
    except Exception as e:
        print(f"Error comparing snapshots: {e}")
        return {}


# Testing the methods-------------------------------------------
my_followers = get_followers(username)
# for user in my_followers['users']:
#   print(user['username'], '-', user['full_name'])
print(is_user_private("og.byg"))


# --------------------------------------------------------------
# Connecting backend to front
@app.route('/call_server', methods=['POST'])
def call_server():
    return jsonify({'result': "HELLO FROM SERVER"})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8020)
