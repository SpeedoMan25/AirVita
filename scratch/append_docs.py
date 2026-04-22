import os

files_to_update = [
    r"c:\Projects\HackAugie\backend\README.md",
    r"c:\Projects\HackAugie\frontend\README.md",
    r"c:\Projects\HackAugie\pico\README.md",
    r"c:\Projects\HackAugie\pi4B\README.md",
    r"c:\Projects\HackAugie\backend\model\README.md",
    r"c:\Projects\HackAugie\scanner\README.md",
    r"c:\Projects\HackAugie\DEPLOYMENT.md",
    r"c:\Projects\HackAugie\API.md",
    r"c:\Projects\HackAugie\PICO_BRIDGE.md"
]

append_text = """

---

## 🔗 Related Documentation

- **[Project Overview](file:///c:/Projects/HackAugie/README.md)**: Main architecture and quick start.
- **[API Reference](file:///c:/Projects/HackAugie/API.md)**: Data schema for the telemetry endpoint.
- **[Deployment Guide](file:///c:/Projects/HackAugie/DEPLOYMENT.md)**: Docker and startup scripts.
"""

for file_path in files_to_update:
    if os.path.exists(file_path):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(append_text)
        print(f"Appended to {file_path}")
    else:
        print(f"Not found: {file_path}")
