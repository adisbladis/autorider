# Getting started with uv2nix

To generate an autorider output for use with uv2nix:
```sh
$ autorider uv2nix
```

You can then use this overlay together with uv2nix like:
```nix
pythonSet =
  (pkgs.callPackage pyproject-nix.build.packages {
    inherit python;
  }).overrideScope
    (
      lib.composeManyExtensions [
        pyproject-build-systems.overlays.default
        overlay
        (autorider.lib.mkOverlay ./autorider.json { })
      ]
    );
```

## Configuring enabled output modules

Autorider is set up into a few different output modules, all of which are _disabled_ by default.
Each feature is opt-in while autorider is still experimental.

- `pyproject.toml`:
```toml
[tool.autorider.outputs]
# Extract PEP-517 build systems from sdist
build-systems = True

# Infer dependencies from a wheel .so dependencies
wheel-depends-so = True

# Infer dependencies from a wheel .so dependencies, adding them to a source build
sdist-depends-so = True

# Scan for non-Python build requirements (such as CMakeLists.txt)
build-requires = True
```

## Overriding lookups

`nix-locate`, which is used to look up which package provides a dependency, often ranks irrelevant libraries quite high & needs to be tuned to exclude false positives.

- `pyproject.toml`:
```toml
[tool.autorider]
nix-locate-ignore = [
  "pyfa",
  "hyperhdr",
  "figma-linux",
]
```

## Overriding failed lookups

Sometimes nixpkgs doesn't even provide a shared library that a package _may_ use under certain circumstances.
To opt out of a `.so` pulled in by something set it to `null`:
```nix
autorider.lib.mkOverlay ./autorider.json {
  so-providers = {
    "libQt6EglFsKmsGbmSupport.so.6" = null;
  };
}
```

Additionally `autoPatchelfHook` also needs to be told to ignore the failed lookup in a separate overlay:
```nix
final: prev: {
  pyside6-essentials = prev.pyside6-essentials.overrideAttrs(old: {
    autoPatchelfIgnoreMissingDeps = [
      "libQt6EglFsKmsGbmSupport.so*"
      "libmimerapi.so"
    ];
  });
}
```
