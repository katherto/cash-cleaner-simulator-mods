PackPileGrab 1.2.0 - for Cash Cleaner Simulator (UE4SS Lua mod)
================================================================

WHAT IT DOES
Vanilla: grabbing a floor pile of strapped money packs with F+Click gives you at most 60 packs, as loose
packs, and leaves the rest of the pile on the floor. Only piles of 51-60 packs come up whole as a pile you
can carry and sweep with (like a pile of loose bills).

With this mod, F+Click on ANY pile of strapped packs picks up the WHOLE pile as one pile in your hands,
whatever its size. A plain click is unchanged (vanilla: takes one pack at a time).

WHAT IT DOES NOT CHANGE
- When piles form (vanilla: more than 101 packs) or break up (vanilla: 50 or fewer).
- Piles of loose bills, coins, or anything else.
- Your save files. The mod only flips one in-memory setting while the game runs; remove the mod and the
  game is back to vanilla.

REQUIREMENTS
UE4SS (Lua enabled) already installed for Cash Cleaner Simulator. No other mod is needed.
Do not run it together with a mod that also changes pile pickup settings.

INSTALL
Vortex: install the zip like any other mod. Manual: copy the PackPileGrab folder into
  ...\Cash Cleaner Simulator\CashCleanerSimulator\Binaries\Win64\ue4ss\Mods\
Restart the game. Piles are switched within about 2 seconds of loading a save.

UNINSTALL
Remove the PackPileGrab folder (or set WholePilePickup = false in scripts\config.lua).

SETTINGS  (scripts\config.lua)
  WholePilePickup      true / false. false makes the mod do nothing.
  GrabKey              Your grab key, default "F". Use a UE4SS key name.
  FallbackHoldSeconds  Backup timer, only used until the game confirms it can report the key as held.
                       Default 0.6 seconds.
  Log                  true writes PackPileGrab_log.txt next to the game exe, for troubleshooting.

GRAB KEY DETECTION
Grab mode is on only while the grab key is physically held, read from the game's own input state, so a quick
tap of F followed by a plain click is a plain click. If that reading ever fails, the mod falls back to a
short timer after the key press.

KNOWN BEHAVIOUR
Grabbing a huge pile as one pile is allowed by the game, but very large piles may look or handle oddly.
If a plain click ever picks up a whole pile, set Log = true, repeat it, and look at the log: the
"left click while mode = ..." lines show whether the mod thought the grab key was held.

HOW IT WORKS (short)
A pack pile has a "partial pickup from composition" flag. When it is on, a grab takes only as many packs
as fit in your hands. The mod turns it off for the moment the grab key is held, so the whole pile is taken
as a pile, and turns it back on when the key is released.
