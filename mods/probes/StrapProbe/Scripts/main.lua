-- StrapProbe: press F6 in-game (after loading a save) to print the TapeColorA/B values the game
-- currently has loaded for the EUR pack materials. Output appears in the UE4SS console.
local targets = {
    "MI_MoneyPack_USD05", "MI_MoneyPack_USD10", "MI_MoneyPack_USD20", "MI_MoneyPack_USD50", "MI_MoneyPack_USD100",
    "MI_MoneyPack_EUR05", "MI_MoneyPack_EUR10", "MI_MoneyPack_EUR20", "MI_MoneyPack_EUR50", "MI_MoneyPack_EUR100", "MI_MoneyPack_EUR200",
    "MI_MoneyPack_GBP5", "MI_MoneyPack_GBP10", "MI_MoneyPack_GBP20", "MI_MoneyPack_GBP50",
    "MI_MoneyPack_JPY1000", "MI_MoneyPack_JPY5000", "MI_MoneyPack_JPY10000",
}

local function probe(name)
    local path = "/Game/Art/Money/" .. name .. "." .. name
    local mi = StaticFindObject(path)
    if mi == nil or not mi:IsValid() then
        local ok, res = pcall(LoadAsset, "/Game/Art/Money/" .. name)
        mi = StaticFindObject(path)
    end
    if mi == nil or not mi:IsValid() then
        print(string.format("[StrapProbe] %s: NOT FOUND / not loaded\n", name))
        return
    end
    local ok, err = pcall(function()
        mi.VectorParameterValues:ForEach(function(index, elem)
            local v = elem:get()
            local pname = v.ParameterInfo.Name:ToString()
            if pname == "TapeColorA" or pname == "TapeColorB" then
                local c = v.ParameterValue
                print(string.format("[StrapProbe] %s %s = (%.4f, %.4f, %.4f)\n", name, pname, c.R, c.G, c.B))
            end
        end)
    end)
    if not ok then print(string.format("[StrapProbe] %s: error reading params: %s\n", name, tostring(err))) end
end

RegisterKeyBind(Key.F6, function()
    ExecuteInGameThread(function()
        print("[StrapProbe] ---- begin ----\n")
        for _, n in ipairs(targets) do probe(n) end
        print("[StrapProbe] ---- end ----\n")
    end)
end)
print("[StrapProbe] loaded - press F6 in-game\n")
