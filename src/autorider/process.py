from typing import override, ClassVar
from collections.abc import Iterable
from concurrent import futures
from fnmatch import fnmatch
from enum import Enum
import logging
import re

from autorider.lib import nix_locate_file
from autorider.manylinux import MANYLINUX_LIBS
from autorider.scanners import PackageScanner, ScanResult
from autorider.manager import GENERATOR_T
from autorider.config import Config
from autorider.output import PackageOutput


logger = logging.getLogger(__name__)


class ScanDepends(Enum):
    NONE = 0
    SDIST = 1
    WHEEL = 2


class PostProcessor:
    SCAN_DEPENDS: ClassVar[ScanDepends]
    scan_result: ScanResult

    def __init__(self, scan_result: ScanResult) -> None:
        self.scan_result = scan_result

    def run(self, output: PackageOutput) -> None:  # pyright: ignore[reportUnusedParameter]
        raise NotImplementedError()


class WheelDependsPostProcessor(PostProcessor):
    """
    Output native dependencies for wheel scan
    """

    SCAN_DEPENDS: ClassVar[ScanDepends] = ScanDepends.WHEEL

    @override
    def run(self, output: PackageOutput) -> None:
        if not self.scan_result.wheel:
            return

        native_depends = [
            so
            for so in (
                self.scan_result.wheel.native_depends  # .so scan result
                - self.scan_result.wheel.native_provides  # Filter self references
                - MANYLINUX_LIBS  # Manylinux libs are added as required by wheel file tags
            )
            if not so.startswith("ld-linux")
        ]

        if not native_depends:
            return

        output["wheel-depends-so"] = list(native_depends)


class SdistDependsPostProcessor(PostProcessor):
    """
    Output native dependencies for source build based on wheel scan
    """

    FILTERED_SO: set[str] = set(
        (
            "libm.so.6",
            "libgcc_s.so.1",
            "libc.so.6",
            "libpthread.so.0",
            "librt.so.1",
            "libstdc++.so.6",
        )
    )

    SCAN_DEPENDS: ClassVar[ScanDepends] = ScanDepends.WHEEL

    @override
    def run(self, output: PackageOutput) -> None:
        if not self.scan_result.wheel:
            return

        native_depends: list[str] = []
        for so in self.scan_result.wheel.native_depends:
            if so.startswith("ld-linux"):
                continue

            m = re.match(r"(.+)-[0-9a-f]{8}(\.so.+)", so)
            soname = "".join((m.group(1), m.group(2))) if m else so

            if soname in self.FILTERED_SO:
                continue

            native_depends.append(soname)

        output["sdist-depends-so"] = native_depends


class BuildSystemPostProcessor(PostProcessor):
    """
    Output python build systems based on sdist scan
    """

    SCAN_DEPENDS: ClassVar[ScanDepends] = ScanDepends.SDIST

    @override
    def run(self, output: PackageOutput) -> None:
        if not self.scan_result.sdist:
            return

        build_systems = self.scan_result.sdist.build_systems
        if not build_systems:
            return

        output["build-systems"] = build_systems


class BuildRequiresPostProcessor(PostProcessor):
    """
    Output nativeBuildInputs tooling based on source tree files
    """

    SCAN_DEPENDS: ClassVar[ScanDepends] = ScanDepends.SDIST

    @override
    def run(self, output: PackageOutput) -> None:
        if not self.scan_result.sdist:
            return

        build_requires = self.scan_result.sdist.build_requires
        if not build_requires:
            return

        output["build-requires"] = list(build_requires)


def lookup_sonames(
    sonames: Iterable[str],
    ignore: list[str],
) -> dict[str, str]:
    ret: dict[str, str] = {}
    with futures.ThreadPoolExecutor() as executor:
        lookup_futures = [
            executor.submit(nix_locate_file, soname, ignore=ignore)
            for soname in sonames
        ]
        for soname, future in zip(sonames, lookup_futures):
            result = future.result()
            if result:
                ret[soname] = result
    return ret


def process_pkg(config: Config, pkg_scanner: PackageScanner):
    name = pkg_scanner.name

    output_config = config.autorider.outputs
    pkg_config = config.autorider.packages.get(name)
    if pkg_config:
        output_config = output_config.model_copy(
            update=pkg_config.model_dump(exclude_none=True)
        )

    # Figure out dependencies for the scan
    scan_depends: set[ScanDepends] = set()
    postprocessors: list[type[PostProcessor]] = []
    if output_config.build_systems:
        postprocessors.append(BuildSystemPostProcessor)
    if output_config.wheel_depends_so:
        postprocessors.append(WheelDependsPostProcessor)
    if output_config.sdist_depends_so:
        postprocessors.append(SdistDependsPostProcessor)
    if output_config.build_requires:
        postprocessors.append(BuildRequiresPostProcessor)
    for postprocessor in postprocessors:
        scan_depends.add(postprocessor.SCAN_DEPENDS)

    logger.debug("processing package '%s' with config '%s'", name, output_config)

    output: PackageOutput = {}
    if not postprocessors:
        return pkg_scanner, output

    if pkg_scanner.version:
        output["version"] = pkg_scanner.version

    logger.info("scanning package '%s'", name)
    scan_result = pkg_scanner.scan()
    for postprocessor_cls in postprocessors:
        logger.debug(
            "processing output for '%s' with postprocessor '%s'",
            name,
            postprocessor_cls,
        )
        postprocessor_cls(scan_result).run(output)

    return pkg_scanner, output


def process_pkgs(config: Config, generator: GENERATOR_T):
    ret: dict[str, PackageOutput | list[PackageOutput]] = {}

    with futures.ThreadPoolExecutor() as executor:
        scan_futures: list[futures.Future[tuple[PackageScanner, PackageOutput]]] = []
        for pkg_scanner in generator:
            name = pkg_scanner.name

            # Include/exclude based on config patterns
            if not any(fnmatch(name, pat) for pat in config.autorider.include):
                continue
            if any(fnmatch(name, pat) for pat in config.autorider.exclude):
                continue

            fut = executor.submit(process_pkg, config, pkg_scanner)
            scan_futures.append(fut)

        for future in scan_futures:
            pkg_scanner, output = future.result()
            ret.setdefault(pkg_scanner.name, []).append(output)  # pyright: ignore[reportAttributeAccessIssue]

    # Collapse structure on non-abmigious packages
    for name, outputs in ret.items():
        if isinstance(outputs, list) and len(outputs) == 1:
            output = outputs[0]
            try:
                del output["version"]
            except KeyError:
                pass
            ret[name] = output

    return {k: v for k, v in ret.items() if v}
