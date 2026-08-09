-- DMS KUKSA -> AAOS HMI bridge, dual-push edition.
--
-- Pushes every DMS signal to:
-- 1) Custom VHAL properties used by the current blueprint.
-- 2) PERF_VEHICLE_SPEED as a decimal multiplex fallback used by APK V2.2.
--
-- Use this in CarSky Script Node: DMS HMI Bridge > Edit Script.

local PROP_SPEED = 291504647 -- 0x11600207, PERF_VEHICLE_SPEED fallback

local PROPS = {
    final_risk = 557843456,     -- 0x21400400
    critical_alert = 555746305, -- 0x21200401
    alertness = 559940610,      -- 0x21600402
    min_ttc = 559940611,        -- 0x21600403
    ai_status = 557843460,      -- 0x21400404
    action = 557843461,         -- 0x21400405
    severity = 557843465,       -- 0x21400409
    driver_state = 557843466,   -- 0x2140040A
}

local severity_code = { SAFE = 0, WARNING = 1, CRITICAL = 2, RECOVERY = 3 }
local driver_code = { alert = 0, drowsy = 1, yawning = 2, distracted = 3, microsleep = 4 }
local ai_code = { ONLINE = 0, DEGRADED = 1, OFFLINE = 2 }
local action_code = { NONE = 0, FOCUS_FORWARD = 1, TAKE_BREAK = 2, BRAKE_SAFE = 3, REDUCE_SPEED = 4 }

local function bool_code(v)
    return (v == true or v == 1 or v == "1" or v == "true" or v == "TRUE") and 1 or 0
end

local function round(v)
    return math.floor((tonumber(v) or 0) + 0.5)
end

local mapping = {
    ["Vehicle.Speed"] = {
        prop = PROP_SPEED,
        custom = function(v) return tonumber(v) or 0 end,
        mux = function(v) return tonumber(v) or 0 end,
    },
    ["Vehicle.ADAS.FinalRiskScore"] = {
        prop = PROPS.final_risk,
        custom = function(v) return tonumber(v) or 0 end,
        mux = function(v) return 41.000 + (round(v) / 1000.0) end,
    },
    ["Vehicle.ADAS.DisplaySeverity"] = {
        prop = PROPS.severity,
        custom = function(v) return severity_code[v] or 0 end,
        mux = function(v) return 42.000 + ((severity_code[v] or 0) / 1000.0) end,
    },
    ["Vehicle.Driver.State"] = {
        prop = PROPS.driver_state,
        custom = function(v) return driver_code[v] or 0 end,
        mux = function(v) return 43.000 + ((driver_code[v] or 0) / 1000.0) end,
    },
    ["Vehicle.Driver.AlertnessScore"] = {
        prop = PROPS.alertness,
        custom = function(v) return tonumber(v) or 0 end,
        mux = function(v) return 44.000 + (round((tonumber(v) or 0) * 100) / 1000.0) end,
    },
    ["Vehicle.ADAS.MinTTC"] = {
        prop = PROPS.min_ttc,
        custom = function(v) return tonumber(v) or 0 end,
        mux = function(v) return 45.000 + (round((tonumber(v) or 0) * 10) / 1000.0) end,
    },
    ["Vehicle.ADAS.CriticalAlert"] = {
        prop = PROPS.critical_alert,
        custom = bool_code,
        mux = function(v) return 46.000 + (bool_code(v) / 1000.0) end,
    },
    ["Vehicle.ADAS.AIStatus"] = {
        prop = PROPS.ai_status,
        custom = function(v) return ai_code[v] or 2 end,
        mux = function(v) return 47.000 + ((ai_code[v] or 2) / 1000.0) end,
    },
    ["Vehicle.ADAS.RecommendedActionCode"] = {
        prop = PROPS.action,
        custom = function(v) return action_code[v] or 0 end,
        mux = function(v) return 48.000 + ((action_code[v] or 0) / 1000.0) end,
    },
}

local paths = {}
for path, _ in pairs(mapping) do
    paths[#paths + 1] = path
end

pins.kuksa:on_change(function(ev)
    local target = mapping[ev.path]
    if not target or ev.value == nil then return end

    local custom_value = target.custom(ev.value)
    local mux_value = target.mux(ev.value)

    pins.vhal:push(target.prop, 0, custom_value)

    if target.prop ~= PROP_SPEED then
        pins.vhal:push(PROP_SPEED, 0, mux_value)
    end

    log(string.format(
        "DMS_HMI_DUAL %s=%s -> custom 0x%08X=%s | mux 0x%08X=%s",
        ev.path,
        tostring(ev.value),
        target.prop,
        tostring(custom_value),
        PROP_SPEED,
        tostring(mux_value)
    ))
end)

pins.kuksa:subscribe(paths)
log(string.format("DMS HMI dual-push bridge subscribed to %d paths", #paths))
