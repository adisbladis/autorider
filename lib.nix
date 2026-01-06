{ pyproject-nix, lib, ... }:
let
  inherit (builtins)
    mapAttrs
    filter
    listToAttrs
    isString
    split
    concatMap
    ;
  inherit (lib)
    optionals
    unique
    getAttrFromPath
    importJSON
    optionalAttrs
    ;
  inherit (pyproject-nix.lib.pep508) parseString mkEnviron evalMarkers;
in
{

  /**
    Create overlay from generated metadata directory
    .
  */
  mkOverlay =
    path:
    {
      so-providers ? { },
    }:
    let
      data = importJSON path;

      packages = mapAttrs (
        name: overrideMeta:
        overrideMeta
        // optionalAttrs (overrideMeta ? build-systems) {
          build-systems = map parseString overrideMeta.build-systems;
        }
      ) (data.packages or { });

    in
    final: prev:
    let
      inherit (prev) python;
      inherit (final) pkgs;
      environ = mkEnviron python;

      so-providers' =
        (mapAttrs (
          so: provider:
          let
            provider' = filter isString (split "\\." provider);
          in
          getAttrFromPath provider' pkgs
        ) (data.so-providers or { }))
        // so-providers;

      lookupSonames =
        sonames:
        unique (
          concatMap (
            soname:
            let
              provider = so-providers'.${soname};
            in
            if provider != null then [ provider ] else [ ]
          ) sonames
        );

    in
    mapAttrs (
      name: overrideMeta:
      let
        drv = prev.${name};
        format = drv.passthru.format or "pyproject";
      in
      if format == "pyproject" then
        drv.overrideAttrs (old: {

          buildInputs =
            (old.buildInputs or [ ])
            # Add native dependencies
            ++ optionals (overrideMeta ? sdist-depends-so) (lookupSonames overrideMeta.sdist-depends-so);

          nativeBuildInputs =
            old.nativeBuildInputs
            # Add native build tooling
            ++ optionals (overrideMeta ? build-requires) (map (name: pkgs.${name}) overrideMeta.build-requires)
            # Add build systems
            ++ optionals (overrideMeta ? build-systems) (
              let
                selected = filter (
                  build-system: build-system.markers == null || evalMarkers environ build-system.markers
                ) overrideMeta.build-systems;
                spec = listToAttrs (
                  map (build-system: {
                    inherit (build-system) name;
                    value = build-system.extras;
                  }) selected
                );
              in
              final.resolveBuildSystem spec
            );
        })
      else if format == "wheel" then
        drv.overrideAttrs (old: {
          buildInputs =
            (old.buildInputs or [ ])
            # Add native dependencies
            ++ optionals (overrideMeta ? wheel-depends-so) (lookupSonames overrideMeta.wheel-depends-so);
        })
      else
        throw "Could not determine format for ${name}"
    ) packages;
}
