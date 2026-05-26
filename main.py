"""
程序入口：加载 AI 配置，启动主窗口
"""
import tkinter.simpledialog
import tkinter as tk

from shared.config import load_ai_config
from features.prompt_list.widget import PromptTool


if __name__ == "__main__":
    load_ai_config()
    # simpledialog 需要在 Tk 实例存在后才能使用，预先导入
    tk.simpledialog = tkinter.simpledialog
    app = PromptTool()
    app.mainloop()
