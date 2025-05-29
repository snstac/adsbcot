"""Web interface for ADSBCOT configuration."""

import os
from typing import Dict
from flask import Flask, render_template, request, jsonify
from configparser import ConfigParser

app = Flask(__name__)

def get_config() -> ConfigParser:
    """Get the current configuration."""
    config = ConfigParser()
    config_path = os.getenv("ADSBCOT_CONFIG", "adsbcot.ini")
    if os.path.exists(config_path):
        config.read(config_path)
    return config

def save_config(config: ConfigParser) -> None:
    """Save the configuration."""
    config_path = os.getenv("ADSBCOT_CONFIG", "adsbcot.ini")
    with open(config_path, "w") as f:
        config.write(f)

@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")

@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current settings."""
    config = get_config()
    settings = {
        "geofence_enabled": config.getboolean("GEOFENCE", "enabled", fallback=False),
        "geofence_lat": config.getfloat("GEOFENCE", "lat", fallback=0.0),
        "geofence_lon": config.getfloat("GEOFENCE", "lon", fallback=0.0),
        "geofence_radius_nm": config.getfloat("GEOFENCE", "radius_nm", fallback=50.0),
        "min_altitude": config.getfloat("GEOFENCE", "min_alt", fallback=0.0),
        "max_altitude": config.getfloat("GEOFENCE", "max_alt", fallback=50000.0),
    }
    return jsonify(settings)

@app.route("/api/settings", methods=["POST"])
def update_settings():
    """Update settings."""
    try:
        data = request.json
        config = get_config()
        
        if "GEOFENCE" not in config:
            config.add_section("GEOFENCE")
            
        config["GEOFENCE"]["enabled"] = str(data.get("geofence_enabled", False))
        config["GEOFENCE"]["lat"] = str(data.get("geofence_lat", 0.0))
        config["GEOFENCE"]["lon"] = str(data.get("geofence_lon", 0.0))
        config["GEOFENCE"]["radius_nm"] = str(data.get("geofence_radius_nm", 50.0))
        config["GEOFENCE"]["min_alt"] = str(data.get("min_altitude", 0.0))
        config["GEOFENCE"]["max_alt"] = str(data.get("max_altitude", 50000.0))
        
        save_config(config)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000) 