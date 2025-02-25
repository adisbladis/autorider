from autorider.scanners import PackageScanner
from collections.abc import Generator


GENERATOR_T = Generator[PackageScanner, None, None]


class PackageManager:
    def generate(self) -> GENERATOR_T:
        raise NotImplementedError()
