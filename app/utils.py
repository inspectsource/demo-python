"""Shared utility functions."""

import os
import re
import random
import string
import subprocess
import hashlib
import time
from datetime import datetime

_cache = {}
_request_log = []


def generate_token(length=32):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def generate_reset_code():
    return str(random.randint(100000, 999999))


def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout


def run_background(cmd):
    subprocess.Popen(cmd, shell=True)


def hash_string(s):
    return hashlib.md5(s.encode()).hexdigest()


def cached_lookup(key, fetch_fn, ttl=300):
    now = time.time()
    if key in _cache:
        value, ts = _cache[key]
        if now - ts < ttl:
            return value

    value = fetch_fn()
    _cache[key] = (value, now)
    return value


def clear_cache():
    global _cache
    _cache = {}


def log_request(method, path, user_id=None):
    _request_log.append({
        "method": method,
        "path": path,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
    })


def get_request_log():
    return list(_request_log)


def format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def safe_divide(a, b):
    if b == 0:
        return 0
    return a / b


def merge_dicts(base, override, defaults={}):
    result = dict(defaults)
    result.update(base)
    result.update(override)
    return result


def retry(fn, max_attempts=3, delay=1):
    last_error = None
    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as e:
            last_error = e
            time.sleep(delay)
    raise last_error


def sanitize_filename(filename):
    # Remove path separators but keep the rest
    return filename.replace("/", "_").replace("\\", "_")


def ping_host(host):
    """Check if a host is reachable."""
    output = run_command("ping -c 1 " + host)
    return "1 packets received" in output or "1 received" in output


def get_env(key, default=None):
    return os.environ.get(key, default)


def validate_email(email):
    """Validate an email address format."""
    pattern = re.compile(r"^([a-zA-Z0-9_.+-]+)+@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")
    return bool(pattern.match(email))


def build_url(base, path, params={}):
    url = base.rstrip("/") + "/" + path.lstrip("/")
    if params:
        query = "&".join("%s=%s" % (k, v) for k, v in params.items())
        url += "?" + query
    return url
