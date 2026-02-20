from __future__ import annotations

import json
import re
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from urllib.error import URLError
from urllib.request import urlopen

from PIL import Image

from app_config import load_app_config
from functions import _is_newer_version

IMAGE_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png")
DEFAULT_CONFIG = {
    "app_name": "Image Crop Tool",
    "app_version": "1.2.0",
    "update_url": "",
}
UPDATE_CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000
INITIAL_UPDATE_CHECK_DELAY_MS = 30_000


CONFIG = load_app_config("crop", DEFAULT_CONFIG)
APP_NAME = CONFIG["app_name"]
APP_VERSION = CONFIG["app_version"]
UPDATE_URL = CONFIG["update_url"]


class CropApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("760x520")
        self.resizable(False, False)
        
        # Set window icon
        icon_path = Path(__file__).with_name("ImageUtils-logo.ico")
        if icon_path.exists():
            self.iconbitmap(icon_path)

        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.crop_pixels = tk.StringVar(value="150")
        self.crop_mode = tk.StringVar(value="center")
        self.margin_top = tk.StringVar(value="0")
        self.margin_right = tk.StringVar(value="0")
        self.margin_bottom = tk.StringVar(value="175")
        self.margin_left = tk.StringVar(value="0")
        self.status = tk.StringVar(value="Select folders and click Start.")
        self.progress_text = tk.StringVar(value="0 / 0")

        self.update_banner: ttk.Frame | None = None
        self.update_download_url = ""

        self._build_ui()
        self._schedule_update_checks()

    def _build_ui(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Input folder:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.input_dir, width=62).grid(row=1, column=0, sticky="ew")
        ttk.Button(frame, text="Browse", command=self._pick_input).grid(row=1, column=1, padx=(8, 0))

        ttk.Label(frame, text="Output folder:").grid(row=2, column=0, sticky="w", pady=(14, 6))
        ttk.Entry(frame, textvariable=self.output_dir, width=62).grid(row=3, column=0, sticky="ew")
        ttk.Button(frame, text="Browse", command=self._pick_output).grid(row=3, column=1, padx=(8, 0))

        mode_frame = ttk.LabelFrame(frame, text="Crop mode", padding=10)
        mode_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        ttk.Radiobutton(
            mode_frame,
            text="Crop from center (keep center content)",
            value="center",
            variable=self.crop_mode,
        ).grid(row=0, column=0, sticky="w")
        
        # Thin separator line
        separator = ttk.Separator(mode_frame, orient="horizontal")
        separator.grid(row=1, column=0, sticky="w", pady=(8, 8), padx=(0, 0))
        # Set width to match text width approximately
        separator.configure(style="Thin.TSeparator")
        
        ttk.Radiobutton(
            mode_frame,
            text="Crop by margins (top/right/bottom/left)",
            value="margins",
            variable=self.crop_mode,
        ).grid(row=2, column=0, sticky="w")

        pixel_frame = ttk.Frame(mode_frame)
        pixel_frame.grid(row=0, column=1, padx=(22, 0), sticky="nw")
        ttk.Label(pixel_frame, text="Pixels from center:").grid(row=0, column=0, sticky="w")
        ttk.Entry(pixel_frame, textvariable=self.crop_pixels, width=8).grid(row=0, column=1, padx=(8, 0))
        ttk.Label(
            pixel_frame,
            text="Distance from center in all 4 directions",
            foreground="#666666",
            font=("Segoe UI", 8)
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 0))

        margin_frame = ttk.Frame(mode_frame)
        margin_frame.grid(row=2, column=1, padx=(22, 0), sticky="nw")
        ttk.Label(margin_frame, text="Top").grid(row=0, column=0)
        ttk.Entry(margin_frame, textvariable=self.margin_top, width=6).grid(row=1, column=0, padx=(0, 4))
        ttk.Label(margin_frame, text="Right").grid(row=0, column=1)
        ttk.Entry(margin_frame, textvariable=self.margin_right, width=6).grid(row=1, column=1, padx=4)
        ttk.Label(margin_frame, text="Bottom").grid(row=0, column=2)
        ttk.Entry(margin_frame, textvariable=self.margin_bottom, width=6).grid(row=1, column=2, padx=4)
        ttk.Label(margin_frame, text="Left").grid(row=0, column=3)
        ttk.Entry(margin_frame, textvariable=self.margin_left, width=6).grid(row=1, column=3, padx=(4, 0))

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
        
        # Footer with version information
        footer = ttk.Frame(self)
        footer.pack(side="bottom", fill="x")
        footer_label = ttk.Label(
            footer, 
            text=f"v{APP_VERSION}", 
            foreground="#888888",
            font=("Segoe UI", 8)
        )
        footer_label.pack(side="right", padx=8, pady=4)

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
        crop_mode = self.crop_mode.get()
        crop_pixels = 0
        margins = (0, 0, 0, 0)

        if crop_mode == "center":
            try:
                crop_pixels = int(self.crop_pixels.get().strip())
            except ValueError:
                messagebox.showerror("Invalid input", "Pixels must be a whole number.")
                return

            if crop_pixels < 1:
                messagebox.showerror("Invalid input", "Pixels must be greater than 0.")
                return

        if crop_mode == "margins":
            try:
                margins = (
                    int(self.margin_top.get().strip()),
                    int(self.margin_right.get().strip()),
                    int(self.margin_bottom.get().strip()),
                    int(self.margin_left.get().strip()),
                )
            except ValueError:
                messagebox.showerror("Invalid input", "All margin values must be whole numbers.")
                return

            if any(value < 0 for value in margins):
                messagebox.showerror("Invalid input", "Margin values must be 0 or greater.")
                return

        input_folder = Path(self.input_dir.get().strip())
        output_folder = Path(self.output_dir.get().strip())

        if not input_folder.exists() or not input_folder.is_dir():
            messagebox.showerror("Invalid folder", "Please choose a valid input folder.")
            return

        if not output_folder:
            messagebox.showerror("Invalid folder", "Please choose an output folder.")
            return

        self.status.set("Cropping files...")
        worker = threading.Thread(
            target=self._crop_images,
            args=(input_folder, output_folder, crop_mode, crop_pixels, margins),
            daemon=True,
        )
        worker.start()

    def _crop_images(
        self,
        input_folder: Path,
        output_folder: Path,
        crop_mode: str,
        crop_pixels: int,
        margins: tuple[int, int, int, int],
    ) -> None:
        image_paths: list[Path] = []
        for ext in IMAGE_EXTENSIONS:
            image_paths.extend(input_folder.rglob(ext))
            image_paths.extend(input_folder.rglob(ext.upper()))
        
        # Remove duplicates (Windows is case-insensitive, so *.jpg and *.JPG match the same files)
        image_paths = list(dict.fromkeys(image_paths))

        total = len(image_paths)
        self.after(0, lambda: self._set_progress(0, total))

        if total == 0:
            self.after(0, lambda: self.status.set("No images found (.jpg, .jpeg, .png)."))
            return

        processed = 0
        skipped = 0
        errors: list[tuple[str, str]] = []  # (filename, error_message)
        max_errors_to_track = 10

        for img_path in image_paths:
            relative_path = img_path.relative_to(input_folder)
            output_path = output_folder / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    crop_box = self._build_crop_box(width, height, crop_mode, crop_pixels, margins)
                    if crop_box is None:
                        skipped += 1
                        if len(errors) < max_errors_to_track:
                            errors.append((img_path.name, "Image too small for crop settings"))
                        continue

                    cropped = img.crop(crop_box)
                    self._save_cropped_image(cropped, img, output_path)

                    # Debug option (keep commented unless needed):
                    # from PIL import ImageChops
                    # original_crop_part = img.crop(crop_box)
                    # diff = ImageChops.difference(original_crop_part, cropped)
                    # print(diff.getbbox())
                processed += 1
            except Exception as e:
                skipped += 1
                if len(errors) < max_errors_to_track:
                    error_msg = f"{type(e).__name__}: {str(e)}" if str(e) else type(e).__name__
                    errors.append((img_path.name, error_msg))

            self.after(0, lambda p=processed + skipped, t=total: self._set_progress(p, t))

        status_msg = f"Done. Cropped: {processed}, Skipped/failed: {skipped}, Output: {output_folder}"
        self.after(0, lambda: self.status.set(status_msg))
        
        if errors:
            self.after(0, lambda: self._show_error_report(errors, skipped))

    def _build_crop_box(
        self,
        width: int,
        height: int,
        crop_mode: str,
        crop_pixels: int,
        margins: tuple[int, int, int, int],
    ) -> tuple[int, int, int, int] | None:
        if crop_mode == "center":
            center_x = width // 2
            center_y = height // 2
            left = center_x - crop_pixels
            top = center_y - crop_pixels
            right = center_x + crop_pixels
            bottom = center_y + crop_pixels

            if left < 0 or top < 0 or right > width or bottom > height:
                return None
            return (left, top, right, bottom)

        if crop_mode == "margins":
            top_margin, right_margin, bottom_margin, left_margin = margins
            left = left_margin
            top = top_margin
            right = width - right_margin
            bottom = height - bottom_margin
            if left >= right or top >= bottom:
                return None
            return (left, top, right, bottom)

        return None

    def _show_error_report(self, errors: list[tuple[str, str]], total_failed: int) -> None:
        """Display a dialog showing error details for failed images."""
        error_lines = []
        for filename, error_msg in errors:
            error_lines.append(f"• {filename}\n  {error_msg}")
        
        error_text = "\n\n".join(error_lines)
        
        if total_failed > len(errors):
            remaining = total_failed - len(errors)
            error_text += f"\n\n... and {remaining} more error(s)"
        
        messagebox.showwarning(
            "Processing Errors",
            f"{total_failed} image(s) failed to process:\n\n{error_text}",
        )

    def _save_cropped_image(self, cropped: Image.Image, original: Image.Image, output_path: Path) -> None:
        image_format = (original.format or "").upper()
        save_kwargs: dict[str, str] = {}
        if image_format:
            save_kwargs["format"] = image_format

        if image_format in {"JPEG", "JPG"}:
            save_kwargs.update({"quality": "keep", "subsampling": "keep"})

        try:
            cropped.save(output_path, **save_kwargs)
        except (OSError, ValueError):
            # Fallback if 'keep' is not supported or other save errors occur
            if image_format in {"JPEG", "JPG"}:
                fallback_kwargs = {"quality": 95, "subsampling": 0, "optimize": True}
                if image_format:
                    fallback_kwargs["format"] = image_format
                cropped.save(output_path, **fallback_kwargs)  # type: ignore[arg-type]
                return
            raise

    def _set_progress(self, current: int, total: int) -> None:
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = current
        self.progress_text.set(f"{current} / {total}")

    def _schedule_update_checks(self) -> None:
        self.after(INITIAL_UPDATE_CHECK_DELAY_MS, self._start_update_check)

    def _start_update_check(self) -> None:
        worker = threading.Thread(target=self._check_for_updates, daemon=True)
        worker.start()

    def _check_for_updates(self) -> None:
        try:
            if not UPDATE_URL:
                return

            with urlopen(UPDATE_URL, timeout=5) as response:
                payload = json.loads(response.read().decode("utf-8"))

            remote_version = str(payload.get("version", "")).strip()
            download_url = str(payload.get("url") or payload.get("html_url") or "").strip()
            notes = str(payload.get("notes", "")).strip()

            if remote_version and download_url and _is_newer_version(remote_version, APP_VERSION):
                self.after(
                    0,
                    lambda: self._show_update_banner(
                        remote_version=remote_version,
                        download_url=download_url,
                        notes=notes,
                    ),
                )
        except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError):
            pass
        finally:
            self.after(UPDATE_CHECK_INTERVAL_MS, self._start_update_check)

    def _show_update_banner(self, remote_version: str, download_url: str, notes: str) -> None:
        if self.update_banner is not None:
            return

        self.update_download_url = download_url
        notes_preview = notes[:80] + ("..." if len(notes) > 80 else "")
        banner_text = f"Update available: v{remote_version}"
        if notes_preview:
            banner_text += f" • {notes_preview}"

        self.update_banner = ttk.Frame(self, padding=(10, 8))
        self.update_banner.place(relx=1.0, x=-12, y=12, anchor="ne")

        ttk.Label(self.update_banner, text=banner_text, wraplength=300).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 8)
        )
        ttk.Button(self.update_banner, text="Download", command=self._open_download_url).grid(
            row=1, column=0, sticky="w"
        )
        ttk.Button(self.update_banner, text="Dismiss", command=self._dismiss_update_banner).grid(
            row=1, column=1, padx=(8, 0), sticky="e"
        )

    def _dismiss_update_banner(self) -> None:
        if self.update_banner is not None:
            self.update_banner.destroy()
            self.update_banner = None

    def _open_download_url(self) -> None:
        if self.update_download_url:
            webbrowser.open(self.update_download_url)


def main() -> None:
    app = CropApp()
    app.mainloop()


if __name__ == "__main__":
    main()
