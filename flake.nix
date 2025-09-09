{
  description = "Development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";

      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true;

        overlays = [
          (final: prev: {

            ffmpeg-full = prev.ffmpeg-full.overrideAttrs (old: {
              configureFlags = (old.configureFlags or [ ])
                ++ [ "--enable-nonfree" "--enable-libfdk-aac" ];
              buildInputs =
                (old.buildInputs or [])
                ++ [ final.fdk_aac ];
            });
          })
        ];
      };

      py = pkgs.python3Packages;
    in {
      devShell.${system} = pkgs.mkShell {
        packages = with pkgs; [
          ffmpeg-full

          py.openai
          py.pydub
          py.mutagen
        ];
      };
    };
}
