from __future__ import annotations
from pathlib import Path
import os.path
from typing import TypedDict, NotRequired
from typing import cast, IO
import tomllib

from autorider.download import GitDownload, HTTPDownload
from autorider.lib import select_wheel
from autorider.scanners import ScanResult, SdistScanner, WheelScanner


class UvLock(TypedDict):
    version: str
    package: NotRequired[list[Package]]


class PackageSource(TypedDict):
    registry: NotRequired[str]
    git: NotRequired[str]
    path: NotRequired[str]


class PackageSdist(TypedDict):
    url: NotRequired[str]
    size: NotRequired[int]
    hash: str


class PackageWheel(TypedDict):
    url: NotRequired[str]
    filename: NotRequired[str]
    size: NotRequired[int]
    hash: str


class Package(TypedDict):
    name: str
    version: NotRequired[str]
    sdist: NotRequired[PackageSdist]
    wheels: NotRequired[list[PackageWheel]]
    source: NotRequired[PackageSource]


def load(fp: IO[bytes]) -> UvLock:
    return cast(UvLock, tomllib.load(fp))  # pyright: ignore[reportInvalidCast]


def loads(s: str) -> UvLock:
    return cast(UvLock, tomllib.loads(s))  # pyright: ignore[reportInvalidCast]


def get_path(source: PackageSource) -> Path:
    if "path" not in source:
        raise ValueError("Expected path in source")

    path = Path(source["path"])

    # Handle overriden registry
    registry = source.get("registry")
    if registry and registry[0] in (".", "/"):
        path = Path(os.path.join(registry, path))

    return path.absolute()


def scan_pkg(pkg: Package):
    source = pkg.get("source", {})

    wheel_scanner: WheelScanner | None = None
    if "wheels" in pkg:
        wheels = pkg["wheels"]

        wheels_by_name: dict[str, PackageWheel] = {}
        for wheel in wheels:
            wheel_path = wheel.get("url", wheel.get("path"))
            if not wheel_path:
                raise ValueError(f"Could not get wheel name for '{wheel}'")
            wheel_name = os.path.basename(wheel_path)
            wheels_by_name[wheel_name] = wheel

        selected = select_wheel(list(wheels_by_name))
        if selected:
            wheel = wheels_by_name[selected]
            if "url" in wheel:
                url = wheel["url"]
                dl = HTTPDownload(url, wheel.get("hash"))
                archive = dl.get()
            elif "path" in source:
                archive = get_path(source)
            else:
                raise ValueError(f"wheel {wheel} unhandled")

            wheel_scanner = WheelScanner(archive)
            wheel_scanner.run()

    sdist_scanner: SdistScanner | None = None
    if "sdist" in pkg:
        sdist = pkg["sdist"]
        archive: Path

        if "url" in sdist:
            dl = HTTPDownload(sdist["url"], sdist.get("hash"))
            archive = dl.get()
        elif "path" in source:  # local path
            archive = get_path(source)
        else:
            raise ValueError(f"sdist {sdist} unhandled")

        sdist_scanner = SdistScanner(archive)
    elif "git" in source:
        dl = GitDownload(source["git"])
        sdist_scanner = SdistScanner(dl.get())

    if sdist_scanner:
        sdist_scanner.run()

    return ScanResult(
        pkg["name"],
        sdist=sdist_scanner,
        wheel=wheel_scanner,
    )
