from typing import TypedDict, NotRequired


PackageOutput = TypedDict(
    "PackageOutput",
    {
        # Package version.
        "version": NotRequired[str],
        # List of natively linked .so files from manylinux wheel.
        # Excluding self-references
        "wheel-depends-so": NotRequired[list[str]],
        # List of natively linked .so files from manylinux wheel
        "sdist-depends-so": NotRequired[list[str]],
        # Build systems as a list of PEP-508 strings
        "build-systems": NotRequired[list[str]],
        # Native build tooling (nativeBuildInputs)
        "build-requires": NotRequired[list[str]],
    },
)

Output = TypedDict(
    "Output",
    {
        "packages": NotRequired[dict[str, PackageOutput | list[PackageOutput]]],
        "so-providers": NotRequired[dict[str, str]],
    }
)
