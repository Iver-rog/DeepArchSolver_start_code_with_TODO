{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    imports = [
    ];
    # nativeBuildInputs is usually what you want -- tools you need to run
    nativeBuildInputs = with pkgs; [
      nix
      home-manager
      git
      gcc
      ];

    buildInputs = with pkgs; [
       systemd
      (python3.withPackages (python-pkgs: [
        python-pkgs.pip
        python-pkgs.numpy
        python-pkgs.matplotlib
        python-pkgs.meshio
      ]))
    ];
}

