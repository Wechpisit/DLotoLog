import importlib.util
import os
import tkinter as tk
from tkinter import font as tkFont


def _load_dloto_module():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "D-Loto.py")
    spec = importlib.util.spec_from_file_location("dloto_module_under_test_tooltip", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dloto = _load_dloto_module()


def test_is_text_truncated_short_text_fits():
    root = tk.Tk()
    root.withdraw()
    try:
        font = tkFont.Font(root=root, family="Tahoma", size=9)
        assert dloto.is_text_truncated("Short", font, column_width=440) is False
    finally:
        root.destroy()


def test_is_text_truncated_long_text_overflows():
    root = tk.Tk()
    root.withdraw()
    try:
        font = tkFont.Font(root=root, family="Tahoma", size=9)
        long_text = "Isolate Valve A for overhaul and maintenance work on the primary system " * 3
        assert dloto.is_text_truncated(long_text, font, column_width=440) is True
    finally:
        root.destroy()


def test_is_text_truncated_respects_padding():
    root = tk.Tk()
    root.withdraw()
    try:
        font = tkFont.Font(root=root, family="Tahoma", size=9)
        text = "Exactly medium length text"
        width = font.measure(text)
        # Text exactly filling the column, with zero padding, must not count as truncated
        assert dloto.is_text_truncated(text, font, column_width=width, padding=0) is False
        # A column narrower than the text must count as truncated
        assert dloto.is_text_truncated(text, font, column_width=width - 5, padding=0) is True
    finally:
        root.destroy()


if __name__ == "__main__":
    test_is_text_truncated_short_text_fits()
    test_is_text_truncated_long_text_overflows()
    test_is_text_truncated_respects_padding()
    print("All tests passed.")
