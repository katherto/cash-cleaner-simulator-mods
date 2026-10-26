-- PileLive: change pile pickup settings live, no restart.
--  F8  : print every pile (id, bill/pack count AtomicStatesCount, pickup settings) + subsystem thresholds.
--  F9  : cycle PartialPickupRule (0..5) on ALL piles. Then grab a pile that normally breaks.
--  NUMPAD 1 : toggle bPartialPickupFromComposition on ALL piles.
--  NUMPAD 2 : toggle bForceGrabOnSinglePickup on ALL piles.
-- Newly created piles get the current settings too. Output: console + PileLive_log.txt
local LOG = io.open("PileLive_log.txt", "a")
local function w(s) if LOG then LOG:write(s .. "\n"); LOG:flush() end; print("[PileLive] " .. s) end
local function nm(o) local ok, v = pcall(function() return o:GetFName():ToString() end) return ok and v or "?" end
local function rd(o, k) local ok, v = pcall(function() return o[k] end) if not ok then return "ERR" end return tostring(v) end
local S = { rule = nil, fromComp = nil, force = nil }

local function apply(o)
    local ok, pc = pcall(function() return o.PickupComponent end)
    if not ok or not pc or not pc:IsValid() then return end
    if S.rule ~= nil then pcall(function() pc.PartialPickupRule = S.rule end) end
    if S.fromComp ~= nil then pcall(function() pc.bPartialPickupFromComposition = S.fromComp end) end
    if S.force ~= nil then pcall(function() pc.bForceGrabOnSinglePickup = S.force end) end
end
local CLASSES = {"BP_MoneyPackPile_C", "BP_MoneyPile_C"}
local function applyAll()
    for _, cn in ipairs(CLASSES) do
        for _, o in ipairs(FindAllOf(cn) or {}) do apply(o) end
    end
end
local function loc(o)
    local ok, l = pcall(function() return o:K2_GetActorLocation() end)
    if ok and l then return l.X, l.Y, l.Z end
end
local function report()
    w("=== piles, NEAREST FIRST (stand next to one pile; the first line is that pile) ===")
    local sys = FindFirstOf("BP_InteractiveObjectSubsystem_C")
    if sys and sys:IsValid() then
        w("thresholds: MoneyPacksToPile=" .. rd(sys, "MoneyPacksToPile") .. " PileToMoneyPacks=" .. rd(sys, "PileToMoneyPacks"))
    end
    local px, py, pz, src
    -- try every plausible "where is the player" source, in order
    for _, pc0 in ipairs(FindAllOf("PlayerController") or {}) do
        if pc0:IsValid() and not px then
            local okc, cm = pcall(function() return pc0.PlayerCameraManager end)
            if okc and cm and cm:IsValid() then
                local okl, l = pcall(function() return cm:GetCameraLocation() end)
                if okl and l and (l.X ~= 0 or l.Y ~= 0 or l.Z ~= 0) then px, py, pz, src = l.X, l.Y, l.Z, "camera" end
            end
            if not px then
                local okp, pawn = pcall(function() return pc0:K2_GetPawn() end)
                if okp and pawn and pawn:IsValid() then
                    local x, y, z = loc(pawn)
                    if x then px, py, pz, src = x, y, z, "pawn " .. nm(pawn) end
                end
            end
        end
    end
    if px then w(string.format("you are at (%.0f, %.0f, %.0f) via %s", px, py, pz, src)) else w("(could not find your position)") end
    -- loose packs / other money objects near you
    local near = {}
    for _, cn in ipairs({"BP_MoneyPack_C", "BP_MoneyPile_C", "BP_MoneyBill_C", "BP_MoneyStack_C"}) do
        local n, n3, n10, nearest = 0, 0, 0, 1e12
        for _, o in ipairs(FindAllOf(cn) or {}) do
            n = n + 1
            local x, y, z = loc(o)
            if px and x then
                local d = math.sqrt((x-px)^2 + (y-py)^2 + (z-pz)^2) / 100
                if d < 3 then n3 = n3 + 1 end
                if d < 10 then n10 = n10 + 1 end
                if d < nearest then nearest = d end
            end
        end
        w(string.format("%s: total=%d within3m=%d within10m=%d nearest=%.1fm", cn, n, n3, n10, nearest < 1e11 and nearest or -1))
    end
    -- every interactive object within 3m, grouped by class
    if px then
        local byClass, total = {}, 0
        for _, o in ipairs(FindAllOf("InteractiveObject") or {}) do
            local x, y, z = loc(o)
            if x and math.sqrt((x-px)^2 + (y-py)^2 + (z-pz)^2) < 300 then
                local cn = "?"
                pcall(function() cn = o:GetClass():GetFName():ToString() end)
                byClass[cn] = (byClass[cn] or 0) + 1; total = total + 1
            end
        end
        w("interactive objects within 3m: total=" .. total)
        for cn, n in pairs(byClass) do w("   " .. cn .. " x" .. n) end
    end
    -- the pack-pile class (the one we actually care about)
    for _, o in ipairs(FindAllOf("BP_MoneyPackPile_C") or {}) do
        local x, y, z = loc(o)
        local d = (px and x) and math.sqrt((x-px)^2 + (y-py)^2 + (z-pz)^2) / 100 or -1
        local line = string.format("PACKPILE %s dist=%.1fm", nm(o), d)
        for _, pn in ipairs({"PickupComponent", "CompositionComponent", "VolumeComponent"}) do
            local okp, comp = pcall(function() return o[pn] end)
            if okp and comp and comp:IsValid() then
                if pn == "PickupComponent" then
                    for _, k in ipairs({"PartialPickupRule","PartialPickupOrder","bPartialPickupFromComposition","bSupportsPartialPickupGrouping","bForceGrabOnSinglePickup","bPickUpBlocked"}) do line = line .. " " .. k .. "=" .. rd(comp, k) end
                elseif pn == "CompositionComponent" then
                    for _, k in ipairs({"AtomicStatesCount","MaxInnerStatesCount","bMaxInnerStatesCountSet"}) do line = line .. " " .. k .. "=" .. rd(comp, k) end
                end
            end
        end
        w(line)
        -- own properties/functions of the class (once per F8)
        local okc, cls = pcall(function() return o:GetClass() end)
        if okc and cls then
            local c, dd = cls, 0
            while c and dd < 3 do
                local oki = pcall(function() return c:IsValid() end)
                if not oki or not c:IsValid() then break end
                w("  CLASS " .. c:GetFullName())
                pcall(function() c:ForEachProperty(function(p) local t = "?"; pcall(function() t = p:GetClass():GetFName():ToString() end); w("    prop " .. nm(p) .. " : " .. t) end) end)
                pcall(function() c:ForEachFunction(function(fn) w("    func " .. nm(fn)) end) end)
                local nx; pcall(function() nx = c:GetSuperStruct() end); c = nx; dd = dd + 1
                if c and c:GetFullName():find("/Script/CashCleanerSim.InteractiveObject") then break end
            end
        end
    end
    local list = {}
    for _, o in ipairs(FindAllOf("BP_MoneyPile_C") or {}) do
        local d = 1e12
        local x, y, z = loc(o)
        if px and x then d = math.sqrt((x-px)^2 + (y-py)^2 + (z-pz)^2) end
        list[#list+1] = {o = o, d = d}
    end
    table.sort(list, function(a, b) return a.d < b.d end)
    for i, e in ipairs(list) do
        if i > 8 then break end
        local o = e.o
        local ox, oy, oz = loc(o)
        local s = string.format("#%d %s dist=%.1fm at(%.0f,%.0f,%.0f)", i, nm(o), e.d / 100, ox or 0, oy or 0, oz or 0)
        local okp, pc = pcall(function() return o.PickupComponent end)
        if okp and pc and pc:IsValid() then
            s = s .. " rule=" .. rd(pc, "PartialPickupRule") .. " fromComp=" .. rd(pc, "bPartialPickupFromComposition") .. " force=" .. rd(pc, "bForceGrabOnSinglePickup")
        end
        local okc, cc = pcall(function() return o.CompositionComponent end)
        if okc and cc and cc:IsValid() then s = s .. " count=" .. rd(cc, "AtomicStatesCount") end
        w(s)
    end
end

RegisterKeyBind(Key.F8, function() ExecuteInGameThreadAfterFrames(1, report) end)
local function current(k)
    for _, cn in ipairs({"BP_MoneyPackPile_C", "BP_MoneyPile_C"}) do
      for _, o in ipairs(FindAllOf(cn) or {}) do
        local ok, pc = pcall(function() return o.PickupComponent end)
        if ok and pc and pc:IsValid() then
            local ok2, v = pcall(function() return pc[k] end)
            if ok2 then return v end
        end
      end
    end
end
RegisterKeyBind(Key.F9, function() ExecuteInGameThreadAfterFrames(1, function()
    local cur = S.rule; if cur == nil then cur = tonumber(current("PartialPickupRule")) or 3 end
    S.rule = (cur + 1) % 6; applyAll(); w("PartialPickupRule -> " .. S.rule .. " on all piles") end) end)
RegisterKeyBind(Key.NUM_ONE, function() ExecuteInGameThreadAfterFrames(1, function()
    local cur = S.fromComp; if cur == nil then cur = current("bPartialPickupFromComposition") end
    S.fromComp = not cur; applyAll(); w("bPartialPickupFromComposition -> " .. tostring(S.fromComp)) end) end)
RegisterKeyBind(Key.NUM_TWO, function() ExecuteInGameThreadAfterFrames(1, function()
    local cur = S.force; if cur == nil then cur = current("bForceGrabOnSinglePickup") end
    S.force = not cur; applyAll(); w("bForceGrabOnSinglePickup -> " .. tostring(S.force)) end) end)

local function setThreshold(v)
    local sys = FindFirstOf("BP_InteractiveObjectSubsystem_C")
    if sys and sys:IsValid() then
        pcall(function() sys.MoneyPacksToPile = v end)
        w("MoneyPacksToPile -> " .. rd(sys, "MoneyPacksToPile") .. "  (PileToMoneyPacks=" .. rd(sys, "PileToMoneyPacks") .. ")")
    else w("subsystem not found") end
end
-- TEST HELPERS: Numpad 3 = loose packs re-pile at 55+ (so you can rebuild test piles fast), Numpad 4 = back to vanilla 101
RegisterKeyBind(Key.NUM_THREE, function() ExecuteInGameThreadAfterFrames(1, function() setThreshold(55) end) end)
RegisterKeyBind(Key.NUM_FOUR, function() ExecuteInGameThreadAfterFrames(1, function() setThreshold(101) end) end)

ExecuteInGameThreadAfterFrames(120, function()
    pcall(function()
        NotifyOnNewObject("/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C", function(o)
            ExecuteInGameThreadAfterFrames(5, function() if o:IsValid() then apply(o) end end)
        end)
        NotifyOnNewObject("/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C", function(o)
            ExecuteInGameThreadAfterFrames(5, function() if o:IsValid() then apply(o) end end)
        end)
    end)
end)
w("ready. F8 report, F9 cycle rule, NUMPAD1 fromComposition, NUMPAD2 forceGrab, NUMPAD3 re-pile threshold 55, NUMPAD4 vanilla 101")


local STRUCT_PATHS = {"/Script/CashCleanerSim.InteractiveObjectPartialPickupRequest"}
local dumpedOnce = false
local function describeRequest(argParam)
    local okv, v = pcall(function() return argParam:get() end)
    if not okv then w("  request: cannot read arg"); return end
    if not dumpedOnce then
        dumpedOnce = true
        for _, sp in ipairs(STRUCT_PATHS) do
            local oks, st = pcall(function() return StaticFindObject(sp) end)
            if oks and st and st:IsValid() then
                w("  STRUCT " .. sp)
                pcall(function() st:ForEachProperty(function(p)
                    local t = "?"; pcall(function() t = p:GetClass():GetFName():ToString() end)
                    w("    field " .. nm(p) .. " : " .. t) end) end)
            else w("  struct not found: " .. sp) end
        end
        local okf, fn = pcall(function() return StaticFindObject("/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C:HandlePartialPickup") end)
        if okf and fn and fn:IsValid() then
            w("  FUNCTION HandlePartialPickup params:")
            pcall(function() fn:ForEachProperty(function(p)
                local t = "?"; pcall(function() t = p:GetClass():GetFName():ToString() end)
                w("    param " .. nm(p) .. " : " .. t) end) end)
        else w("  function object not found") end
    end
    for _, sp in ipairs(STRUCT_PATHS) do
        local oks, st = pcall(function() return StaticFindObject(sp) end)
        if oks and st and st:IsValid() then
            local line = "  request:"
            pcall(function() st:ForEachProperty(function(p)
                local name = nm(p)
                local okr, val = pcall(function() return v[name] end)
                local sv = okr and val or "?"
                if type(sv) == "userdata" then local o2, s2 = pcall(function() return sv:GetFullName() end); sv = o2 and s2 or "obj" end
                line = line .. " " .. name .. "=" .. tostring(sv) end) end)
            w(line)
        end
    end
end

-- Logging hooks on the pack-pile class (retry until the class is loaded). CheckComposition is too noisy to log.
local HOOKS = {
 "/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C:HandlePartialPickup",
 "/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C:Split",
 "/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C:OnSplitRequested",
 "/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C:UpdateDenomination",
 "/Game/Core/Objects/BP_MoneyPackPile.BP_MoneyPackPile_C:HandleCombination",
}
local hooked = {}
LoopAsync(5000, function()
    local left = 0
    for _, p in ipairs(HOOKS) do
        if not hooked[p] then
            local ok = pcall(function()
                RegisterHook(p, function(self, ...)
                    local fn = p:match(":(.+)$")
                    local s2 = "CALL " .. fn .. " on " .. nm(self:get())
                    local okc, cnt = pcall(function() return self:get().CompositionComponent.AtomicStatesCount end)
                    if okc then s2 = s2 .. " count=" .. tostring(cnt) end
                    for i, a in ipairs({...}) do
                        local okv, v = pcall(function() return a:get() end)
                        s2 = s2 .. " | a" .. i .. "=" .. tostring(okv and (type(v) == "userdata" and nm(v) or v) or "?")
                    end
                    w(s2)
                    if p:find("HandlePartialPickup") then
                        local args = {...}
                        if args[1] then describeRequest(args[1]) end
                    end
                end, function(self, ...)
                    local rv = ({...})[1]
                    if rv ~= nil then
                        local okv, v = pcall(function() return rv:get() end)
                        w("  RET " .. p:match(":(.+)$") .. " = " .. tostring(okv and (type(v) == "userdata" and nm(v) or v) or "?"))
                    end
                end)
            end)
            if ok then hooked[p] = true; w("hooked " .. p) else left = left + 1 end
        end
    end
    return left == 0
end)
