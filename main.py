import json
import codecs
import uuid
import requests
import os
from flask import Flask, jsonify, request
from datetime import datetime
from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError, ClientCompatPatch)


app = Flask(__name__)


# -----------------------Set up private API and Avoid re-login----------------------
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


SESSION_FOLDER = "sessions"  # folder to store session files

if not os.path.exists(SESSION_FOLDER):
    os.makedirs(SESSION_FOLDER)

api: Client = None
settings_file = "settings.json"


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    # generate token
    token = str(uuid.uuid4())
    settings_file = os.path.join(SESSION_FOLDER, f"settings_{token}.json")

    device_id = None

    try:
        api = Client(
            username,
            password,
            on_login=lambda x: on_login_callback(x, settings_file)
        )
    except (ClientLoginError, ClientCookieExpiredError, ClientLoginRequiredError) as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ClientError as e:
        return jsonify({"status": "error", "message": e.msg}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    # success
    cookie_expiry = api.cookie_jar.auth_expires
    expiry_str = datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')

    return jsonify({
        "status": "success",
        "message": f"Logged in as {username}",
        "token": token,
        "cookie_expiry": expiry_str
    })


# -----------------------Set up private API and Avoid re-login----------------------


# -----------------------UTILITY: Get API from token-----------------------
def get_api_from_token(token):
    settings_file = os.path.join(SESSION_FOLDER, f"settings_{token}.json")
    if not os.path.isfile(settings_file):
        raise Exception("Invalid or expired token")

    with open(settings_file) as file_data:
        cached_settings = json.load(file_data, object_hook=from_json)

    # username = cached_settings.get('username_id')  # optional log
    # device_id = cached_settings.get('device_id')

    api = Client(
        None, None,  # username/password not needed
        settings=cached_settings
    )
    return api


# -----------------------Fetch Data Methods-------------------
@app.route("/get_own_number_of_followers", methods=["POST"])
def get_own_number_of_followers():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        number_of_followers = user_info['user']['follower_count']
        return jsonify({
            "status": "success",
            "follower_count": number_of_followers
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_number_of_followers", methods=["POST"])
def get_number_of_followers():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        number_of_followers = user_info['user']['follower_count']
        return jsonify({
            "status": "success",
            "follower_count": number_of_followers
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_number_of_following", methods=["POST"])
def get_own_number_of_following():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        number_of_following = user_info['user']['following_count']
        return jsonify({
            "status": "success",
            "following_count": number_of_following
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_number_of_following", methods=["POST"])
def get_number_of_following():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        number_of_following = user_info['user']['following_count']
        return jsonify({
            "status": "success",
            "following_count": number_of_following
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_followers", methods=["POST"])
def get_own_followers():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        followers = []
        results = api.followers(api.authenticated_user_id)
        for user in results.get('users', []):
            followers.append(user['username'])
        return jsonify({
            "status": "success",
            "followers": followers
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_followers", methods=["POST"])
def get_followers():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        target_user = api.username_info(target_username)
        target_user_id = target_user['user']['pk']

        followers = []
        results = api.followers(target_user_id)
        for user in results.get('users', []):
            followers.append(user['username'])

        return jsonify({
            "status": "success",
            "followers": followers
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_bio", methods=["POST"])
def get_own_bio():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400

    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        bio = user_info['user']['biography']
        return jsonify({
            "status": "success",
            "bio": bio
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_bio", methods=["POST"])
def get_bio():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        bio = user_info['user']['biography']
        return jsonify({
            "status": "success",
            "bio": bio
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_post_count", methods=["POST"])
def get_own_post_count():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        post_count = user_info['user']['media_count']
        return jsonify({
            "status": "success",
            "post_count": post_count
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_post_count", methods=["POST"])
def get_post_count():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        post_count = user_info['user']['media_count']
        return jsonify({
            "status": "success",
            "post_count": post_count
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_profile_pic_url", methods=["POST"])
def get_own_profile_pic_url():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        profile_pic_url = user_info['user']['profile_pic_url']
        return jsonify({
            "status": "success",
            "profile_pic_url": profile_pic_url
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_profile_pic_url", methods=["POST"])
def get_profile_pic_url():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        profile_pic_url = user_info['user']['profile_pic_url']
        return jsonify({
            "status": "success",
            "profile_pic_url": profile_pic_url
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_verified", methods=["POST"])
def get_own_verified():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        verified = user_info['user']['is_verified']
        return jsonify({
            "status": "success",
            "verified": verified
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_verified", methods=["POST"])
def get_verified():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        verified = user_info['user']['is_verified']
        return jsonify({
            "status": "success",
            "verified": verified
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_private", methods=["POST"])
def get_own_private():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        private = user_info['user']['is_private']
        return jsonify({
            "status": "success",
            "private": private
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_private", methods=["POST"])
def get_private():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        private = user_info['user']['is_private']
        return jsonify({
            "status": "success",
            "private": private
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_own_full_name", methods=["POST"])
def get_own_full_name():
    data = request.json
    token = data.get("token", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.current_user()
        full_name = user_info['user']['full_name']
        return jsonify({
            "status": "success",
            "full_name": full_name
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/get_full_name", methods=["POST"])
def get_full_name():
    data = request.json
    token = data.get("token", "")
    target_username = data.get("target_username", "")

    if not token:
        return jsonify({"status": "error", "message": "Token required"}), 400
    try:
        api = get_api_from_token(token)
        user_info = api.username_info(target_username)
        full_name = user_info['user']['full_name']
        return jsonify({
            "status": "success",
            "full_name": full_name
        })
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
