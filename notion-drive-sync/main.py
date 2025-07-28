"""
Google Cloud Function that syncs Notion pages to Google Drive.
"""
import functions_framework
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

from notion_client import Client as NotionClient
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO

from shared.env import (
    load_tool_env,
    get_notion_api_key,
    get_gcp_project_id,
    get_drive_folder_id
)

# Load tool-specific environment variables
load_tool_env('notion-drive-sync')

# Initialize clients
notion = NotionClient(auth=get_notion_api_key())
DRIVE_FOLDER_ID = get_drive_folder_id()

################################################################################
# Configuration
################################################################################

# ---- ENVIRONMENT VARIABLES (see .env.yaml) ----------------------------------
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_PAGE_ID = os.environ.get("NOTION_PAGE_ID")  # optional fallback
DRIVE_TXT_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "0ADh8oHDMGlVNUk9PVA")
DRIVE_GDOC_FOLDER_ID = os.environ.get("GDOC_FOLDER_ID", "0AE4_IKRqRvtYUk9PVA")
NOTION_VERIFICATION_TOKEN = os.environ.get("NOTION_VERIFICATION_TOKEN", "")

# ---- CONSTANTS ----------------------------------------------------------------
LA_TZ = pytz.timezone("America/Los_Angeles")
APP_VERSION = "6.0.0_raw_http"
USER_AGENT = f"notion-drive-sync/{APP_VERSION}"

################################################################################
# Logging – very verbose for debugging
################################################################################
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s [%(filename)s:%(lineno)d] %(message)s",
)

################################################################################
# Google credentials & token helper
################################################################################
creds, _ = google.auth.default(
    scopes=[
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]
)

def _get_access_token() -> str:
    """Return a valid OAuth2 access token string."""
    if not creds.valid or creds.expired:
        logging.debug("Refreshing Google credentials …")
        creds.refresh(GoogleRequest())
    return creds.token

################################################################################
# Notion helpers
################################################################################
notion = Client(auth=NOTION_API_KEY)

def _extract_rich_text(rt_array: List[Dict[str, Any]]) -> str:
    return "".join(span.get("plain_text", "") for span in (rt_array or []))

def _extract_title(page: Dict[str, Any]) -> str:
    for k in ["Title", "Name", "title", "name"]:
        prop = page.get("properties", {}).get(k)
        if prop and prop.get("type") == "title":
            return _extract_rich_text(prop.get("title", [])) or "Untitled"
    return f"Untitled_{page['id'][:8]}"

################################################################################
# Drive upload helpers (raw HTTP)
################################################################################

_DRIVE_UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
_DRIVE_FILES = "https://www.googleapis.com/drive/v3/files"


def _multipart_request(metadata: Dict[str, Any], filepath: str, mimetype: str) -> requests.Response:
    token = _get_access_token()
    boundary = "===============sync_part_boundary=="

    with open(filepath, "rb") as fh:
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(metadata)}\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: {mimetype}\r\n\r\n"
        ).encode("utf-8") + fh.read() + f"\r\n--{boundary}--".encode("utf-8")

    params = {"uploadType": "multipart", "supportsAllDrives": "true"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": f"multipart/related; boundary={boundary}",
        "User-Agent": USER_AGENT,
    }
    logging.debug(f"Uploading file metadata={metadata} size={len(body)} bytes")
    return requests.post(_DRIVE_UPLOAD, params=params, headers=headers, data=body, timeout=900)


def create_drive_file(
    name: str,
    folder_id: str,
    filepath: str,
    mimetype: str,
    convert_to_gdoc: bool = False,
) -> str:
    metadata = {"name": name, "parents": [folder_id]}
    if convert_to_gdoc:
        metadata["mimeType"] = "application/vnd.google-apps.document"
    resp = _multipart_request(metadata, filepath, mimetype)
    if not resp.ok:
        logging.error("Drive upload failed: %s", resp.text)
        resp.raise_for_status()
    file_id = resp.json()["id"]
    logging.info("Created Drive file %s (%s)", name, file_id)
    return file_id

################################################################################
# Content generators
################################################################################

def convert_to_la(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(LA_TZ).strftime("%B %d, %Y %I:%M %p PT")


def fetch_all_blocks(page_id: str, start_cursor: Optional[str] = None) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    while True:
        res = notion.blocks.children.list(block_id=page_id, start_cursor=start_cursor)
        blocks += res["results"]
        if not res.get("has_more"):
            break
        start_cursor = res.get("next_cursor")
    for blk in blocks:
        if blk.get("has_children"):
            blk["children"] = fetch_all_blocks(blk["id"])
    return blocks


def blocks_to_plaintext(blocks: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for blk in blocks:
        typ = blk["type"]
        content = _extract_rich_text(blk[typ].get("rich_text", [])) if typ != "divider" else "---"
        if typ.startswith("heading_"):
            lines.append(content.upper())
        elif typ == "bulleted_list_item":
            lines.append(f"- {content}")
        elif typ == "numbered_list_item":
            lines.append(f"1. {content}")
        elif typ == "quote":
            lines.append(f"> {content}")
        elif typ == "code":
            lines.append(content)
        elif typ == "divider":
            lines.append("\n---\n")
        else:  # paragraph or others
            lines.append(content)
        if blk.get("children"):
            lines.append(blocks_to_plaintext(blk["children"]))
    return "\n".join(lines)


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&#39;")
    )


def blocks_to_html(blocks: List[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for blk in blocks:
        typ = blk["type"]
        if typ == "paragraph":
            parts.append(f"<p>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</p>")
        elif typ == "heading_1":
            parts.append(f"<h1>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</h1>")
        elif typ == "heading_2":
            parts.append(f"<h2>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</h2>")
        elif typ == "heading_3":
            parts.append(f"<h3>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</h3>")
        elif typ == "bulleted_list_item":
            parts.append(f"<ul><li>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</li></ul>")
        elif typ == "numbered_list_item":
            parts.append(f"<ol><li>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</li></ol>")
        elif typ == "code":
            parts.append(f"<pre><code>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</code></pre>")
        elif typ == "quote":
            parts.append(f"<blockquote>{html_escape(_extract_rich_text(blk[typ]['rich_text']))}</blockquote>")
        elif typ == "divider":
            parts.append("<hr />")
        if blk.get("children"):
            parts.append(blocks_to_html(blk["children"]))
    return "\n".join(parts)


def _extract_property_value(prop: Dict[str, Any]) -> Optional[str]:
    """Extract a readable string value from any Notion property type."""
    if not prop:
        return None
    
    prop_type = prop.get("type")
    if not prop_type:
        return None
    
    try:
        if prop_type == "title":
            return _extract_rich_text(prop.get("title", []))
        elif prop_type == "rich_text":
            return _extract_rich_text(prop.get("rich_text", []))
        elif prop_type == "number":
            num = prop.get("number")
            return str(num) if num is not None else None
        elif prop_type == "select":
            sel = prop.get("select")
            return sel.get("name") if sel else None
        elif prop_type == "multi_select":
            items = prop.get("multi_select", [])
            return ", ".join(item.get("name", "") for item in items) if items else None
        elif prop_type == "date":
            date_obj = prop.get("date")
            if not date_obj:
                return None
            start = date_obj.get("start")
            end = date_obj.get("end")
            if end:
                return f"{start} to {end}"
            return start
        elif prop_type == "checkbox":
            return "Yes" if prop.get("checkbox") else "No"
        elif prop_type == "url":
            return prop.get("url")
        elif prop_type == "email":
            return prop.get("email")
        elif prop_type == "phone_number":
            return prop.get("phone_number")
        elif prop_type == "people":
            people = prop.get("people", [])
            names = []
            for person in people:
                name = person.get("name") or person.get("id", "Unknown")
                names.append(name)
            return ", ".join(names) if names else None
        elif prop_type == "files":
            files = prop.get("files", [])
            file_names = []
            for file_obj in files:
                name = file_obj.get("name")
                if name:
                    file_names.append(name)
                elif file_obj.get("file"):
                    # External file
                    url = file_obj.get("file", {}).get("url", "")
                    file_names.append(url.split("/")[-1] if url else "Unnamed file")
            return ", ".join(file_names) if file_names else None
        elif prop_type == "formula":
            formula = prop.get("formula", {})
            formula_type = formula.get("type")
            if formula_type == "string":
                return formula.get("string")
            elif formula_type == "number":
                num = formula.get("number")
                return str(num) if num is not None else None
            elif formula_type == "boolean":
                return "Yes" if formula.get("boolean") else "No"
            elif formula_type == "date":
                date_obj = formula.get("date")
                return date_obj.get("start") if date_obj else None
        elif prop_type == "relation":
            relations = prop.get("relation", [])
            return f"{len(relations)} related items" if relations else None
        elif prop_type == "rollup":
            rollup = prop.get("rollup", {})
            rollup_type = rollup.get("type")
            if rollup_type == "number":
                num = rollup.get("number")
                return str(num) if num is not None else None
            elif rollup_type == "array":
                array = rollup.get("array", [])
                return f"{len(array)} items" if array else None
        elif prop_type == "created_time":
            return convert_to_la(datetime.fromisoformat(prop.get("created_time", "").replace("Z", "+00:00")))
        elif prop_type == "last_edited_time":
            return convert_to_la(datetime.fromisoformat(prop.get("last_edited_time", "").replace("Z", "+00:00")))
        elif prop_type == "created_by":
            user = prop.get("created_by", {})
            return user.get("name") or user.get("id", "Unknown")
        elif prop_type == "last_edited_by":
            user = prop.get("last_edited_by", {})
            return user.get("name") or user.get("id", "Unknown")
        elif prop_type == "status":
            status = prop.get("status")
            return status.get("name") if status else None
    
    except Exception as e:
        logging.warning(f"Error extracting property {prop_type}: {e}")
        return None
    
    return None


def build_metadata(page: Dict[str, Any]) -> List[str]:
    """Extract comprehensive metadata from Notion page including all properties."""
    page_id = page["id"]
    title = _extract_title(page)
    now_str = convert_to_la(datetime.utcnow())
    
    metadata_lines = [
        f"Title: {title}",
        f"Notion Page ID: {page_id}",
        f"Last Synced: {now_str}",
    ]
    
    # Extract all properties
    properties = page.get("properties", {})
    if properties:
        metadata_lines.append("")  # Empty line separator
        metadata_lines.append("== Page Properties ==")
        
        for prop_name, prop_data in properties.items():
            # Skip the title property as it's already included
            if prop_data.get("type") == "title":
                continue
                
            prop_value = _extract_property_value(prop_data)
            if prop_value and prop_value.strip():  # Only include non-empty properties
                # Clean up property name for display
                display_name = prop_name.replace("_", " ").title()
                metadata_lines.append(f"{display_name}: {prop_value}")
    
    # Add page-level metadata
    metadata_lines.append("")  # Empty line separator
    metadata_lines.append("== Page Info ==")
    
    if page.get("created_time"):
        created = convert_to_la(datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")))
        metadata_lines.append(f"Created: {created}")
    
    if page.get("last_edited_time"):
        edited = convert_to_la(datetime.fromisoformat(page["last_edited_time"].replace("Z", "+00:00")))
        metadata_lines.append(f"Last Edited: {edited}")
    
    if page.get("created_by"):
        creator = page["created_by"].get("name") or page["created_by"].get("id", "Unknown")
        metadata_lines.append(f"Created By: {creator}")
    
    if page.get("last_edited_by"):
        editor = page["last_edited_by"].get("name") or page["last_edited_by"].get("id", "Unknown")
        metadata_lines.append(f"Last Edited By: {editor}")
    
    if page.get("url"):
        metadata_lines.append(f"Notion URL: {page['url']}")
    
    metadata_lines.append("---")
    return metadata_lines


def assemble_html(metadata_lines: List[str], blocks: List[Dict[str, Any]]) -> str:
    body_meta = "\n".join(f"<p>{html_escape(line)}</p>" for line in metadata_lines if line != "---")
    style = (
        "body{font-family:Arial,Helvetica,sans-serif;line-height:1.6;padding:20px;max-width:800px;margin:auto;}"  # noqa: E501
        "h1,h2,h3{font-weight:bold;}pre{background:#f0f0f0;padding:10px;}blockquote{border-left:3px solid #ccc;padding-left:15px;color:#555;}"  # noqa: E501
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>" + html_escape(metadata_lines[0]) + "</title>"
        f"<style>{style}</style></head><body><div class='metadata'>{body_meta}</div>"
        + blocks_to_html(blocks)
        + "</body></html>"
    )

################################################################################
# Utility
################################################################################

def sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in " ._-()")[:200]

################################################################################
# Cloud Function entry point
################################################################################

@functions_framework.http
def sync_notion_to_drive(request):
    logging.info("\n=========== New Sync Request (v%s) ===========", APP_VERSION)

    # ------------------------------------------------------------------
    # Webhook validation (optional)
    # ------------------------------------------------------------------
    if NOTION_VERIFICATION_TOKEN:
        sig = request.headers.get("X-Notion-Signature", "")
        if sig != NOTION_VERIFICATION_TOKEN:
            logging.warning("Signature mismatch – ignoring request")
            return ("invalid signature", 200)  # never error to Notion

    try:
        payload = request.get_json(silent=True) or {}
        logging.debug("Incoming payload: %s", payload)
    except Exception:
        payload = {}

    # Allow override via payload.page.id else fallback to env var
    page_id = (
        payload.get("page", {}).get("id")
        or payload.get("id")
        or NOTION_PAGE_ID
    )
    if not page_id:
        return ("No page_id provided", 200)

    page_id = page_id.replace("-", "")  # Notion API expects stripped id

    # ===================================================================
    # IMMEDIATELY RETURN SUCCESS TO PREVENT NOTION TIMEOUT
    # ===================================================================
    import threading
    
    def _perform_sync():
        """Background sync operation"""
        try:
            logging.debug("Background sync started for page %s", page_id)
            page = notion.pages.retrieve(page_id)
            title = _extract_title(page)
            blocks = fetch_all_blocks(page_id)
            metadata_lines = build_metadata(page)

            # ----------------------------- TXT -----------------------------
            txt_content = "\n".join(metadata_lines) + "\n\n" + blocks_to_plaintext(blocks)
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as tf:
                tf.write(txt_content)
                txt_path = tf.name
            create_drive_file(
                f"{sanitize(title)}.txt",
                DRIVE_TXT_FOLDER_ID,
                txt_path,
                "text/plain",
                convert_to_gdoc=False,
            )

            # ----------------------------- GDOC ----------------------------
            html_str = assemble_html(metadata_lines, blocks)
            with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as hf:
                hf.write(html_str)
                html_path = hf.name
            gdoc_id = create_drive_file(
                sanitize(title),
                DRIVE_GDOC_FOLDER_ID,
                html_path,
                "text/html",
                convert_to_gdoc=True,
            )
            doc_url = f"https://docs.google.com/document/d/{gdoc_id}/edit"

            logging.info("Background sync completed – page '%s' => %s", title, doc_url)

        except Exception as exc:
            logging.exception("Background sync failed: %s", exc)

    # Start background sync
    sync_thread = threading.Thread(target=_perform_sync)
    sync_thread.daemon = False  # Ensure thread completes even after response is sent
    sync_thread.start()

    # Return immediate success response to Notion
    logging.info("Returning immediate success response to prevent Notion timeout")
    return (
        json.dumps({
            "status": "started", 
            "message": "Sync started successfully! Please wait 10-30 seconds for the documents to appear in your Drive folders. Check your Google Drive for the updated files."
        }),
        200,
        {"Content-Type": "application/json"},
    )