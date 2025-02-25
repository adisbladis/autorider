from __future__ import annotations
from dataclasses import dataclass
from typing import override, IO
from pathlib import Path
import os.path

from elftools.elf.elffile import ELFFile
from elftools.elf.dynamic import DynamicSection

from autorider.pep517 import FALLBACK_SYSTEMS, read_build_systems
from autorider.readers import Reader, ZipReader, TarReader, DirReader


class Scanner:
    reader: Reader
    name: str

    def __init__(self, path: Path) -> None:
        self.name = path.name

        # Instantiate reader
        name = path.name
        if name.endswith(".zip") or name.endswith(".whl"):
            cls = ZipReader
        elif ".tar" in name:
            cls = TarReader
        elif path.is_dir():
            cls = DirReader
        else:
            raise ValueError(f"Could not instantiate reader for '{path}'")
        self.reader = cls(path, self.reader_pred, self.reader_cb)

    def reader_pred(self, name: str) -> bool:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def reader_cb(self, name: str, fp: IO[bytes]) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()

    def run(self):
        self.reader.run()


class SdistScanner(Scanner):
    build_systems: list[str]

    def __init__(self, path: Path) -> None:
        self.build_systems = FALLBACK_SYSTEMS
        super().__init__(path)

    @override
    def reader_pred(self, name: str) -> bool:
        levels = name.count("/")
        return (levels == 1) and os.path.basename(name) == "pyproject.toml"

    @override
    def reader_cb(self, name: str, fp: IO[bytes]) -> None:
        self.build_systems = read_build_systems(fp)


class WheelScanner(Scanner):
    native_depends: set[str]
    native_provides: set[str]

    def __init__(self, path: Path) -> None:
        self.native_depends = set()
        self.native_provides = set()
        super().__init__(path)

    @override
    def reader_pred(self, name: str) -> bool:
        return name.endswith(".so") or ".so." in name

    @override
    def reader_cb(self, name: str, fp: IO[bytes]) -> None:
        self.native_provides.add(os.path.basename(name))

        elf = ELFFile(fp)
        for section in elf.iter_sections():  # pyright: ignore[reportUnknownMemberType]
            if not isinstance(section, DynamicSection):
                continue
            for tag in section.iter_tags():  # pyright: ignore[reportUnknownMemberType]
                if tag.entry.d_tag == "DT_NEEDED":  # pyright: ignore[reportUnknownMemberType]
                    needed: str = tag.needed  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue,reportUnknownVariableType]
                    self.native_depends.add(needed)  # pyright: ignore[reportUnknownArgumentType]


@dataclass
class ScanResult:
    name: str  # Artifact filename
    sdist: None | SdistScanner = None
    wheel: None | WheelScanner = None


class PackageScanner:
    name: str
    version: str | None

    def __init__(self, name: str, version: str | None = None) -> None:
        self.name = name
        self.version = version

    def scan(self) -> ScanResult:
        raise NotImplementedError()
