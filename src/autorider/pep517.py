import tomllib
from typing import TypedDict, NotRequired, IO


# https://pip.pypa.io/en/stable/reference/build-system/pyproject-toml/#fallback-behaviour
FALLBACK_SYSTEMS = ["setuptools"]


class BuildSystem(TypedDict):
    requires: NotRequired[list[str]]


Pyproject = TypedDict(
    "Pyproject",
    {
        "build-system": NotRequired[BuildSystem],
    },
)


def get_build_systems(pyproject: Pyproject) -> list[str]:
    build_system = pyproject.get("build-system")
    if build_system is None:
        return FALLBACK_SYSTEMS

    systems = build_system.get("requires")
    if systems is None:
        return FALLBACK_SYSTEMS

    if not isinstance(systems, list) or not all(  # pyright: ignore[reportUnnecessaryIsInstance]
        isinstance(system, str)  # pyright: ignore[reportUnnecessaryIsInstance]
        for system in systems
    ):
        raise ValueError(
            "PEP-517 build-system.requires not defined as a list of strings"
        )

    return systems


def read_build_systems(fp: IO[bytes]) -> list[str]:
    pyproject: Pyproject = tomllib.load(fp)  # pyright: ignore[reportAssignmentType]
    return get_build_systems(pyproject)
