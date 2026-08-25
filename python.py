import os, time, pickle, requests
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

AUTH = os.environ.get("SLING_AUTH_TOKEN", "").strip()
UID = int(os.environ.get("SLING_USER_ID", "0"))
ORG = os.environ.get("SLING_ORG_ID", "").strip()
CAL = os.environ.get("CALENDAR_ID", "primary")
INTERVAL = int(os.environ.get("CHECK_INTERVAL_MINUTES", "60"))

EVENT_TITLE_PREFIX = os.environ.get("EVENT_TITLE_PREFIX", "Work Shift")
EVENT_COLOR_ID = os.environ.get("EVENT_COLOR_ID", "1")
EVENT_ID_PREFIX = os.environ.get("EVENT_ID_PREFIX", "wk").lower()

def get_cal():
    with open("token.pickle", "rb") as f:
        creds = pickle.load(f)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.pickle", "wb") as f:
            pickle.dump(creds, f)
    return build("calendar", "v3", credentials=creds)

def get_shifts():
    now = datetime.utcnow()
    s = (now - timedelta(days=2)).strftime("%Y-%m-%dT00:00:00-0500")
    e = (now + timedelta(days=35)).strftime("%Y-%m-%dT23:59:59-0500")
    headers = {"Authorization": AUTH, "Accept": "application/json"}
    url = f"https://api.getsling.com/v1/{ORG}/calendar/{ORG}/users/{UID}?dates={s}%2F{e}&user-fields=id"
    r = requests.get(url, headers=headers)
    raw = r.json() if r.status_code == 200 else []
    data = raw if isinstance(raw, list) else raw.get("shifts", [])
    return [item for item in data if item.get("type") == "shift" and item.get("user", {}).get("id") == UID]

def sync():
    shifts = get_shifts()
    service = get_cal()

    events = service.events().list(
        calendarId=CAL,
        timeMin=(datetime.utcnow() - timedelta(days=2)).isoformat() + "Z",
        singleEvents=True
    ).execute().get("items", [])

    existing = {
        e.get("extendedProperties", {}).get("private", {}).get("sling_id"): e["id"]
        for e in events
        if "extendedProperties" in e and "private" in e["extendedProperties"]
    }

    active_ids = set()
    for s in shifts:
        sid, dt_s, dt_e = str(s.get("id")), s.get("dtstart"), s.get("dtend")
        if not dt_s or not dt_e: continue
        active_ids.add(sid)

        pos = s.get("position", {}).get("name") if isinstance(s.get("position"), dict) else None
        clean_sid = "".join([c for c in str(sid).lower() if c in "abcdefghijklmnopqrstuv0123456789"])
        event_id = EVENT_ID_PREFIX + clean_sid

        body = {
            "summary": f"{EVENT_TITLE_PREFIX} - {pos}" if pos else EVENT_TITLE_PREFIX,
            "description": s.get("summary", "") or s.get("notes", ""),
            "start": {"dateTime": dt_s},
            "end": {"dateTime": dt_e},
            "colorId": EVENT_COLOR_ID,
            "id": event_id,
            "extendedProperties": {"private": {"sling_id": sid}}
        }

        if sid in existing:
            service.events().update(calendarId=CAL, eventId=existing[sid], body=body).execute()
        else:
            service.events().import_(calendarId=CAL, body=body).execute()
            print(f"Synced shift: {dt_s}")

    for sid, gid in existing.items():
        if sid not in active_ids:
            try:
                service.events().delete(calendarId=CAL, eventId=gid).execute()
                print(f"Removed deleted shift: {sid}")
            except HttpError:
                pass

if __name__ == "__main__":
    while True:
        try:
            sync()
            print(f"{EVENT_TITLE_PREFIX} sync check complete.")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(INTERVAL * 60)