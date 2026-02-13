from __future__ import annotations

import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")


class CropApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Image Crop Tool")
        self.geometry("680x420")
        self.resizable(False, False)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.crop_pixels = tk.StringVar(value="175")
        self.status = tk.StringVar(value="Select folders and click Start.")
        self.progress_text = tk.StringVar(value="0 / 0")

        self._build_ui()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Input folder:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.input_dir, width=62).grid(row=1, column=0, sticky="ew")
        ttk.Button(frame, text="Browse", command=self._pick_input).grid(row=1, column=1, padx=(8, 0))

        ttk.Label(frame, text="Output folder:").grid(row=2, column=0, sticky="w", pady=(14, 6))
        ttk.Entry(frame, textvariable=self.output_dir, width=62).grid(row=3, column=0, sticky="ew")
        ttk.Button(frame, text="Browse", command=self._pick_output).grid(row=3, column=1, padx=(8, 0))

        options = ttk.Frame(frame)
        options.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))
        ttk.Label(options, text="Pixels to crop from bottom:").pack(side="left")
        ttk.Entry(options, textvariable=self.crop_pixels, width=8).pack(side="left", padx=(8, 0))

        ttk.Button(frame, text="Start Cropping", command=self._start_crop).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(18, 10)
        )

        self.progress = ttk.Progressbar(frame, mode="determinate", length=520)
        self.progress.grid(row=6, column=0, sticky="ew")
        ttk.Label(frame, textvariable=self.progress_text).grid(row=6, column=1, padx=(8, 0))

        ttk.Label(frame, textvariable=self.status, wraplength=620).grid(
            row=7, column=0, columnspan=2, sticky="w", pady=(14, 0)
        )

        frame.columnconfigure(0, weight=1)

    def _pick_input(self) -> None:
        folder = filedialog.askdirectory(title="Select input folder")
        if not folder:
            return
        self.input_dir.set(folder)
        if not self.output_dir.get().strip():
            input_path = Path(folder)
            self.output_dir.set(str(input_path.parent / f"{input_path.name}-cropped"))

    def _pick_output(self) -> None:
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_dir.set(folder)

    def _start_crop(self) -> None:
        try:
            crop_pixels = int(self.crop_pixels.get().strip())
        except ValueError:
            messagebox.showerror("Invalid input", "Crop pixels must be a whole number.")
            return

        if crop_pixels < 1:
            messagebox.showerror("Invalid input", "Crop pixels must be greater than 0.")
            return

        input_folder = Path(self.input_dir.get().strip())
        output_folder = Path(self.output_dir.get().strip())

        if not input_folder.exists() or not input_folder.is_dir():
            messagebox.showerror("Invalid folder", "Please choose a valid input folder.")
            return

        if not output_folder:
            messagebox.showerror("Invalid folder", "Please choose an output folder.")
            return

        self.status.set("Scanning files...")
        worker = threading.Thread(
            target=self._crop_images,
            args=(input_folder, output_folder, crop_pixels),
            daemon=True,
        )
        worker.start()

    def _crop_images(self, input_folder: Path, output_folder: Path, crop_pixels: int) -> None:
        image_paths: list[Path] = []
        for ext in IMAGE_EXTENSIONS:
            image_paths.extend(input_folder.rglob(ext))
            image_paths.extend(input_folder.rglob(ext.upper()))

        total = len(image_paths)
        self.after(0, lambda: self._set_progress(0, total))

        if total == 0:
            self.after(0, lambda: self.status.set("No images found (.jpg, .jpeg, .png)."))
            return

        processed = 0
        skipped = 0

        for img_path in image_paths:
            relative_path = img_path.relative_to(input_folder)
            output_path = output_folder / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    if crop_pixels >= height:
                        skipped += 1
                        continue

                    cropped = img.crop((0, 0, width, height - crop_pixels))
                    cropped.save(output_path, quality=95, subsampling=0, optimize=True)
                processed += 1
            except Exception:
                skipped += 1

            self.after(0, lambda p=processed + skipped, t=total: self._set_progress(p, t))

        self.after(
            0,
            lambda: self.status.set(
                f"Done. Cropped: {processed}, Skipped/failed: {skipped}, Output: {output_folder}"
            ),
        )

    def _set_progress(self, current: int, total: int) -> None:
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = current
        self.progress_text.set(f"{current} / {total}")


def main() -> None:
    app = CropApp()
    app.mainloop()


if __name__ == "__main__":
    main()
