"""只改元数据块，保留原压缩图像、动画与工作流数据。"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import tempfile
import zlib
import xml.etree.ElementTree as ET
from pathlib import Path

from .recording import VERSION

KEY = "comfyui_browser_timing"
NS = "urn:comfyui-browser:timing:1"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
MAX_METADATA = 4 * 1024 * 1024
MAX_FILE = 512 * 1024 * 1024
ET.register_namespace("cbt", NS)


def fingerprint(path):
    p = Path(path)
    stat = p.stat()
    digest = hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    after = p.stat()
    if (stat.st_size, stat.st_mtime_ns, stat.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError("file_changed")
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "inode": stat.st_ino, "sha256": digest.hexdigest()}


def load_bytes(path):
    if Path(path).stat().st_size > MAX_FILE:
        raise ValueError("container_size_limit")
    return Path(path).read_bytes()


def chunks(data):
    png = data.startswith(b"\x89PNG\r\n\x1a\n")
    webp = data[:4] == b"RIFF" and data[8:12] == b"WEBP"
    if not png and not webp:
        raise ValueError("unsupported_container")
    if webp and len(data) != struct.unpack_from("<I", data, 4)[0] + 8:
        raise ValueError("invalid_riff_size")
    pos = 8 if png else 12
    result = []
    while pos < len(data):
        start = pos
        if pos + 8 > len(data):
            raise ValueError("truncated_chunk")
        if png:
            size, kind = struct.unpack_from(">I4s", data, pos)
            pos += 8
            end = pos + size
            if end + 4 > len(data) or zlib.crc32(kind + data[pos:end]) & 0xffffffff != struct.unpack_from(">I", data, end)[0]:
                raise ValueError("invalid_png_crc")
            payload = data[pos:end]
            pos = end + 4
        else:
            kind, size = struct.unpack_from("<4sI", data, pos)
            pos += 8
            payload = data[pos:pos + size]
            pos += size + (size % 2)
            if pos > len(data):
                raise ValueError("truncated_riff_chunk")
        result.append((kind, payload, data[start:pos]))
    if png and (not result or result[0][0] != b"IHDR" or result[-1][0] != b"IEND"):
        raise ValueError("invalid_png_structure")
    return "PNG" if png else "WEBP", result


def is_timing_chunk(kind, payload):
    return kind in (b"iTXt", b"tEXt", b"zTXt") and payload.split(b"\0", 1)[0] == KEY.encode()


def xmp_root(payload):
    if len(payload) > MAX_METADATA:
        raise ValueError("unsafe_xmp")
    text = payload.decode('utf-8-sig')
    if '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError("unsafe_xmp")
    try:
        return ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError("invalid_xmp") from exc


def read_payload(data):
    fmt, items = chunks(data)
    values = []
    for kind, payload, _ in items:
        if fmt == "PNG" and is_timing_chunk(kind, payload):
            if kind != b"iTXt":
                raise ValueError("unsupported_timing_encoding")
            parts = payload.split(b"\0", 5)
            if len(parts) != 6 or parts[1] != b"" or parts[2] != b"":
                raise ValueError("unsupported_timing_encoding")
            raw = parts[5]
            if len(raw) > MAX_METADATA:
                raise ValueError("timing_size_limit")
            values.append(json.loads(raw))
        elif fmt == "WEBP" and kind == b"XMP ":
            root = xmp_root(payload)
            for node in root.iter("{" + NS + "}" + KEY):
                values.append(json.loads(node.text or "null"))
    if len(values) > 1:
        raise ValueError("duplicate_timing")
    return values[0] if values else None


def png_chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xffffffff)


def riff_chunk(kind, payload):
    return kind + struct.pack("<I", len(payload)) + payload + (b"\0" if len(payload) % 2 else b"")


def embed_bytes(data, record):
    raw = json.dumps(record, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_METADATA:
        raise ValueError("timing_size_limit")
    old = read_payload(data)
    if old is not None and (not isinstance(old, dict) or old.get("version") != VERSION):
        raise ValueError("unknown_timing_version")
    if old == record:
        return data
    fmt, items = chunks(data)
    if fmt == "PNG":
        timing = png_chunk(b"iTXt", KEY.encode() + b"\0\0\0\0\0" + raw)
        return data[:8] + b"".join((timing if kind == b"IEND" else b"") + original
                                  for kind, payload, original in items if not is_timing_chunk(kind, payload))
    xmps = [payload for kind, payload, _ in items if kind == b"XMP "]
    if len(xmps) > 1:
        raise ValueError("multiple_xmp_packets")
    root = xmp_root(xmps[0]) if xmps else ET.Element("{adobe:ns:meta/}xmpmeta")
    rdf = root.find(".//{" + RDF + "}RDF") if root.tag != "{" + RDF + "}RDF" else root
    if rdf is None:
        if xmps:
            raise ValueError("unsupported_xmp_structure")
        rdf = ET.SubElement(root, "{" + RDF + "}RDF")
    timing_parent = None
    for parent in root.iter():
        for child in list(parent):
            if child.tag == "{" + NS + "}" + KEY:
                timing_parent = parent
                parent.remove(child)
    description = timing_parent if timing_parent is not None else ET.SubElement(rdf, "{" + RDF + "}Description", {"{" + RDF + "}about": ""})
    ET.SubElement(description, "{" + NS + "}" + KEY).text = raw.decode("utf-8")
    packet = ET.tostring(root, encoding="utf-8")
    if len(packet) > MAX_METADATA:
        raise ValueError("xmp_size_limit")
    output = []
    if not any(kind == b"VP8X" for kind, _, _ in items):
        from PIL import Image
        import io
        with Image.open(io.BytesIO(data)) as im:
            width, height = im.size
            flags = 4 | (16 if "A" in im.getbands() else 0)
        extended = bytes([flags, 0, 0, 0]) + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
        output.append(riff_chunk(b"VP8X", extended))
    for kind, payload, original in items:
        if kind == b"XMP ":
            continue
        if kind == b"VP8X":
            if len(payload) != 10:
                raise ValueError("invalid_vp8x")
            output.append(riff_chunk(kind, bytes([payload[0] | 4]) + payload[1:]))
        else:
            output.append(original)
    output.append(riff_chunk(b"XMP ", packet))
    body = b"WEBP" + b"".join(output)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def preserved_chunks(data):
    fmt, items = chunks(data)
    return [original for kind, payload, original in items
            if not (is_timing_chunk(kind, payload) if fmt == "PNG" else kind in (b"XMP ", b"VP8X"))]


def write_payload(path, record, expected):
    """先验证新文件，再以文件版本为条件提交；原文件始终完整可读。"""
    path = Path(path)
    if fingerprint(path) != expected:
        raise ValueError("file_changed")
    original = load_bytes(path)
    updated = embed_bytes(original, record)
    if preserved_chunks(original) != preserved_chunks(updated) or read_payload(updated) != record:
        raise ValueError("verification_failed")
    fd, temporary = tempfile.mkstemp(prefix=".browser-timing-", suffix=path.suffix, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        if fingerprint(path) != expected:
            raise ValueError("file_changed")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return fingerprint(path)
