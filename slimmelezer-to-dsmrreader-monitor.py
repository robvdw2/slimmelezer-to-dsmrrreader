#!/usr/bin/env python3
from datetime import datetime, timezone, timedelta
import requests
from urllib3.exceptions import InsecureRequestWarning
import json
import subprocess
import config

# Ignore warnings when using self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Only request latest reading
params = {'ordering': '-read_at', 'limit': 1}
headers = {'X-AUTHKEY': f'{config.API_KEY}'}

try:
    response = requests.get(config.MONITOR_URL, headers=headers, params=params, verify=False, timeout=10)
    content = json.loads(response.content)
    timestamp = datetime.fromisoformat(content['results'][0]['read_at'])
    now = datetime.now(timezone.utc)
    delta = now - timestamp
    if delta > timedelta(seconds=config.MONITOR_TIMEOUT):
        print(now.strftime('%Y-%m-%dT%H:%M:%SZ') + " monitor detected old data ("+str(round(delta.total_seconds()))+"s), restarting service")
        subprocess.run(["systemctl", "restart", "slimmelezer-to-dsmrreader.service"])
except Exception as e:
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f"{ts} Error: {e}")
