-- PileTrace v2. F8 = report every money pile (pack counts + pickup settings). Hooks retry until the pile class is loaded.
local LOG = io.open("PileTrace2_log.txt", "a")
local function w(s) if LOG then LOG:write(s .. "\n"); LOG:flush() end; print("[PileTrace2] " .. s) end
local function nm(o) local ok, v = pcall(function() return o:GetFName():ToString() end) return ok and v or "?" end
local function full(o) local ok, v = pcall(function() return o:GetFullName() end) return ok and v or "?" end
local function rd(o, k) local ok, v = pcall(function() return o[k] end) if not ok then return "ERR" end
    if type(v) == "userdata" then local o2, s = pcall(function() return v:GetFullName() end) return o2 and s or "obj" end
    return tostring(v) end

local HOOKS = {
 "/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C:Split Requested",
 "/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C:Split",
 "/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C:HandlePartialPickup",
 "/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C:CheckComposition",
 "/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C:OnPickupStatusChangedEvent",
 "/Game/Core/Objects/BP_MoneyPile.BP_MoneyPile_C:UpdateDenomination",
 "/Script/CashCleanerSim.PickupObjectComponent:IsPartialPickupOnGrabEnabled",
 "/Script/CashCleanerSim.PickupObjectComponent:IsPartialPickupOnPickupEnabled",
 "/Script/CashCleanerSim.PickupObjectComponent:IsPartialPickupPossible",
 "/Script/CashCleanerSim.PickupObjectComponent:IsPartialPickupEnabled",
 "/Script/CashCleanerSim.PickupObjectComponent:HandlePartialPickupRequest",
 "/Script/CashCleanerSim.PickupObjectComponent:SetIsPickedUp",
 "/Script/CashCleanerSim.PickupObjectComponent:RedirectPickup",
 "/Script/CashCleanerSim.PickupObjectComponent:OnGrabStateChanged",
 "/Script/CashCleanerSim.PickupObjectComponent:OnCompositionChanged",
 "/Script/CashCleanerSim.CompositionObjectComponent:Split",
 "/Script/CashCleanerSim.CompositionObjectComponent:RemoveLastStates",
 "/Script/CashCleanerSim.CompositionObjectComponent:RemoveFirstStates",
 "/Script/CashCleanerSim.InteractiveObject:ReplaceWith",
}
local done = {}
local function tryHooks()
    local left = 0
    for _, p in ipairs(HOOKS) do
        if not done[p] then
            local ok = pcall(function()
                RegisterHook(p, function(self, ...)
                    local s = "CALL " .. p:match(":(.+)$") .. " on " .. nm(self:get())
                    for i, a in ipairs({...}) do
                        local okv, v = pcall(function() return a:get() end)
                        s = s .. " | a" .. i .. "=" .. tostring(okv and (type(v) == "userdata" and nm(v) or v) or "?")
                    end
                    w(s)
                end, function(self, ...)
                    local rv = ({...})[1]
                    if rv ~= nil then
                        local okv, v = pcall(function() return rv:get() end)
                        w("  RET " .. p:match(":(.+)$") .. " = " .. tostring(okv and v or "?"))
                    end
                end)
            end)
            if ok then done[p] = true; w("hooked " .. p) else left = left + 1 end
        end
    end
    return left
end
LoopAsync(5000, function()
    local left = tryHooks()
    return left == 0   -- stop looping once everything is hooked
end)

local PK = {"PartialPickupRule","PartialPickupOrder","bPartialPickupFromComposition","bSupportsPartialPickupGrouping","bForceGrabOnSinglePickup","bPickUpBlocked","bCustomPickupSettingsSet"}
local CK = {"AtomicStatesCount","MaxInnerStatesCount","bMaxInnerStatesCountSet","ContainerEntryDecompositionPattern"}
RegisterKeyBind(Key.F8, function()
    ExecuteInGameThreadAfterFrames(1, function()
        w("=== F8 pile report ===")
        for _, cn in ipairs({"BP_MoneyPile_C", "BP_MoneyPack_C"}) do
            local objs = FindAllOf(cn) or {}
            w(cn .. " count = " .. #objs)
            for i, o in ipairs(objs) do
                if i > 25 then break end
                local s = nm(o)
                local okp, pc = pcall(function() return o.PickupComponent end)
                if okp and pc and pc:IsValid() then for _, k in ipairs(PK) do s = s .. " " .. k .. "=" .. rd(pc, k) end end
                local okc, cc = pcall(function() return o.CompositionComponent end)
                if okc and cc and cc:IsValid() then for _, k in ipairs(CK) do s = s .. " " .. k .. "=" .. rd(cc, k) end end
                w(s)
            end
        end
        local sys = FindFirstOf("BP_InteractiveObjectSubsystem_C")
        if sys and sys:IsValid() then
            for _, k in ipairs({"MoneyPacksToPile","PileToMoneyPacks","MoneyBillsToPile","PileToMoneyBills","PilingRadius"}) do w("subsystem " .. k .. " = " .. rd(sys, k)) end
        end
        w("=== end ===")
    end)
end)
print("[PileTrace2] ready; F8 = pile report")
