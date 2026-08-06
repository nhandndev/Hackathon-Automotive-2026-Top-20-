-- DMS KUKSA -> AAOS HMI bridge.
--
-- CarSky/BTC reference flow:
-- Team Solution -> CarSky Platform/SOVD -> MQTT/Vehicle-HPC -> Android HMI.
--
-- Runtime finding from our CarSky AAOS deployment:
-- Android CarService exposes PERF_VEHICLE_SPEED reliably, while custom DMS
-- properties are not visible to the APK. Therefore this bridge multiplexes DMS
-- state into PERF_VEHICLE_SPEED values. The APK decodes these values back into
-- severity, driver state, risk, TTC, AI status and recommended action.

local PROP_SPEED = 291504647 -- 0x11600207, PERF_VEHICLE_SPEED

local severity_code = { SAFE = 0, WARNING = 1, CRITICAL = 2, RECOVERY = 3 }
local driver_code = { alert = 0, drowsy = 1, yawning = 2, distracted = 3, microsleep = 4 }
local ai_code = { ONLINE = 0, DEGRADED = 1, OFFLINE = 2 }
local action_code = { NONE = 0, FOCUS_FORWARD = 1, TAKE_BREAK = 2, BRAKE_SAFE = 3, REDUCE_SPEED = 4 }

local mapping = {
    ["Vehicle.Speed"] = {
        encode = function(v)
            return tonumber(v) or 0
        end
    },
    ["Vehicle.ADAS.FinalRiskScore"] = {
        encode = function(v)
            return 10000 + math.floor((tonumber(v) or 0) + 0.5)
        end
    },
    ["Vehicle.ADAS.DisplaySeverity"] = {
        encode = function(v)
            return 11000 + (severity_code[v] or 0)
        end
    },
    ["Vehicle.Driver.State"] = {
        encode = function(v)
            return 12000 + (driver_code[v] or 0)
        end
    },
    ["Vehicle.Driver.AlertnessScore"] = {
        encode = function(v)
            return 13000 + math.floor(((tonumber(v) or 0) * 100) + 0.5)
        end
    },
    ["Vehicle.ADAS.MinTTC"] = {
        encode = function(v)
            return 14000 + math.floor(((tonumber(v) or 0) * 10) + 0.5)
        end
    },
    ["Vehicle.ADAS.CriticalAlert"] = {
        encode = function(v)
            return 15000 + ((v == true or v == 1 or v == "true") and 1 or 0)
        end
    },
    ["Vehicle.ADAS.AIStatus"] = {
        encode = function(v)
            return 16000 + (ai_code[v] or 2)
        end
    },
    ["Vehicle.ADAS.RecommendedActionCode"] = {
        encode = function(v)
            return 17000 + (action_code[v] or 0)
        end
    },
}

local paths = {}
for path, _ in pairs(mapping) do paths[#paths + 1] = path end

pins.kuksa:on_change(function(ev)
    local target = mapping[ev.path]
    if not target or ev.value == nil then return end
    local encoded = target.encode(ev.value)
    pins.vhal:push(PROP_SPEED, 0, encoded)
    log(string.format("DMS_HMI_MUX %s=%s -> %s on 0x%08X", ev.path, tostring(ev.value), tostring(encoded), PROP_SPEED))
end)

pins.kuksa:subscribe(paths)
log(string.format("DMS HMI multiplex bridge subscribed to %d paths", #paths))
