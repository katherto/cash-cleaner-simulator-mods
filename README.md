# Cash Cleaner Simulator mods

Mods and the tools used to make them for **Cash Cleaner Simulator** (Unreal Engine 5.4). Built through trial
and error with Claude; every behavior below was tested in game by the repo owner.

## Mods

| Mod | What it does | Type |
|---|---|---|
| [PackPileGrab](mods/PackPileGrab) | F+Click on any floor pile of strapped packs picks up the **whole pile** as a pile (vanilla caps it at 60 loose packs). A plain click is unchanged. | UE4SS Lua |
| [Strap colour mods](strap-mods) | Recoloured bill-pack straps (EUR 5/10/100, GBP 5/10/20/50). Only the build tools and notes are here, see below. | Asset override (IoStore) |

PackPileGrab is ready to use: grab `releases/PackPileGrab_v1.2.0.zip` (Vortex-ready) and read its
[README](mods/PackPileGrab/README.txt). Requires UE4SS.

## Probes (`mods/probes`)
Small read-only UE4SS Lua scripts used to find out how the game works. Not needed to play.
- `PileProbe`, `PileTrace`, `PileLive`: inspect and trace pile/pickup classes (how PackPileGrab was found).
- `StrapProbe`: prints the strap colour parameters of loaded pack materials (F6).

## Strap mods (`strap-mods`)
Python tools that build IoStore containers (`.utoc/.ucas/.pak`) containing recoloured copies of
`MI_MoneyPack_*` material instances (the strap colour is the `TapeColorB` parameter), and
`strap_color_tuner.py`, which edits those colours in an already-built container.
The finished containers are **not** in this repo: they contain modified copies of the game's assets and,
for EUR 5/10, of another author's mod (New Banknotes on Nexus Mods).

## Notes
- No game files are stored here.
- The idea for PackPileGrab started from the `pile_settings` UE4SS mod on Nexus Mods; no code is shared.
- Game is no longer updated by its developers, so the class names used here are not expected to change.
