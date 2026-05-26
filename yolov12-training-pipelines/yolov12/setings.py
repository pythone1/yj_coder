from ultralytics import settings

# View all settings
print(settings)

# Return a specific setting
value = settings["runs_dir"]

from ultralytics import settings

# Update a setting
settings.update({"runs_dir": r"E:\PY\YOLO\yolov12"})

# Update multiple settings
settings.update({"runs_dir": r"E:\PY\YOLO\yolov12", "tensorboard": False})

# Reset settings to default values
settings.reset()