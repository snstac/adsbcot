"""Geofencing functionality for ADSBCOT."""

from typing import Dict, Tuple, Optional
from geopy.distance import geodesic

class Geofence:
    """Geofence class for filtering aircraft based on location and altitude."""

    def __init__(self, config: Dict) -> None:
        """Initialize geofence with configuration.
        
        Parameters
        ----------
        config : dict
            Configuration dictionary containing geofence settings
        """
        self.enabled = config.getboolean("GEOFENCE_ENABLED", False)
        self.center: Tuple[float, float] = (
            float(config.get("GEOFENCE_LAT", "0.0")),
            float(config.get("GEOFENCE_LON", "0.0"))
        )
        self.radius_nm = float(config.get("GEOFENCE_RADIUS_NM", "50.0"))
        self.min_alt = float(config.get("MIN_ALTITUDE", "0.0"))
        self.max_alt = float(config.get("MAX_ALTITUDE", "50000.0"))

    def is_in_geofence(self, lat: float, lon: float, alt: float) -> bool:
        """Check if a point is within the geofence and altitude limits.
        
        Parameters
        ----------
        lat : float
            Latitude of the point
        lon : float
            Longitude of the point
        alt : float
            Altitude of the point in feet
        
        Returns
        -------
        bool
            True if the point is within the geofence and altitude limits
        """
        if not self.enabled:
            return True

        if not lat or not lon or not alt:
            return False

        point = (float(lat), float(lon))
        distance_nm = geodesic(self.center, point).nautical
        
        return (distance_nm <= self.radius_nm and
                float(alt) >= self.min_alt and
                float(alt) <= self.max_alt)

    def to_dict(self) -> Dict:
        """Convert geofence settings to dictionary.
        
        Returns
        -------
        dict
            Dictionary containing geofence settings
        """
        return {
            "enabled": self.enabled,
            "center_lat": self.center[0],
            "center_lon": self.center[1],
            "radius_nm": self.radius_nm,
            "min_alt": self.min_alt,
            "max_alt": self.max_alt
        } 