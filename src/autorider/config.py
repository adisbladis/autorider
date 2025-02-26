from __future__ import annotations
from pathlib import Path
from pydantic import BaseModel, Field

import tomllib


class OutputConfig(BaseModel):
    build_systems: bool = Field(alias="build-systems", default=True)
    wheel_depends_so: bool = Field(alias="wheel-depends-so", default=True)
    sdist_depends_so: bool = Field(alias="sdist-depends-so", default=True)


class PackageOutputConfig(BaseModel):
    build_systems: bool | None = Field(alias="build-systems", default=None)
    wheel_depends_so: bool | None = Field(alias="wheel-depends-so", default=None)
    sdist_depends_so: bool | None = Field(alias="sdist-depends-so", default=None)


class AutoriderConfig(BaseModel):
    include: list[str] = Field(default_factory=lambda: ["*"])
    exclude: list[str] = Field(default_factory=list)
    outputs: OutputConfig = Field(default_factory=OutputConfig)
    packages: dict[str, PackageOutputConfig] = Field(default_factory=dict)


class Config(BaseModel):
    autorider: AutoriderConfig = Field(default_factory=AutoriderConfig)

    @classmethod
    def from_path(cls, path: Path) -> Config:
        if path.exists():
            with open(path, "rb") as config_file:
                return cls(**tomllib.load(config_file))
        else:
            return cls()
