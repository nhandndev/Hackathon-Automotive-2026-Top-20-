import sampleData from './T01-Sample.json';
import { TripData } from '../types';

const baseTrip = sampleData as unknown as TripData;

// Organizer-provided BTC trip data with only the original sample trip.
export const btcTripData: TripData[] = [
  baseTrip,
];
