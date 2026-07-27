-- DMS KUKSA -> AAOS VHAL bridge for Phase 05.2.
local PROP = {
    SPEED = 291504647,
    RISK = 557843456,
    SEVERITY = 559940617,
    DRIVER_STATE = 559940618,
    ALERTNESS = 555746306,
    TTC = 555746307,
    CRITICAL = 555746305,
    AI_STATUS = 555746308,
    ACTION = 555746309,
}

local severity_code = { SAFE = 0, WARNING = 1, CRITICAL = 2, RECOVERY = 3 }
local driver_code = { alert = 0, drowsy = 1, yawning = 2, distracted = 3, microsleep = 4 }
local ai_code = { ONLINE = 0, DEGRADED = 1, OFFLINE = 2 }
local action_code = { NONE = 0, FOCUS_FORWARD = 1, TAKE_BREAK = 2, BRAKE_SAFE = 3, REDUCE_SPEED = 4 }

local mapping = {
    ["Vehicle.Speed"] = { prop = PROP.SPEED },
    ["Vehicle.ADAS.FinalRiskScore"] = { prop = PROP.RISK },
    ["Vehicle.ADAS.DisplaySeverity"] = { prop = PROP.SEVERITY, convert = function(v) return severity_code[v] or 0 end },
    ["Vehicle.Driver.State"] = { prop = PROP.DRIVER_STATE, convert = function(v) return driver_code[v] or 0 end },
    ["Vehicle.Driver.AlertnessScore"] = { prop = PROP.ALERTNESS },
    ["Vehicle.ADAS.MinTTC"] = { prop = PROP.TTC },
    ["Vehicle.ADAS.CriticalAlert"] = { prop = PROP.CRITICAL, convert = function(v) return v and 1 or 0 end },
    ["Vehicle.ADAS.AIStatus"] = { prop = PROP.AI_STATUS, convert = function(v) return ai_code[v] or 2 end },
    ["Vehicle.ADAS.RecommendedActionCode"] = { prop = PROP.ACTION, convert = function(v) return action_code[v] or 0 end },
}

local paths = {}
for path, _ in pairs(mapping) do paths[#paths + 1] = path end

pins.kuksa:on_change(function(ev)
    local target = mapping[ev.path]
    if not target or ev.value == nil then return end
    local value = target.convert and target.convert(ev.value) or ev.value
    pins.vhal:push(target.prop, 0, value)
    log(string.format("DMS_HMI %s=%s -> 0x%08X", ev.path, tostring(value), target.prop))
end)

pins.kuksa:subscribe(paths)
log(string.format("DMS HMI bridge subscribed to %d paths", #paths))
