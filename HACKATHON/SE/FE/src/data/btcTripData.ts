import { TripData } from '../types';

/**
 * btcTripData holds completed trip records saved in `src/data/saved_trips/`.
 * When an AI pipeline trip session status transitions to 'completed',
 * the frontend auto-persists the full TripData to `src/data/saved_trips/{trip_id}.json`.
 * Both the Dashboard and AI Copilot read from `src/data/saved_trips/` to trace completed trips.
 */
export const btcTripData: TripData[] = [];
