{
  pyproject-nix,
  uv2nix,
  lib,
  pyproject-build-systems,
}@inputs:
let
  workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
  overlay = workspace.mkPyprojectOverlay {
    sourcePreference = "wheel";
  };

in
{
  lib = import ./lib.nix inputs;

  packages = {
    autorider =
      { callPackage, callPackages, python }:
      let
        pythonSet =
          (callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope
            (
              lib.composeManyExtensions [
                pyproject-build-systems.overlays.wheel
                overlay
              ]
            );

        venv = pythonSet.mkVirtualEnv "autorider-env" workspace.deps.default;
        inherit (callPackages pyproject-nix.build.util { }) mkApplication;
      in
        mkApplication {
          inherit venv;
          package = pythonSet.autorider;
        };
  };
}
