// Haversine formula to calculate distance between two lat/lon points
export function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371; // Earth's radius in km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) *
      Math.cos(toRad(lat2)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return Math.round(distance * 100) / 100; // Round to 2 decimal places
}

function toRad(degrees: number): number {
  return degrees * (Math.PI / 180);
}

export function calculateETA(params: {
  avgPrepTime: number;
  additionalPrepTime: number;
  distanceKm: number;
  isPeakHour?: boolean;
}): number {
  const { avgPrepTime, additionalPrepTime, distanceKm, isPeakHour = false } = params;
  
  // Base preparation time
  const prepTime = avgPrepTime + additionalPrepTime;
  
  // Queue waiting time (higher during peak hours)
  const queueTime = isPeakHour ? 7 : 1;
  
  // Travel time (4 min per km, +50% during peak traffic)
  const baseTravel = distanceKm * 4;
  const travelTime = isPeakHour ? baseTravel * 1.5 : baseTravel;
  
  return Math.round(prepTime + queueTime + travelTime);
}

export function simulateActualDelivery(predictedETA: number): number {
  // Simulate real delivery with variance (-10 to +20 minutes)
  const variance = Math.random() * 30 - 10;
  return Math.max(5, Math.round(predictedETA + variance));
}
