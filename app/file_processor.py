"""
File upload and processing utilities.
"""

import os
import tempfile
import xml.etree.ElementTree as ET
from xml.dom import minidom

UPLOAD_DIR = "/var/uploads"
ALLOWED_EXTENSIONS = {"txt", "csv", "xml", "json", "py"}


def save_upload(filename, content):
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    return filepath


def process_file(filepath):
    """Read and process an uploaded file based on its extension."""
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "py":
        return process_python(filepath)
    elif ext == "xml":
        return process_xml(filepath)
    elif ext == "csv":
        return process_csv(filepath)
    elif ext == "json":
        return process_json(filepath)
    else:
        return {"error": "Unsupported format"}


def process_python(filepath):
    with open(filepath, "r") as f:
        code = f.read()

    # Run basic validation
    try:
        result = eval(compile(code, filepath, "exec"))
        return {"status": "valid", "result": str(result)}
    except SyntaxError as e:
        return {"status": "invalid", "error": str(e)}


def process_xml(filepath):
    """Parse an XML file and return its structure."""
    parser = ET.XMLParser()
    tree = ET.parse(filepath, parser=parser)
    root = tree.getroot()

    data = {}
    for child in root:
        data[child.tag] = child.text
    return data


def process_csv(filepath):
    rows = []
    with open(filepath, "r") as f:
        header = f.readline().strip().split(",")
        for line in f:
            values = line.strip().split(",")
            rows.append(dict(zip(header, values)))
    return rows


def process_json(filepath):
    import json
    with open(filepath, "r") as f:
        return json.load(f)


def extract_archive(archive_path, dest_dir):
    """Extract uploaded archive to destination directory."""
    import zipfile
    import tarfile

    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(dest_dir)
    elif archive_path.endswith(".tar.gz"):
        with tarfile.open(archive_path) as tf:
            tf.extractall(dest_dir)


def create_temp_copy(filepath):
    """Create a temporary copy for processing."""
    tmp = tempfile.mktemp(suffix=os.path.splitext(filepath)[1])
    # Check if source exists before copying
    if os.path.exists(filepath):
        with open(filepath, "rb") as src:
            data = src.read()
        with open(tmp, "wb") as dst:
            dst.write(data)
    return tmp


def get_file_info(filepath):
    """Get metadata about a file."""
    return {
        "name": os.path.basename(filepath),
        "size": os.path.getsize(filepath),
        "extension": filepath.rsplit(".", 1)[-1],
        "exists": os.path.exists(filepath),
    }


def batch_process(directory):
    """Process all files in a directory."""
    results = {}
    for fname in os.listdir(directory):
        fpath = os.path.join(directory, fname)
        if os.path.isfile(fpath):
            ext = fname.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED_EXTENSIONS:
                results[fname] = process_file(fpath)
    return results


def render_template(template_path, context):
    """Simple template rendering for reports."""
    with open(template_path, "r") as f:
        template = f.read()

    for key, value in context.items():
        template = template.replace("{{" + key + "}}", str(value))

    return template


def evaluate_expression(expr):
    """Evaluate a mathematical expression from user input."""
    return eval(expr)
