"""Zero-dependency, deterministic PEP 517 build backend for this package."""

from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import io
import os
import pathlib
import tarfile
import zipfile


NAME = "scitt-time-anchor-cleanroom"
NORMALIZED_NAME = "scitt_time_anchor_cleanroom"
VERSION = "0.1.0"
DIST_INFO = f"{NORMALIZED_NAME}-{VERSION}.dist-info"
ROOT = pathlib.Path(__file__).resolve().parent


def _metadata() -> bytes:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    headers = (
        "Metadata-Version: 2.3\n"
        f"Name: {NAME}\n"
        f"Version: {VERSION}\n"
        "Summary: Clean-room verifier for draft-fassbender-scitt-time-anchor-06\n"
        "Author-email: Iman Schrock <team@emiliaprotocol.ai>\n"
        "Requires-Python: >=3.11\n"
        "License-File: LICENSE\n"
        "Description-Content-Type: text/markdown\n"
        "Project-URL: Repository, https://github.com/emiliaprotocol/"
        "scitt-time-anchor-verifier\n"
        "Project-URL: Specification, https://www.ietf.org/archive/id/"
        "draft-fassbender-scitt-time-anchor-06.txt\n"
        "\n"
    )
    return (headers + readme).encode("utf-8")


def _wheel_metadata() -> bytes:
    return (
        "Wheel-Version: 1.0\n"
        "Generator: scitt-time-anchor-cleanroom deterministic backend\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    ).encode("ascii")


def _hash_record(payload: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=")
    return "sha256=" + digest.decode("ascii")


def _zip_info(name: str, mode: int = 0o644) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (mode & 0xFFFF) << 16
    return info


def build_wheel(
    wheel_directory: str,
    config_settings: object = None,
    metadata_directory: str | None = None,
) -> str:
    del config_settings, metadata_directory
    destination = pathlib.Path(wheel_directory)
    destination.mkdir(parents=True, exist_ok=True)
    filename = f"{NORMALIZED_NAME}-{VERSION}-py3-none-any.whl"
    target = destination / filename

    entries: dict[str, bytes] = {}
    package_root = ROOT / "src" / "scitt_time_anchor"
    for source in sorted(package_root.rglob("*")):
        if source.is_file() and "__pycache__" not in source.parts:
            archive_name = source.relative_to(ROOT / "src").as_posix()
            entries[archive_name] = source.read_bytes()
    entries[f"{DIST_INFO}/METADATA"] = _metadata()
    entries[f"{DIST_INFO}/WHEEL"] = _wheel_metadata()
    entries[f"{DIST_INFO}/licenses/LICENSE"] = (ROOT / "LICENSE").read_bytes()
    entries[f"{DIST_INFO}/licenses/NOTICE"] = (ROOT / "NOTICE").read_bytes()

    record_buffer = io.StringIO(newline="")
    writer = csv.writer(record_buffer, lineterminator="\n")
    for archive_name in sorted(entries):
        payload = entries[archive_name]
        writer.writerow((archive_name, _hash_record(payload), str(len(payload))))
    record_name = f"{DIST_INFO}/RECORD"
    writer.writerow((record_name, "", ""))
    entries[record_name] = record_buffer.getvalue().encode("utf-8")

    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as wheel:
        for archive_name in sorted(entries):
            wheel.writestr(_zip_info(archive_name), entries[archive_name], compresslevel=9)
    return filename


def _sdist_sources() -> list[pathlib.Path]:
    roots = (
        pathlib.Path(".gitignore"),
        pathlib.Path("LICENSE"),
        pathlib.Path("NOTICE"),
        pathlib.Path("README.md"),
        pathlib.Path("REPRODUCING.md"),
        pathlib.Path("build_backend.py"),
        pathlib.Path("pyproject.toml"),
    )
    result = [ROOT / item for item in roots]
    for directory in ("docs", "src", "tests", "tools", "vectors"):
        result.extend(
            path
            for path in sorted((ROOT / directory).rglob("*"))
            if path.is_file()
            and "__pycache__" not in path.parts
            # The repository verification log records distribution hashes and
            # therefore cannot itself be an input to the source distribution.
            and path != ROOT / "docs" / "BUILD_LOG.md"
        )
    return result


def build_sdist(sdist_directory: str, config_settings: object = None) -> str:
    del config_settings
    destination = pathlib.Path(sdist_directory)
    destination.mkdir(parents=True, exist_ok=True)
    filename = f"{NAME}-{VERSION}.tar.gz"
    target = destination / filename
    prefix = f"{NAME}-{VERSION}"

    with target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w", format=tarfile.GNU_FORMAT) as archive:
                package_metadata = _metadata()
                metadata_info = tarfile.TarInfo(f"{prefix}/PKG-INFO")
                metadata_info.size = len(package_metadata)
                metadata_info.mode = 0o644
                metadata_info.mtime = 0
                metadata_info.uid = 0
                metadata_info.gid = 0
                metadata_info.uname = ""
                metadata_info.gname = ""
                archive.addfile(metadata_info, io.BytesIO(package_metadata))
                for source in sorted(_sdist_sources(), key=lambda item: item.relative_to(ROOT).as_posix()):
                    relative = source.relative_to(ROOT).as_posix()
                    payload = source.read_bytes()
                    info = tarfile.TarInfo(f"{prefix}/{relative}")
                    info.size = len(payload)
                    info.mode = 0o755 if relative.startswith("tools/") else 0o644
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, io.BytesIO(payload))
    return filename


def prepare_metadata_for_build_wheel(
    metadata_directory: str, config_settings: object = None
) -> str:
    del config_settings
    target = pathlib.Path(metadata_directory) / DIST_INFO
    target.mkdir(parents=True, exist_ok=True)
    (target / "METADATA").write_bytes(_metadata())
    (target / "WHEEL").write_bytes(_wheel_metadata())
    return DIST_INFO


def get_requires_for_build_wheel(config_settings: object = None) -> list[str]:
    del config_settings
    return []


def get_requires_for_build_sdist(config_settings: object = None) -> list[str]:
    del config_settings
    return []


if __name__ == "__main__":
    output = os.environ.get("SCITT_DIST_DIR", "dist")
    wheel = build_wheel(output)
    sdist = build_sdist(output)
    print(pathlib.Path(output) / wheel)
    print(pathlib.Path(output) / sdist)
