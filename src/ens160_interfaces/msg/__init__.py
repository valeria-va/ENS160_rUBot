try:
    # Standard ROS2 generated name
    from ._SensorData import SensorData
except ImportError:
    try:
        # Alternate standard name (no underscore)
        from .SensorData import SensorData
    except ImportError:
        # Fallback for lowercased name
        try:
            from .sensor_data import SensorData
        except ImportError:
            # If everything fails, do nothing; the build system will error later.
            pass