{
  description = "Hermetic deterministic environment for Thalos Prime / MNN";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            python312
            python312Packages.pip
            python312Packages.virtualenv
            python312Packages.pytest
            python312Packages.z3-solver
            gnumake
            gcc
            clang
            cmake
            pkg-config
            git
            jq
            curl
            nodejs_20
            yarn
          ];

          shellHook = ''
            export PYTHONHASHSEED=0
            export SOURCE_DATE_EPOCH=1704067200
            export TZ=UTC
            export LC_ALL=C.UTF-8
            export DETERMINISTIC_MODE=true
            export CXXFLAGS="-O2 -fno-fast-math -ffp-contract=off -fno-common"
            echo "Loaded deterministic Thalos Prime shell"
          '';
        };

        checks.py-smoke = pkgs.runCommand "py-smoke" {
          buildInputs = [ pkgs.python312 ];
        } ''
          python - <<'PY'
import hashlib
payload = b"THALOS_DETERMINISTIC_CHECK"
print(hashlib.sha256(payload).hexdigest())
PY
          touch $out
        '';
      });
}
