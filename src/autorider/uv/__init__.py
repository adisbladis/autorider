from typing import override
from pathlib import Path
import logging

from autorider.scanners import PackageScanner
from autorider.uv import lock1
from autorider.manager import GENERATOR_T, PackageManager


logger = logging.getLogger(__name__)


class UvPackageScanner(PackageScanner):
    package: lock1.Package

    def __init__(self, package: lock1.Package):
        self.package = package
        super().__init__(package["name"], package.get("version"))

    @override
    def scan(self):
        return lock1.scan_pkg(self.package)


class Uv2nix(PackageManager):
    workspace_root: Path

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        super().__init__()

    @override
    def generate(self) -> GENERATOR_T:
        with open(self.workspace_root.joinpath("uv.lock"), "rb") as fp:
            lock = lock1.load(fp)

        for pkg in lock.get("package", []):
            yield UvPackageScanner(pkg)
