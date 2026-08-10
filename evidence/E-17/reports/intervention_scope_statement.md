# Intervention Scope Statement - E-17

This project does **not** claim autonomous physical vehicle actuation.

Verified scope:

- Fleet Dashboard operator can send an intervention command (`alarm`, `stop`, `call`).
- Backend stores the command in memory at `/api/v1/alerts/interventions`.
- AI desktop/demo process can poll `/api/v1/alerts/interventions/pending` and render an overlay/message.
- HMI may display recommendation text such as `BRAKE_SAFE` / `BRAKE ASSIST REQUESTED`, but this is a driver/HMI advisory signal in the demo, not proof of physical brake control.

Out of scope / not claimed:

- No production actuator control.
- No direct brake/throttle/steering command.
- No autonomous enforcement of stop/suspension/work order.
- CarSky REST path name `actuate` is used for signal updates; this evidence does not equate it with physical vehicle actuation.
