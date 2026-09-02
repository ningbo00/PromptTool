"""
帮助文档窗口
"""
from shared import qt_compat as tk
from shared.qt_compat import ttk

from shared.ui_kit import (
    BG_BASE, BG_ELEVATED, BG_SURFACE, BG_CARD, BG_HOVER, BORDER_SUBTLE,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_PURPLE, ACCENT_YELLOW,
    ACCENT_RED, ACCENT_CYAN, ACCENT_ORANGE, FONT_FAMILY,
    apply_dark_notebook_style,
)

HELP_SECTIONS = [
    ("🚀 快速入门", """
欢迎使用 Prompt 管理工具！本工具帮助你管理、生成和优化 AI 绘画/视频提示词（Prompt）。

━━━ 5 步上手 ━━━

第 1 步：新建 Prompt
  点击左侧"+ 新建"按钮，在右侧编辑区输入你的 Prompt 内容，填写标题，然后点"保存"。

第 2 步：复制 Prompt
  在左侧列表点击任意 Prompt 条目，内容会自动显示在右侧并复制到剪贴板，可直接粘贴到 AI 工具中。

第 3 步：使用提示词生成器（推荐新手）
  点击"✨ 提示词生成器"，通过可视化界面选择摄影参数，自动生成专业英文 Prompt。
  右侧实时预览，满意后点"插入列表"或"复制"。

第 4 步：AI 优化
  选中一条 Prompt，点"🤖 AI 优化"打开优化窗口。
  需先在"⚙ AI 设置"配置你的 API Key。

第 5 步：组合使用多条 Prompt
  在列表中勾选多条 Prompt，点"☑ 拼接复制"，所有内容会合并复制到剪贴板。
"""),

    ("📋 主界面功能详解", """
━━━ 左侧 Prompt 列表 ━━━

【搜索框】输入关键词实时过滤列表，同时匹配标题和内容。

【+ 新建】创建空白 Prompt，自动进入编辑模式。
【✎ 编辑】对选中 Prompt 进行修改，编辑完成后需点"保存"。
【✕ 删除】删除选中 Prompt（弹出确认，不可撤销）。

【↑ 上移 / ↓ 下移】调整列表排列顺序。

【☑ 拼接复制】将所有勾选（打√）的 Prompt 内容合并后复制到剪贴板，多段之间用空行分隔。
【全选】一键勾选所有条目。
【清空选择】取消所有勾选。

【✨ 提示词生成器】打开专业 Prompt 构建器（详见"提示词生成器"章节）。

━━━ 右侧编辑预览区 ━━━

【标题栏】显示/编辑当前 Prompt 的标题。
【文本区】显示/编辑 Prompt 内容。

【💾 保存】将当前编辑内容保存到本地（JSON 文件，重启后保留）。
【📋 复制到剪切板】复制当前文本区内容。
【🤖 AI 优化】打开 AI 优化窗口（需配置 API Key）。
【⚙ AI 设置】配置 AI 服务参数。

━━━ 顶部工具栏 ━━━

【🗂 精简模式】收起主窗口，弹出迷你浮动列表，可拖动到屏幕任意位置。
  点击浮动窗口的"↔ 恢复"按钮返回主界面。
【📌 置顶】让主窗口始终显示在其他窗口之上。
"""),

    ("✨ 提示词生成器", """
提示词生成器通过 8 个功能标签页，帮助你搭建专业的 AI 生图 Prompt。

━━━ 标签页说明 ━━━

【🎬 预设】一键应用经典电影风格或动漫风格预设，自动填充所有参数。
  点击预设按钮后，可在其他标签页对参数进行微调。

【⚙ 基础参数】设置相机基础参数（镜头类型、光圈、快门、ISO、景深等）。
  每行包含：是否启用（复选框）+ 预设选项（下拉框）+ 自定义词（输入框）。
  输入自定义词会覆盖预设选项。

【🎥 镜头位置】可视化设置：
  - 景别滑条（超远景 ~ 超微距）
  - 俯仰角滑条（极端仰 ~ 顶视）
  - 主体方位角滑条（正面、左侧、背面等）
  - 主光源球体（鼠标拖拽设定光源方向，可选颜色）
  - 轮廓光开关

【🎨 滤镜积木】点击关键词高亮选中（紫色），再次点击取消。
  可在每组下方输入自定义词块并点"+ 添加"。

【✍ 主体场景】
  - 主体描述文本框（角色/物体描述）
  - 场景环境文本框（地点/天气/时间）
  - 快捷词块：点击自动追加到文本框末尾

【🎭 风格情绪】风格（艺术风格）、美学流派、情绪氛围的多选网格，以及动作/动态下拉。

【🔬 细节技术】质量词块、细节质感、色彩补充、渲染引擎、输出比例，以及负面提示词。

【🧪 风格提炼器】二次元动漫风格预设库，可将风格关键词"应用到风格情绪"或"追加到附加词"。

━━━ 右侧预览面板 ━━━

【附加词】可直接输入额外关键词，追加到生成结果末尾。
【正面提示词（英文）】实时预览生成的英文 Prompt。
【负面提示词（英文）】实时显示负面提示词。
【正面/负面中文对照】自动翻译显示（基于内置词库，无需 AI）。

━━━ 顶部操作按钮 ━━━

【🪄 生成】手动刷新预览（通常自动触发）。
【📋 复制】复制正面提示词到剪贴板。
【➕ 插入列表】保存为新 Prompt 并插入主列表。
【二次元模式 开/关】切换实拍/动漫两套参数体系。
"""),

    ("🤖 AI 优化窗口", """
AI 优化窗口提供 10 项功能，对你的 Prompt 进行深度加工。

━━━ 前置条件 ━━━
需要先在主窗口点"⚙ AI 设置"配置：
  - API Key（向 AI 服务提供商申请）
  - 接口地址（默认支持 OpenAI 格式，可填 DeepSeek/Qwen 等兼容地址）
  - 模型名称（如 gpt-4o、deepseek-chat 等）

━━━ 界面布局 ━━━

【左侧】原始 Prompt（可编辑）+ 自动中文翻译
【右侧】AI 优化结果 + 自动中文翻译
【顶部第一行】优化方向预设、输出长度、历史记录
【顶部第二行】自定义指令输入框
【第三行】所有功能按钮

━━━ 10 项功能说明 ━━━

1. 🚀 发送
   将左侧原始 Prompt 按选定的"优化方向"发给 AI 处理。
   先选好预设方向（如"优化英文语法"），再点发送。

2. 🔄 再优化
   把右侧 AI 结果填入左侧，再次发送给 AI 做第二轮优化。
   适合逐步提升 Prompt 质量，可以反复使用。

3. 🌐 中文→英文
   在左侧框输入中文描述（如"清晨海边的渔夫"），AI 直接生成对应的英文 Prompt。
   非常适合不熟悉英文关键词的新手。

4. 🔀 生成3变体
   AI 一次返回同一方向的 3 个不同风格版本，底部出现单选按钮供选择。

5. 🎯 AI评分
   AI 对当前 Prompt 评分（1-10分）并给出 3 条改进建议，结果显示在底部评分区。

6. 历史记录（右上角"历史 ▾"）
   自动保存最近 10 次 AI 结果，点击菜单可一键恢复任意历史版本。

7. 🏷 提取关键词
   AI 提取 10-15 个核心语义标签，以蓝色按钮显示，点击即复制该词。

8. 💡 仅扩写
   AI 不修改原有内容，只在末尾追加新的细节词补充（场景细节、光线质感等）。

9. 差异高亮（结果区右上角复选框）
   勾选后，新增词用绿色显示，被删除的词用红色删除线标注，直观对比优化前后差异。

10. 📋 复制结果
    直接复制右侧 AI 结果到剪贴板。

━━━ 输出长度控制 ━━━
顶部可选：简短（≤50词）/ 中等（50-150词）/ 详细（150词+）

━━━ 结果处理 ━━━
【✅ 应用到编辑器】将 AI 结果写回主窗口编辑区（还需点"保存"持久化）。
【💾 另存为】将 AI 结果作为新 Prompt 保存，不影响原始 Prompt。
"""),

    ("⚙ AI 设置说明", """
点击主窗口右下角"⚙ AI 设置"按钮打开配置界面。

━━━ 配置项说明 ━━━

【API Key】你的 AI 服务密钥。
  获取方式：在 AI 服务提供商的官网注册账号，在"API Key"页面创建密钥并复制。

【接口地址（Base URL）】
  OpenAI：https://api.openai.com/v1
  DeepSeek：https://api.deepseek.com/v1
  其他 OpenAI 兼容服务：请参考对应服务商文档

【模型名称】
  常用模型：
  - OpenAI: gpt-4o, gpt-4o-mini, gpt-3.5-turbo
  - DeepSeek: deepseek-chat
  - 阿里云通义: qwen-turbo, qwen-plus
  - 其他：请参考服务商文档

配置保存后会自动记住，下次打开无需重新填写。

━━━ 常见问题 ━━━

Q: AI 请求失败怎么办？
A: 检查 API Key 是否正确、网络是否可用、余额是否充足。
   状态栏会显示具体错误信息。

Q: 支持哪些 AI 服务？
A: 支持所有 OpenAI API 格式兼容的服务，包括 OpenAI、DeepSeek、阿里云通义、月之暗面等。
"""),

    ("💡 使用技巧", """
━━━ Prompt 写作技巧 ━━━

1. 基础结构
   好的 AI 图像 Prompt 通常包含：
   主体 + 动作/状态 + 场景环境 + 光线风格 + 艺术风格 + 质量词

   例：a young woman sitting by a lake, sunset, golden hour lighting,
      cinematic photography, 4K, bokeh

2. 关键词顺序
   越靠前的词权重越大，把最重要的描述放在最前面。

3. 逗号分隔
   英文 Prompt 用逗号（,）分隔各个词/短语，不需要写完整句子。

4. 质量词
   常用质量词：masterpiece, best quality, ultra-detailed, 8K, HDR

5. 负面提示词
   用于排除不想要的元素：
   常用：blurry, low quality, watermark, text, bad anatomy

━━━ 工具使用技巧 ━━━

1. 迭代优化流程（推荐）
   写基础 Prompt → AI 优化 → 查看效果 → 🔄 再优化 → 反复迭代

2. 中文用户快速入门
   用中文描述场景 → 🌐 中文→英文 → 得到英文 Prompt → 保存使用

3. 探索风格
   提示词生成器中尝试不同预设 → 复制 Prompt → 在 AI 工具中测试效果

4. 批量管理
   相关 Prompt 用统一前缀命名（如"人像-街拍-"），便于搜索过滤

5. 精简模式
   将精简模式浮窗放在屏幕一侧，左边对照 AI 生图工具，右边是 Prompt 列表。
"""),
]


class HelpDialog(tk.Toplevel):

    def __init__(self, parent):
        super().__init__(parent)
        self.title("❓ 使用帮助文档")
        self.geometry("820x640")
        self.configure(bg=BG_BASE)
        self.resizable(True, True)
        self.minsize(600, 400)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, bg=BG_ELEVATED, padx=12, pady=8,
                       highlightbackground=BORDER_SUBTLE, highlightthickness=1)
        top.pack(fill=tk.X, padx=16, pady=(12, 6))
        tk.Label(top, text="Help Library", bg=BG_ELEVATED, fg=FG_PRIMARY,
                 font=(FONT_FAMILY, 12, "bold")).pack(side=tk.LEFT)
        tk.Button(top, text="✕ 关闭", command=self.destroy,
                  bg=BG_CARD, fg=ACCENT_RED, relief=tk.FLAT,
                  font=(FONT_FAMILY, 9, "bold"), padx=10, pady=3,
                  cursor="hand2", activebackground=BG_HOVER,
                  highlightbackground=ACCENT_RED, highlightthickness=1).pack(side=tk.RIGHT)

        apply_dark_notebook_style()
        nb = ttk.Notebook(self, style="Dark.TNotebook")
        nb.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))

        for title, content in HELP_SECTIONS:
            frame = tk.Frame(nb, bg=BG_SURFACE)
            nb.add(frame, text=title)

            canvas = tk.Canvas(frame, bg=BG_SURFACE, highlightthickness=0)
            sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            inner = tk.Frame(canvas, bg=BG_SURFACE)
            win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
            inner.bind("<Configure>", lambda _e, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.bind("<Configure>", lambda e, c=canvas, wid=win_id: c.itemconfig(wid, width=e.width))
            canvas.configure(yscrollcommand=sb.set)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            def _bind_mw(c):
                def _on_enter(_e):
                    c.bind_all("<MouseWheel>", lambda e, cv=c: cv.yview_scroll(-1*(e.delta//120), "units"))
                def _on_leave(_e):
                    c.unbind_all("<MouseWheel>")
                c.bind("<Enter>", _on_enter)
                c.bind("<Leave>", _on_leave)
            _bind_mw(canvas)

            text_widget = tk.Text(
                inner, bg=BG_SURFACE, fg=FG_PRIMARY,
                relief=tk.FLAT, font=(FONT_FAMILY, 10),
                wrap=tk.WORD, padx=20, pady=16,
                state=tk.DISABLED,
                spacing1=2, spacing3=2,
            )
            text_widget.pack(fill=tk.BOTH, expand=True)
            text_widget.config(state=tk.NORMAL)

            # 配置文字样式
            text_widget.tag_config("heading", foreground=ACCENT_YELLOW,
                                   font=(FONT_FAMILY, 10, "bold"))
            text_widget.tag_config("normal", foreground=FG_PRIMARY)

            # 插入内容，对 ━━━ 行应用标题样式
            for line in content.split("\n"):
                if "━━━" in line:
                    text_widget.insert(tk.END, line + "\n", "heading")
                else:
                    text_widget.insert(tk.END, line + "\n", "normal")

            text_widget.config(state=tk.DISABLED)
