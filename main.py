"""
程序入口：加载 AI 配置，启动主窗口
"""
from shared import qt_compat as tk
from shared.qt_compat import simpledialog

from shared.config import load_ai_config
from features.prompt_list.widget import PromptTool


if __name__ == "__main__":
    load_ai_config()
    tk.simpledialog = simpledialog
    app = PromptTool()
    app.mainloop()
