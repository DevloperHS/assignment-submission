"""Sends redirect events to the external analytics service."""
import json
import urllib.request

from . import config


def track_redirect(code, user_agent, referrer):
    try:
        payload = json.dumps({"event": "redirect", "code": code, "ua": user_agent, "ref": referrer})
        req = urllib.request.Request(
            config.ANALYTICS_ENDPOINT,
            data=payload.encode(),
            headers={"Authorization": "Bearer " + config.ANALYTICS_API_KEY, "Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except:
        pass


def get_daily_report(date):
    try:
        resp = urllib.request.urlopen(config.ANALYTICS_ENDPOINT + "/report?date=" + date)
        data = json.loads(resp.read())
        return data["rows"]
    except Exception as e:
        print(e)
        return []
