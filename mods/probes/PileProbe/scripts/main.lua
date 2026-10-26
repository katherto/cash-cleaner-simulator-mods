-- PileProbe: press F7 in-game (ideally while holding a money-pack pile and again with nothing held).
-- Writes a report to PileProbe_report.txt next to the game's Win64 exe and prints a summary to the console.
local KW = {"pile","grab","hold","hand","pick","interactive","carry","moneypack","packs"}
local out = {}
local function log(s) out[#out+1] = s end
local function nm(o) local ok, v = pcall(function() return o:GetFName():ToString() end) return ok and v or "?" end
local function full(o) local ok, v = pcall(function() return o:GetFullName() end) return ok and v or "?" end

local function dumpClass(cls, depth)
    local c, d = cls, 0
    while c and d < 6 do
        local okv = pcall(function() return c:IsValid() end)
        if not okv or not c:IsValid() then break end
        log(string.rep("  ", depth) .. "CLASS " .. full(c))
        pcall(function() c:ForEachProperty(function(p)
            local t = "?"
            pcall(function() t = p:GetClass():GetFName():ToString() end)
            log(string.rep("  ", depth+1) .. "prop " .. nm(p) .. " : " .. t)
        end) end)
        pcall(function() c:ForEachFunction(function(f)
            log(string.rep("  ", depth+1) .. "func " .. nm(f))
        end) end)
        local nxt
        pcall(function() nxt = c:GetSuperStruct() end)
        c = nxt; d = d + 1
        if c and full(c):find("/Script/Engine.Actor") then break end
    end
end

local function matches(name)
    local l = name:lower()
    for _, k in ipairs(KW) do if l:find(k, 1, true) then return true end end
    return false
end

RegisterKeyBind(Key.F7, function()
    ExecuteInGameThreadAfterFrames(1, function()
        out = {}
        log("=== PileProbe report ===")
        -- 1) interactive object subsystem
        local sys = FindFirstOf("BP_InteractiveObjectSubsystem_C")
        if sys and sys:IsValid() then log("--- Subsystem ---"); dumpClass(sys:GetClass(), 0) end
        -- 2) every loaded Blueprint class whose name looks relevant
        local seen = {}
        local classes = FindObjects(0, "BlueprintGeneratedClass", nil, 0, 0, false) or {}
        log("--- Blueprint classes matching keywords ---")
        for _, c in ipairs(classes) do
            local f = full(c)
            local short = nm(c)
            if matches(short) and not seen[f] then
                seen[f] = true
                log("")
                dumpClass(c, 0)
            end
        end
        -- 3) live instances of those classes
        log("--- live instances ---")
        local objs = FindAllOf("Actor") or {}
        for _, o in ipairs(objs) do
            local cn = "?"
            pcall(function() cn = o:GetClass():GetFName():ToString() end)
            if matches(cn) then log(cn .. "  =>  " .. full(o)) end
        end
        local f = io.open("PileProbe_report.txt", "w")
        if f then f:write(table.concat(out, "\n")); f:close() end
        print("[PileProbe] wrote PileProbe_report.txt (" .. #out .. " lines)")
        for i = 1, math.min(#out, 60) do print(out[i]) end
    end)
end)
print("[PileProbe] ready - press F7")
