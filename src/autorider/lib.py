import subprocess
import logging


logger = logging.getLogger(__name__)


SO_PROVIDERS: dict[str, str] = {
    "libgcc_s.so.1": "stdenv.cc.cc",
    "libstdc++.so.6": "stdenv.cc.libc",
    "libm.so.6": "stdenv.cc.libc",
    "libc.so.6": "stdenv.cc.libc",
}


def nix_locate_file(name: str, ignore: list[str] | None = None) -> str | None:
    logger.debug("running nix-locate for file '%s'", name)

    try:
        return SO_PROVIDERS[name]
    except KeyError:
        pass

    """Use nix-locate to find filename from db"""
    proc = subprocess.run(
        [
            "nix-locate",
            "--top-level",
            "--no-group",
            "--minimal",
            "-t",
            "r",
            "-t",
            "x",
            name,
        ],
        check=True,
        stdout=subprocess.PIPE,
    )

    for line in proc.stdout.decode().split("\n"):
        if not line:
            continue

        if ignore and any(line.startswith(prefix) for prefix in ignore):
            continue

        return line


def select_wheel(names: list[str]) -> None | str:
    for name in reversed(sorted(names)):
        if "manylinux" in name:
            return name
