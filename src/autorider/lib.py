import subprocess
import re


PAREN_RE = re.compile(r"\(.+\)")


SO_PROVIDERS: dict[str, str] = {
    "libgcc_s.so.1": "stdenv.cc.cc",
    "libstdc++.so.6": "stdenv.cc.libc",
    "libm.so.6": "stdenv.cc.libc",
    "libc.so.6": "stdenv.cc.libc",
}


def nix_locate_file(name: str, ignore: list[str]) -> str | None:
    try:
        return SO_PROVIDERS[name]
    except KeyError:
        pass

    """Use nix-locate to find filename from db"""
    proc = subprocess.run(
        [
            "nix-locate",
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
        if not line or PAREN_RE.match(line):
            continue

        if any(line.startswith(prefix) for prefix in ignore):
            continue

        return line


def select_wheel(names: list[str]) -> None | str:
    for name in reversed(sorted(names)):
        if "manylinux" in name:
            return name
