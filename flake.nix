{
    description = "C++ dev environment";

    inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

    outputs = { self, nixpkgs }:
    let
    system = "x86_64-linux";
    pkgs = import nixpkgs { inherit system; };
    in {
        devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
            gcc
            cmake
            gdb
            clang-tools
            # OpenGL / GLUT
            freeglut
            mesa
            libGL
            libGLU
            # Script
            python3
            python3Packages.svgpathtools
            ];
        };
    };
}
