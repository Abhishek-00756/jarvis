"""macOS screenshot capture and Vision OCR from plain Python."""

import os
import subprocess
import tempfile
from pathlib import Path


def capture_screen() -> str:
    fd, raw = tempfile.mkstemp(prefix="jarvis-screen-", suffix=".png")
    os.close(fd)
    path = Path(raw)
    try:
        result = subprocess.run(["screencapture", "-x", str(path)], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "screencapture failed")
        return str(path)
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _ocr_image(path: str) -> str:
    try:
        import Quartz
        from Vision import VNImageRequestHandler, VNRecognizeTextRequest
    except ImportError as exc:
        raise RuntimeError("Screen OCR requires pyobjc-framework-Quartz and pyobjc-framework-Vision.") from exc

    image = Quartz.CGImageSourceCreateWithURL(
        Quartz.CFURLCreateFromFileSystemRepresentation(None, os.fsencode(path), len(os.fsencode(path)), False), None
    )
    if image is None:
        raise RuntimeError("Could not load captured screen image.")
    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(1)
    request.setUsesLanguageCorrection_(True)
    handler = VNImageRequestHandler.alloc().initWithCGImage_options_(image, {})
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise RuntimeError(str(error))
    lines = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if candidates:
            lines.append(str(candidates[0].string()))
    return "\n".join(lines)


def read_screen_text() -> str:
    path = capture_screen()
    try:
        return _ocr_image(path)
    finally:
        Path(path).unlink(missing_ok=True)


def find_text_on_screen(query: str) -> str:
    text = read_screen_text()
    matches = [line for line in text.splitlines() if query.lower() in line.lower()]
    return "\n".join(matches) if matches else f"No visible screen text matched '{query}'."


def get_screen_context() -> str:
    return read_screen_text()
