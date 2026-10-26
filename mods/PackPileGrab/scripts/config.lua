return {
    -- true  = F+Click on a pile of strapped packs picks up the WHOLE pile as a pile (any size).
    --         A plain click stays vanilla (one pack at a time).
    -- false = fully vanilla (the mod does nothing).
    WholePilePickup = true,

    -- Your in-game "grab" key (the F in F+Click). Use a UE4SS key name, e.g. "F", "G", "E".
    GrabKey = "F",

    -- Backup only. The mod asks the game whether the key is held; until that has worked once it uses this
    -- timer instead: seconds "grab mode" stays on after pressing the key. Once the exact method works
    -- (see the log), this setting is ignored.
    FallbackHoldSeconds = 0.6,

    -- Diagnostics: write PackPileGrab_log.txt next to the game exe (detection method, mode switches,
    -- and the mode at every left click). Leave off for normal play.
    Log = false,
}
