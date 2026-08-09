-- DMS HMI Bridge - BTC default VSS passthrough.
--
-- Use this when the KUKSA broker does not include custom DMS VSS paths.
-- Backend sends DMS multiplex values directly to Vehicle.Speed:
--   41.088 = risk 88
--   42.002 = CRITICAL
--   43.004 = microsleep
-- APK V2.2 decodes those decimal speed-mux values.

local PROP_SPEED = 291504647 -- 0x11600207, PERF_VEHICLE_SPEED
local PATH_SPEED = "Vehicle.Speed"

pins.kuksa:on_change(function(ev)
    if ev.path ~= PATH_SPEED or ev.value == nil then return end
    local value = tonumber(ev.value) or 0
    pins.vhal:push(PROP_SPEED, 0, value)
    log(string.format("DMS_HMI_SPEED_MUX %s=%s -> 0x%08X=%s", ev.path, tostring(ev.value), PROP_SPEED, tostring(value)))
end)

pins.kuksa:subscribe({ PATH_SPEED })
log("DMS HMI speed-mux bridge subscribed to Vehicle.Speed")
