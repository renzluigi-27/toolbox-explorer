"""
Toolbox Finder - Search indexer
Created by Renz Luigi - renzluigi.pages.dev

Builds a local SQLite FTS5 index of filenames + file contents
(xlsx, docx, pdf) under a chosen folder scope. Manual re-index only
(no background file watching, keeps it lightweight).

Requires: openpyxl, python-docx, pdfplumber
    pip install openpyxl python-docx pdfplumber
"""

import os
import sqlite3

try:
    import openpyxl
except ImportError:
    openpyxl = None

try:
    import docx
except ImportError:
    docx = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


DB_NAME = "toolbox_finder_index.sqlite3"
INDEXABLE_EXTENSIONS = {".xlsx", ".xlsm", ".docx", ".pdf"}
MAX_CONTENT_CHARS = 200_000  # cap per file, avoids huge files ballooning the index


def get_db_path():
    # store the index next to the script/exe, in a hidden-ish folder
    base_dir = os.path.join(os.path.expanduser("~"), ".toolbox_finder")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, DB_NAME)


def init_db():
    conn = sqlite3.connect(get_db_path())
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS file_index USING fts5(
            filename, path, content, matched_in
        )
    """)
    conn.commit()
    return conn


def extract_xlsx_text(path):
    if not openpyxl:
        return ""
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        chunks = []
        for sheet in wb.worksheets:
            for row in sheet.iter_rows(values_only=True):
                for cell in row:
                    if cell is not None:
                        chunks.append(str(cell))
        wb.close()
        return " ".join(chunks)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def extract_docx_text(path):
    if not docx:
        return ""
    try:
        d = docx.Document(path)
        text = " ".join(p.text for p in d.paragraphs)
        return text[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def extract_pdf_text(path):
    if not pdfplumber:
        return ""
    try:
        chunks = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    chunks.append(text)
        return " ".join(chunks)[:MAX_CONTENT_CHARS]
    except Exception:
        return ""


def extract_content(path, ext):
    if ext in (".xlsx", ".xlsm"):
        return extract_xlsx_text(path)
    if ext == ".docx":
        return extract_docx_text(path)
    if ext == ".pdf":
        return extract_pdf_text(path)
    return ""


def build_index(scope_path, progress_callback=None, cancel_event=None):
    """
    Scans scope_path recursively, indexes filenames for everything
    and content for supported types. progress_callback(current, total, filename)
    is called on every file, for a progress bar + status text.
    cancel_event: optional threading.Event - if set, stops indexing early
    and commits whatever was indexed so far.
    """
    conn = init_db()
    conn.execute("DELETE FROM file_index WHERE path LIKE ?", (scope_path + "%",))

    # quick pre-pass just to count files, so we can show "X / total"
    total = 0
    for root, dirs, files in os.walk(scope_path):
        total += len(files)

    count = 0
    cancelled = False
    for root, dirs, files in os.walk(scope_path):
        if cancel_event and cancel_event.is_set():
            cancelled = True
            break

        for name in files:
            if cancel_event and cancel_event.is_set():
                cancelled = True
                break

            full_path = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()

            content = ""
            matched_in = "filename"
            if ext in INDEXABLE_EXTENSIONS:
                content = extract_content(full_path, ext)
                if content:
                    matched_in = "filename+content"

            conn.execute(
                "INSERT INTO file_index (filename, path, content, matched_in) VALUES (?, ?, ?, ?)",
                (name, full_path, content, matched_in),
            )

            count += 1
            if progress_callback:
                progress_callback(count, total, name)

    conn.commit()
    conn.close()
    return count, cancelled


def search(query, scope_path=None):
    """
    Word-by-word AND search across filename + content.
    Returns list of dicts: filename, path, snippet, match_type
    """
    conn = init_db()

    # FTS5 default is AND between terms - matches Windows Search behavior
    words = query.strip().split()
    if not words:
        return []
    fts_query = " ".join(f'"{w}"' for w in words)

    sql = """
        SELECT filename, path, snippet(file_index, 2, '[', ']', '...', 10), matched_in
        FROM file_index
        WHERE file_index MATCH ?
    """
    params = [fts_query]

    if scope_path:
        sql += " AND path LIKE ?"
        params.append(scope_path + "%")

    sql += " LIMIT 200"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    results = []
    for filename, path, snippet, matched_in in rows:
        results.append({
            "filename": filename,
            "path": path,
            "snippet": snippet,
            "matched_in": matched_in,
        })
    return results
