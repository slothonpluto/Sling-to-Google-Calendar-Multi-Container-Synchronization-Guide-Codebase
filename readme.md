# Sling to Google Calendar Docker Sync

This project automatically synchronizes work shifts from the [Sling](https://getsling.com/) scheduling app directly into your Google Calendar. It runs as a lightweight Docker container in the background and checks for new, updated, or deleted shifts.

## Features
* **Multi-Job Support:** Run multiple containers to sync different jobs or organizations.
* **Auto-Updates & Deletions:** If a shift time changes or is removed in Sling, it automatically updates in Google Calendar.
* **Customizable Colors:** Tag your shifts with specific Google Calendar colors.
* **No Duplicates:** Uses deterministic Google Calendar event IDs to prevent duplicate shifts.

## Setup Instructions
1. Clone this repository.
2. Obtain your `credentials.json` from the [Google Cloud Console](https://console.cloud.google.com/) (Google Calendar API enabled).
3. Generate your initial `token.pickle` by running the Google OAuth flow locally once.
4. Get your Sling API Token, User ID, and Organization ID by inspecting the web traffic on the Sling dashboard.
5. Create a directory for your job (e.g., `./data/job1/`) and place `token.pickle` inside it.
6. Edit the variables in `docker-compose.yml` to match your IDs and preferences.
7. Run `docker-compose up -d --build`.