from PIL import Image
from pathlib import Path
import sys

FOLDER = sys.argv[1] if len(sys.argv) > 1 else None

if FOLDER is None: print("Usage: python crop.py <input_folder>"); sys.exit(1)

# Config
input_folder = Path(FOLDER)  # Change to your input folder
output_folder = Path(f"./{input_folder.name}-cropped")

CROP_PIXELS = 175  # Pixels to crop from bottom

# Process all images in subfolders
for ext in ['*.jpg', '*.jpeg', '*.png']:
	for img_path in input_folder.rglob(ext):
		# Create corresponding output directory
		relative_path = img_path.relative_to(input_folder)
		output_path = output_folder / relative_path
		output_path.parent.mkdir(parents=True, exist_ok=True)
		
		# Crop and save
		img = Image.open(img_path)
		width, height = img.size
		cropped = img.crop((0, 0, width, height - CROP_PIXELS))
		cropped.save(
			output_path,
			quality=95,
			subsampling=0,
			optimize=True
		)
		print(f"Cropped: {relative_path}")
