# E-05 - Alert Orchestrator Explainer

Decision Engine runs after C1/C2/C3. It does not modify the BTC CSV, does not train a model, and does not create new predictions. Its role is to filter signals over time before sending alerts.

Real source files in repo:

- `HACKATHON/AI/configs/decision_engine.yaml`
- `HACKATHON/AI/core/decision_engine/policy.py`
- `HACKATHON/AI/core/decision_engine/engine.py`
- `HACKATHON/AI/core/decision_engine/schemas.py`

Policy groups currently include: TTC, microsleep, distraction, drowsiness, speeding, harsh behavior, risk tiers, sensor health and vigilance lapse.

Note: this evidence proves source structure/policy presence. It does not prove real-world alert quality unless ablation or episode-level replay is added.
