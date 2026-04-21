"""
upload_gdrive.py
────────────────
Upload the final video to Google Drive using a Service Account.
Uses YOUR existing Google One storage (from Jio) — no extra cost.

Setup (one-time, takes ~5 minutes):
1. Go to https://console.cloud.google.com
2. Create a project (or use existing)
3. Enable "Google Drive API"
4. Create a Service Account (IAM → Service Accounts → Create)
5. Download the JSON key file
6. Share your Google Drive folder with the service account email
7. Add the JSON contents as GitHub Secret: GDRIVE_CREDENTIALS
8. Add your folder ID as GitHub Secret: GDRIVE_FOLDER_ID
   (Folder ID = the part after /folders/ in the Drive URL)
"""

import os
import json
import sys
from pathlib import Path

VIDEO_PATH = "output/final_video.mp4"
GDRIVE_LINK_FILE = "output/gdrive_link.txt"


def upload_to_drive(
    file_path: str,
    folder_id: str,
    credentials_json: str,
) -> tuple[str, str] | None:
    """
    Upload a file to Google Drive.

    Returns:
        (file_id, web_view_link) on success, None on failure.
    """
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("❌ Google API libraries not installed. Run: pip install google-api-python-client google-auth")
        return None

    # Parse credentials
    try:
        creds_dict = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid GDRIVE_CREDENTIALS JSON: {e}")
        return None

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.file"],
    )

    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    # Build file name: timestamp + topic snippet
    filename = Path(file_path).name

    file_metadata = {
        "name": filename,
        "parents": [folder_id] if folder_id else [],
    }

    media = MediaFileUpload(
        file_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5 MB chunks
    )

    print(f"☁️  Uploading {filename} to Google Drive...")
    request = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id,webViewLink,name",
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   📤 Upload progress: {int(status.progress() * 100)}%")

    file_id = response.get("id")
    link = response.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view")

    print(f"✅ Uploaded to Google Drive!")
    print(f"   📎 Link: {link}")
    return file_id, link


def main():
    credentials_json = os.environ.get("GDRIVE_CREDENTIALS", "")
    folder_id        = os.environ.get("GDRIVE_FOLDER_ID", "")

    if not credentials_json:
        print("⚠️  GDRIVE_CREDENTIALS secret not set — skipping Google Drive upload.")
        print("   The video is still saved as a GitHub Actions artifact (7 days).")
        sys.exit(0)

    if not os.path.exists(VIDEO_PATH):
        print(f"❌ Video not found at {VIDEO_PATH}")
        sys.exit(1)

    result = upload_to_drive(VIDEO_PATH, folder_id, credentials_json)

    if result:
        file_id, link = result
        # Save link to file so the callback step can read it
        with open(GDRIVE_LINK_FILE, "w") as f:
            f.write(link)
    else:
        print("⚠️  Google Drive upload failed. Video is still in GitHub artifact.")


if __name__ == "__main__":
    main()
