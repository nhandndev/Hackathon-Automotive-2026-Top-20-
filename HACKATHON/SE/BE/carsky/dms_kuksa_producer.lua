-- DMS internal KUKSA producer for CarSky topology verification.
--
-- Purpose:
-- - Create an in-blueprint producer node so BTC can see data is generated
--   inside CarSky, not only from the external Backend/Mac script.
-- - Publish a deterministic critical DMS scenario into KUKSA.
-- - DMS HMI Bridge should then receive these KUKSA changes and log DMS_HMI_MUX.
--
-- Expected topology:
-- DMS KUKSA Producer -> DMS Signal Broker -> DMS HMI Bridge -> DMS Android HMI
--
-- Node setup:
-- - Type: Script Node
-- - Label: DMS KUKSA Producer
-- - Pin: kuksa, type KUKSA, direction Client/Output depending on CarSky UI wording
-- - Edge: connect Producer.kuksa to DMS Signal Broker.kuksa

local signals = {
    { path = "Vehicle.Speed", value = 75.0 },
    { path = "Vehicle.SpeedLimit", value = 80.0 },
    { path = "Vehicle.Driver.State", value = "microsleep" },
    { path = "Vehicle.Driver.AlertnessScore", value = 0.15 },
    { path = "Vehicle.ADAS.MinTTC", value = 1.2 },
    { path = "Vehicle.ADAS.Headway", value = 0.8 },
    { path = "Vehicle.ADAS.FinalRiskScore", value = 88.0 },
    { path = "Vehicle.ADAS.DisplaySeverity", value = "CRITICAL" },
    { path = "Vehicle.ADAS.CriticalAlert", value = true },
    { path = "Vehicle.ADAS.AlertReasonCode", value = "TTC_CRITICAL" },
    { path = "Vehicle.ADAS.RecommendedActionCode", value = "BRAKE_SAFE" },
    { path = "Vehicle.ADAS.AIStatus", value = "ONLINE" },
    { path = "Vehicle.ADAS.EventTransition", value = "ENTER_CRITICAL" },
    { path = "Vehicle.ADAS.DataAgeMs", value = 40 },
}

local function publish()
    for _, signal in ipairs(signals) do
        pins.kuksa:publish(signal.path, signal.value)
        log(string.format(
            "DMS_KUKSA_PRODUCER %s=%s",
            signal.path,
            tostring(signal.value)
        ))
    end
    log(string.format("DMS KUKSA producer published %d demo signals", #signals))
end

publish()
