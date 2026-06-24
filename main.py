"""PDF Compressor — CLI and GUI entry point."""

from __future__ import annotations

import argparse
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from compressor import PROFILES, compress_pdf, default_output_path, format_size


def run_cli() -> int:
    parser = argparse.ArgumentParser(
        description="Сжатие PDF-файлов с уменьшением размера изображений.",
    )
    parser.add_argument("input", type=Path, help="Путь к исходному PDF")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Путь для сохранения (по умолчанию: имя_compressed.pdf)",
    )
    parser.add_argument(
        "-l",
        "--level",
        choices=PROFILES.keys(),
        default="medium",
        help="Уровень сжатия: low, medium, high (по умолчанию: medium)",
    )

    args = parser.parse_args()
    output = args.output or default_output_path(args.input)
    profile = PROFILES[args.level]

    try:
        original, compressed = compress_pdf(args.input, output, profile)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    saved = original - compressed
    ratio = (saved / original * 100) if original else 0

    print(f"Профиль: {profile.name}")
    print(f"Исходный размер:   {format_size(original)}")
    print(f"Новый размер:      {format_size(compressed)}")
    print(f"Сэкономлено:       {format_size(saved)} ({ratio:.1f}%)")
    print(f"Сохранено в:       {output}")
    return 0


class PdfCompressorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("PDF Compressor")
        self.root.geometry("520x320")
        self.root.resizable(False, False)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.level = tk.StringVar(value="medium")
        self.status = tk.StringVar(value="Выберите PDF-файл для сжатия")

        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="PDF Compressor", font=("Segoe UI", 14, "bold")).pack(
            anchor="w",
            pady=(0, 8),
        )

        ttk.Label(frame, text="Исходный файл:").pack(anchor="w")
        input_row = ttk.Frame(frame)
        input_row.pack(fill="x", **padding)
        ttk.Entry(input_row, textvariable=self.input_path).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6),
        )
        ttk.Button(input_row, text="Обзор...", command=self._pick_input).pack(side="right")

        ttk.Label(frame, text="Куда сохранить:").pack(anchor="w")
        output_row = ttk.Frame(frame)
        output_row.pack(fill="x", **padding)
        ttk.Entry(output_row, textvariable=self.output_path).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 6),
        )
        ttk.Button(output_row, text="Обзор...", command=self._pick_output).pack(side="right")

        ttk.Label(frame, text="Уровень сжатия:").pack(anchor="w")
        level_frame = ttk.Frame(frame)
        level_frame.pack(anchor="w", **padding)
        for key, profile in PROFILES.items():
            ttk.Radiobutton(
                level_frame,
                text=profile.name,
                value=key,
                variable=self.level,
            ).pack(anchor="w")

        ttk.Button(
            frame,
            text="Сжать PDF",
            command=self._compress,
        ).pack(pady=(12, 8))

        ttk.Label(frame, textvariable=self.status, wraplength=480).pack(anchor="w")

    def _pick_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if path:
            self.input_path.set(path)
            if not self.output_path.get():
                self.output_path.set(str(default_output_path(Path(path))))

    def _pick_output(self) -> None:
        initial = self.input_path.get()
        initial_dir = str(Path(initial).parent) if initial else None
        path = filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".pdf",
            initialdir=initial_dir,
            filetypes=[("PDF files", "*.pdf")],
        )
        if path:
            self.output_path.set(path)

    def _compress(self) -> None:
        input_text = self.input_path.get().strip()
        output_text = self.output_path.get().strip()

        if not input_text:
            messagebox.showwarning("PDF Compressor", "Выберите исходный PDF-файл.")
            return

        input_path = Path(input_text)
        output_path = Path(output_text) if output_text else default_output_path(input_path)
        profile = PROFILES[self.level.get()]

        self.status.set("Сжатие...")
        self.root.update_idletasks()

        try:
            original, compressed = compress_pdf(input_path, output_path, profile)
        except (FileNotFoundError, ValueError, OSError) as exc:
            messagebox.showerror("Ошибка", str(exc))
            self.status.set("Ошибка при сжатии.")
            return

        saved = original - compressed
        ratio = (saved / original * 100) if original else 0

        if compressed >= original:
            message = (
                f"Файл уже достаточно оптимизирован.\n\n"
                f"Исходный: {format_size(original)}\n"
                f"Результат: {format_size(compressed)}\n\n"
                f"Сохранено в:\n{output_path}"
            )
        else:
            message = (
                f"Сжатие завершено!\n\n"
                f"Исходный: {format_size(original)}\n"
                f"Результат: {format_size(compressed)}\n"
                f"Сэкономлено: {format_size(saved)} ({ratio:.1f}%)\n\n"
                f"Сохранено в:\n{output_path}"
            )

        messagebox.showinfo("Готово", message)
        self.status.set(
            f"Готово: {format_size(original)} → {format_size(compressed)} "
            f"({ratio:.1f}% экономии)"
        )


def run_gui() -> int:
    root = tk.Tk()
    PdfCompressorApp(root)
    root.mainloop()
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        return run_cli()
    return run_gui()


if __name__ == "__main__":
    raise SystemExit(main())
