# Introduction

Take the tedium out of Python packaging by automating the boring parts
While only uv (through `uv2nix`) is supported at the moment `autorider` is designed to work with any Python dependency locker dependency locker.

## Features

### Automatic build-system inference

PEP-517 can automatically be added to your build by inspecting the dependency sdist.

### Automatic native dependencies

By inspecting existing wheels, inspecting their RPATHs & looking up their corresponding Nixpkgs packages using `nix-locate` native dependencies can be automatically inferred.

### Native build requirements

By looking at what files are present, for example `CMakeLists.txt`, it's possible to automatically infer that the packages sdist build process requires additional tools.

## Method

Autorider works by reading package data from binary wheels & sdists.
This makes it possible to infer more information than Python build systems normally expose.

The data flow of `autorider` is roughly as follows:

- Reader

Reads package from a local directory, an sdist or a wheel.

- Scanner

Implements different scanning behaviour on top of the reader.

- Output

Takes the result of a scan and generates concrete output.
