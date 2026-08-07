# src/data/saved_trips/

Completed trip JSON files (`{trip_id}.json`) are persisted directly under `src/data/saved_trips/`.

## Architecture & Data Flow

1. **Auto-save on Completion**: When a live trip status changes to `completed`, `App.tsx` calls `POST /api/trips/save` to save the full `TripData` JSON object into `src/data/saved_trips/{trip_id}.json`.
2. **AI Copilot Tracing**: The Express server (`server.ts`) reads all completed trip JSON files in `src/data/saved_trips/` so AI Copilot can trace and analyze historical completed trips.
3. **Vite Watcher Exclusions**: `vite.config.ts` includes `'**/src/data/**'` in `server.watch.ignored` so Vite never hot-reloads when new trip JSON files are saved to this folder.
