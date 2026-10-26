-- PackPileGrab 1.2.0
-- F+Click on a floor pile of strapped packs picks up the whole pile as a pile (vanilla: only 60 loose packs).
-- A plain click is untouched (vanilla). Implementation: the pile's bPartialPickupFromComposition flag is
-- switched OFF while the grab key is held and back ON (vanilla) otherwise. Nothing else is modified, and
-- nothing is saved: removing the mod restores vanilla.
local config = require "config"
local LOG = config.Log and io.open("PackPileGrab_log.txt", "a") or nil
local function w(s) if LOG then LOG:write(string.format("[%.2f] %s\n", os.clock(), s)); LOG:flush() end end

local key = Key[config.GrabKey]
if not key then w("unknown GrabKey " .. tostring(config.GrabKey)); return end
if not config.WholePilePickup then w("WholePilePickup=false, mod idle"); return end

-- How we find out whether the grab key is held:
--  1) preferred: ask the game's PlayerController whether the key is physically down right now
--  2) backup: a short timer after the key press event (used until method 1 has proven it works)
local latchUntil = 0
RegisterKeyBind(key, function() latchUntil = os.clock() + config.FallbackHoldSeconds end)

local pcRef = nil
local trusted = false          -- true once IsInputKeyDown has reported "down" at least once
local variant = nil            -- which call style works
local function getController()
    if pcRef and pcall(function() return pcRef:IsValid() end) and pcRef:IsValid() then return pcRef end
    pcRef = FindFirstOf("PlayerController")
    return pcRef
end
local function keyDown()       -- must run on the game thread; returns true / false / nil (unavailable)
    local pc = getController()
    if not pc then return nil end
    local tries = {
        function() return pc:IsInputKeyDown({KeyName = FName(config.GrabKey)}) end,
        function() return pc:IsInputKeyDown({KeyName = config.GrabKey}) end,
    }
    if variant then
        local ok, r = pcall(tries[variant]); if ok and type(r) == "boolean" then return r end
        return nil
    end
    for i, f in ipairs(tries) do
        local ok, r = pcall(f)
        if ok and type(r) == "boolean" then variant = i; return r end
    end
    return nil
end
local function grabHeld()      -- game thread
    local down = keyDown()
    if down == true then
        if not trusted then trusted = true; w("IsInputKeyDown works (call style " .. tostring(variant) .. "): exact key detection active") end
        return true
    end
    if trusted then return false end                     -- exact method proven: believe it
    return os.clock() < latchUntil                       -- not proven yet: timer backup
end

local current = nil   -- true = vanilla partial pickup, false = whole pile; last mode requested

local function setPile(pile, partial)
    pcall(function()
        if pile:IsValid() then
            local pc = pile.PickupComponent
            if pc and pc:IsValid() and pc.bPartialPickupFromComposition ~= partial then
                pc.bPartialPickupFromComposition = partial
            end
        end
    end)
end
local function applyAll(partial)
    for _, pile in ipairs(FindAllOf("BP_MoneyPackPile_C") or {}) do setPile(pile, partial) end
end

-- piles that appear later (spawned / loaded) start in the mode that is current right now
ExecuteInGameThreadAfterFrames(120, function()
    pcall(function()
        NotifyOnNewObject("/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C", function(pile)
            ExecuteInGameThreadAfterFrames(10, function()
                if current ~= nil then setPile(pile, current) end
            end)
        end)
    end)
end)

-- main loop: switch mode when the key state changes, and re-sweep every ~3 s as a safety net
local tick = 0
LoopAsync(40, function()
    ExecuteInGameThread(function()
        local wantPartial = not grabHeld()
        tick = tick + 1
        local changed = (wantPartial ~= current)
        if changed or tick % 75 == 0 then
            current = wantPartial
            applyAll(wantPartial)
            if changed then w("mode -> " .. (wantPartial and "vanilla (plain click)" or "whole pile (grab key held)")) end
        end
    end)
    return false
end)

-- diagnostics only: note which mode was active at each left click
if LOG then
    pcall(function()
        RegisterKeyBind(Key.LEFT_MOUSE_BUTTON, function()
            w("left click while mode = " .. (current == false and "WHOLE PILE" or "vanilla"))
        end)
    end)
end

w("PackPileGrab 1.2.0 loaded; key detection = IsInputKeyDown with timer backup until proven")
