param(
    [string]$TargetRoot = "evidence"
)

$ErrorActionPreference = "Stop"
$CommonDirectories = @("commands", "raw", "derived", "visual", "reports")

$EvidencePaths = @(
    "00_index/E-35_reviewer_findability",
    "01_release/E-01_challenge_evaluation_bundle",
    "01_release/E-02_as_is_architecture",
    "01_release/E-04_golden_end_to_end_trace",
    "01_release/E-15_automated_test_traceability",
    "01_release/E-16_failure_handling",
    "01_release/E-18_immutable_release_packet",
    "01_release/E-26_clean_room_build",
    "02_ai_c1/E-13_c1_critical_case_evaluation",
    "03_ai_c2/E-08_c2_model_dependencies",
    "03_ai_c2/E-27_c2_generalization_evaluation",
    "03_ai_c2/E-42_domain_gap_and_drift",
    "04_ai_c3/E-07_c3_formula_and_thresholds",
    "05_orchestrator/E-05_state_policy_lifecycle",
    "05_orchestrator/E-06_frame_alert_vs_event_ablation",
    "06_backend/E-03_decision_event_contract",
    "06_backend/E-14_backend_reliability",
    "06_backend/E-17_operator_intervention_workflow",
    "06_backend/E-36_long_run_load_test",
    "06_backend/E-41_multi_instance_failover",
    "07_dashboard/E-21_report_export_qa",
    "07_dashboard/E-22_dashboard_workflow",
    "07_dashboard/E-23_dashboard_failure_states",
    "08_carla/E-11_dataset_manifest_validation",
    "08_carla/E-12_collection_reproducibility",
    "08_carla/E-37_calibration_audit",
    "08_carla/E-38_scenario_event_matrix",
    "09_edge/E-09_jetson_performance_benchmark",
    "09_edge/E-10_jetson_soak_thermal_power",
    "10_carsky_hmi/E-24_carsky_kuksa_vhal_trace",
    "10_carsky_hmi/E-25_audio_alert_path",
    "10_carsky_hmi/E-39_warning_ux_evaluation",
    "11_copilot/E-19_grounded_output_evaluation",
    "11_copilot/E-20_latency_cost_failure",
    "11_copilot/E-40_review_time_comparison",
    "12_business/E-28_market_sources",
    "12_business/E-29_competitive_analysis",
    "12_business/E-30_pricing_bom_unit_economics",
    "12_business/E-31_customer_interviews",
    "12_business/E-32_pilot_protocol",
    "12_business/E-33_roi_validation",
    "13_safety_privacy/E-34_safety_privacy_gates"
)

foreach ($EvidencePath in $EvidencePaths) {
    foreach ($Subdirectory in $CommonDirectories) {
        $FullPath = Join-Path $TargetRoot (Join-Path $EvidencePath $Subdirectory)
        New-Item -ItemType Directory -Path $FullPath -Force | Out-Null
        New-Item -ItemType File -Path (Join-Path $FullPath ".gitkeep") -Force | Out-Null
    }
}

Write-Host "Created evidence structure at: $TargetRoot"
