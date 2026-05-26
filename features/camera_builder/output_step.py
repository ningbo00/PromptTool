import tkinter as tk

from shared.ui_kit import BG_BASE


def create_output_step(notebook, builder):
    step = tk.Frame(notebook, bg=BG_BASE)
    notebook.add(step, text="4 输出")
    builder.tab_detail = tk.Frame(step, bg=BG_BASE)
    builder.tab_detail.pack(fill=tk.BOTH, expand=True)
    return step
