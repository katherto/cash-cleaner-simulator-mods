# Strap colour tools

- `tools/iostore.py`: reads IoStore `.utoc`/`.ucas` (uncompressed containers).
- `tools/cityhash.py`: CityHash64 as used for UE package/container IDs (`pkgid(name)`).
- `tools/iobuild.py`, `tools/iobuild2.py`: write a standalone container. Blocks must be 16-byte aligned and the
  `.ucas` padded to a multiple of 16, or the game ignores the package.
- `tools/merge.py`: append assets to an existing container.
- `tools/make_eur100.py`, `make_gbp.py`, `set_eur10_strap.py`, `build_addon.py`: the scripts that produced the
  individual mods. They were run from a scratch workspace and refer to input files (extracted game chunks, the
  original mod) that are not in this repo, so they are reference material, not turnkey.
- `strap_color_tuner.py`: change the strap colours inside a built `NewBanknotes_AddonStrapFix_P.ucas`
  (`python strap_color_tuner.py --eur5 "#2E3D52"`). Backs up the file first.

Known container-loading rules learned the hard way:
1. 16-byte alignment (see above).
2. When two mod containers hold the same package, the one with the higher container ID wins ties; container
   ID = CityHash64 of the lower-cased container name, UTF-16LE.
3. The game's own container is Oodle-compressed, so game assets must be extracted with `retoc`.
