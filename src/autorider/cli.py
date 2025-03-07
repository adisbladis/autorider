from collections.abc import Generator
from pathlib import Path
from typing import cast
import argparse
import json
import os

from autorider.config import Config
from autorider.scanners import ScanResult
from autorider.manager import PackageManager
from autorider.uv import Uv2nix
from autorider.process import process_pkgs, lookup_sonames


SCAN_RESULTS = Generator[ScanResult, None, None]


def _make_argparse():
    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "--output", "-o", help="Overlay output directory", default="autorider.nix"
    )
    _ = parser.add_argument("--root", default=os.getcwd(), help="Path to project root")
    _ = parser.add_argument(
        "--config", help="Path to TOML config (defaults to $root/pyproject.toml)"
    )

    subp = parser.add_subparsers(
        help="packaging integration", dest="subcommand", required=True
    )

    _ = subp.add_parser("uv2nix")

    return parser


def main() -> None:
    args = _make_argparse().parse_args()
    subcommand = cast(str, args.subcommand)
    root = Path(cast(str, args.root))

    output_path = Path(cast(str, args.output))
    if not output_path.is_absolute():
        output_path = root.joinpath(output_path)

    config_path = Path(
        args.config if args.config else os.path.join(root, "pyproject.toml")
    )
    config = Config.from_path(config_path)

    manager: PackageManager
    match subcommand:
        case "uv2nix":
            manager = Uv2nix(Path(root))
        case _:
            raise ValueError(f"Unsupported subcommand '{subcommand}'")

    results = process_pkgs(config, manager.generate())

    # Aggregate all dependency sonames for nixpkgs lookup
    sonames: set[str] = set()
    for pkg_outputs in results.values():
        if isinstance(pkg_outputs, list):
            for pkg_output in pkg_outputs:
                for soname in pkg_output.get("wheel-depends-so", []):
                    sonames.add(soname)
                for soname in pkg_output.get("sdist-depends-so", []):
                    sonames.add(soname)
        else:
            for soname in pkg_outputs.get("wheel-depends-so", []):
                sonames.add(soname)
            for soname in pkg_outputs.get("sdist-depends-so", []):
                sonames.add(soname)

    # Lookup soname providers using nix-locate
    so_providers = lookup_sonames(sonames, config.autorider.nix_locate_ignore)

    try:
        os.mkdir(output_path)
    except FileExistsError:
        pass

    with open(output_path.joinpath("packages.json"), "w") as fp:
        json.dump(results, fp, indent=2)
        _ = fp.write("\n")

    with open(output_path.joinpath("so-providers.json"), "w") as fp:
        json.dump(so_providers, fp, indent=2)
        _ = fp.write("\n")

    print(f"Wrote {output_path}")
