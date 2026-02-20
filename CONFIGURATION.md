# Configuration Layout

`config.json` supports both legacy single-app keys and multi-tool settings.

## Recommended structure

```json
{
  "app_name": "ImageUtils",
  "app_version": "1.0.0",
  "update_url": "",
  "apps": {
    "crop": {
      "app_name": "Image Crop Tool",
      "app_version": "1.0.0",
      "update_url": "https://.../latest.json"
    },
    "resize": {
      "app_name": "Image Resize Tool",
      "app_version": "1.0.0",
      "update_url": "https://.../resize-latest.json"
    }
  }
}
```

## How each tool reads config

Use:

```python
from app_config import load_app_config

CONFIG = load_app_config("crop", {
    "app_name": "Image Crop Tool",
    "app_version": "1.0.0",
    "update_url": "",
})
```

Resolution order:
1. defaults passed in code
2. root-level keys (legacy compatibility)
3. `apps.<tool_name>` keys (highest priority)

So if you add a new file like `resize.py`, use `load_app_config("resize", defaults)` and add an `apps.resize` section.
