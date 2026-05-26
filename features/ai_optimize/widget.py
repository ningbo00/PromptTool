"""
AI 优化 Prompt 弹出窗口（10 项增强功能版 v2 — 逻辑修复）
"""
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.simpledialog
import pyperclip

from shared.ui_kit import (
    BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER,
    FG_PRIMARY, FG_MUTED, FG_DIM,
    ACCENT_BLUE, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_RED,
    ACCENT_PURPLE, ACCENT_CYAN, ACCENT_ORANGE, DARK_TEXT, Tooltip,
)
from shared.config import get_ai_config
from core.services.ai_optimize_service import (
    AIOptimizeService,
    AIOptimizeValidationError,
)
from features.ai_optimize.client import call_ai
from features.ai_optimize.panels import (
    ActionBar,
    InsightsPanel,
    InstructionPanel,
    ResultPanel,
)


class AIOptimizeDialog(tk.Toplevel):

    PRESETS = [
        "优化英文语法和流畅度，保持原意",
        "扩充细节，让画面描述更具体生动",
        "压缩精简，去除冗余保留核心词",
        "转换为更专业的摄影/绘画术语",
        "调整为可灵（Kling）视频生成最佳格式：简洁动作描述+镜头运动+画面风格",
        "调整为即梦（Jimeng）最佳格式：分镜描述+情绪氛围+画面细节",
        "调整为 Seedance 最佳格式：主体动作+场景环境+运镜方式+光影",
        "调整为豆包（Doubao）图像生成最佳格式：主体描述+风格标签+质量词",
        "调整为海螺（Hailuo MiniMax）视频最佳格式：镜头语言+时序动作+氛围",
        "调整为万象（Wan）视频最佳格式：场景+人物动作+摄影机运动+光线",
        "调整为 Midjourney 最佳格式：风格词+参数+画质标签",
        "调整为 Stable Diffusion 最佳格式：正向提示词+括号权重",
        "调整为 Sora 最佳格式：长镜头叙事+摄影机动作+场景细节",
        "调整为 Runway Gen-4 最佳格式：主体+动作+镜头+氛围",
        "自定义指令（在下方输入）",
    ]

    _LENGTH_HINTS = {
        "简短": "输出长度控制在 50 词以内，保留最核心关键词。",
        "中等": "输出长度在 50-150 词之间，内容详略适中。",
        "详细": "输出长度在 150 词以上，尽量丰富细节描写。",
    }

    def __init__(self, parent, current_prompt: str, on_apply=None, on_saveas=None):
        super().__init__(parent)
        self.title("🤖 AI 协助优化 Prompt")
        self.geometry("960x700")
        self.configure(bg=BG_BASE)
        self.grab_set()
        self.resizable(True, True)
        self.minsize(720, 520)

        self._current    = current_prompt
        self._on_apply   = on_apply
        self._on_saveas  = on_saveas

        # 状态
        self._length_var   = tk.StringVar(value="中等")
        self._diff_var     = tk.BooleanVar(value=False)
        self._variant_var  = tk.StringVar(value="")
        self._variants     = []          # list[str] — 当前变体列表
        self._history      = []          # list[(direction, raw_result)]
        self._raw_result   = ""          # 当前结果的干净文本（无差异标注）
        self._busy         = False
        self._ai_service   = AIOptimizeService(custom_direction_label=self.PRESETS[-1])

        # 控件引用（在 _build_ui 中赋值）
        self._orig_text       = None
        self._orig_zh_text    = None
        self._result_text     = None
        self._result_zh_text  = None
        self._status_lbl      = None
        self._apply_btn       = None
        self._saveas_btn      = None
        self._iterate_btn     = None
        self._improve_btn     = None
        self._action_btns     = []       # 所有需随 busy 一起禁用的按钮
        self._history_menu    = None
        self._kw_frame        = None
        self._score_frame     = None
        self._neg_rec_frame   = None
        self._compliance_frame = None
        self._score_text      = None
        self._variant_frame   = None
        self._preset_var      = None
        self._custom_var      = None

        self._build_ui()
        self._auto_translate_original()

    # ─────────────────────────────────────────────────────────────
    #  UI 骨架
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        instruction = InstructionPanel(self, self.PRESETS, self._length_var)
        self._preset_var = instruction.preset_var
        self._custom_var = instruction.custom_var
        self._hist_mb = instruction.history_button
        self._history_menu = instruction.history_menu

        action_bar = ActionBar(self)
        primary_row = action_bar.add_group("主要流程")
        advanced_row = action_bar.add_group("高级工具")
        result_row = action_bar.add_group("结果操作")

        def _abtn(text, cmd, color, state=tk.NORMAL, tip="", parent=primary_row):
            """action button — 统一加入 _action_btns 受 busy 控制"""
            b = action_bar.action_button(parent, text, cmd, color, state=state, tip=tip)
            self._action_btns.append(b)
            return b

        def _sbtn(text, cmd, color, state=tk.NORMAL, tip="", parent=result_row):
            """secondary button — 不加入 action_btns"""
            return action_bar.action_button(parent, text, cmd, color, state=state, tip=tip)

        _abtn("🚀 发送",        self._run_ai,          ACCENT_BLUE,
              tip="🚀 发送\n按照所选[优化方向]，将原始 Prompt 发送给 AI 进行优化。\n首先在上方选择预设方向（如[优化英文语法]），然后点击此按钮。")
        self._iterate_btn = _abtn("🔄 再优化",  self._iterate,         ACCENT_CYAN,   tk.DISABLED,
              tip="🔄 再优化\n将右侧 AI 优化结果自动填入左侧原始框，然后再次发送给 AI 进行第二轮优化。\n可以反复使用，逐步提升 Prompt 质量。")
        _abtn("🌐 中文→英",    self._zh_to_en,         ACCENT_PURPLE,
              tip="🌐 中文→英\n在左侧框输入中文场景描述（如[夕阳下的少女]），AI 会将其转化为适合图像生成的英文 Prompt（逗号分隔关键词格式）。")
        _abtn("🔀 生成3变体",  self._gen_variants,     ACCENT_ORANGE,
              tip="🔀 生成3变体\n让 AI 一次生成同一方向的 3 个不同风格版本，下方会出现单选按钮供选择，选中后才能应用。")
        _abtn("🎯 AI评分",     self._score,            ACCENT_YELLOW, parent=advanced_row,
              tip="🎯 AI评分\n让 AI 对当前原始 Prompt 进行质量评分（1-10分），给出 3 条具体改进建议，并自动检测词汇矛盾。评分结果显示在底部评分区。")
        _abtn("🏷 提取关键词", self._extract_keywords, "#74c7ec", parent=advanced_row,
              tip="🏷 提取关键词\n从原始 Prompt 中提取 10-15 个最核心的语义关键词，以蓝色标签显示在底部。点击任意标签可将该词复制到剪贴板。")
        _abtn("💡 仅扩写",     self._expand_only,      "#a6e3a1", parent=advanced_row,
              tip="💡 仅扩写\nAI 不修改原有内容，只在末尾追加新的细节词（场景细节、光线质感、情绪氛围等）。\n输出格式：原文, [新增：追加词]")

        advanced_row2 = tk.Frame(advanced_row, bg=BG_SURFACE)
        advanced_row2.pack(fill=tk.X, pady=(4, 0))
        _abtn("🧙 引导创作",   self._guided_create,    ACCENT_PURPLE, parent=advanced_row2,
              tip="🧙 引导创作\n如果你不知道怎么写 Prompt，AI 会一步步提问你主体、场景、氛围、风格和特殊要求，最后自动生成完整 Prompt。")
        _abtn("🚫 推荐负面词", self._recommend_negative, ACCENT_RED, parent=advanced_row2,
              tip="🚫 推荐负面词\n根据当前 Prompt，AI 自动推荐适合排除的负面词，按分组显示在底部，点击即可复制。")
        _abtn("📖 描述转Prompt", self._desc_to_prompt, ACCENT_ORANGE, parent=advanced_row2,
              tip="📖 描述转Prompt\n把一段自然语言描述、小说片段或中文场景说明，提炼成适合生图/生视频的英文 Prompt。")
        _abtn("🛡 合规检验",   self._compliance_check, "#94e2d5", parent=advanced_row2,
              tip="🛡 合规检验\n检测 Prompt 中可能导致 AI 视频/图像平台拒绝生成的违规词或敏感内容，结果显示在底部，标出违规词并给出修改建议。")

        self._apply_btn  = _sbtn("✅ 应用到编辑器", self._apply,   ACCENT_GREEN, tk.DISABLED,
              tip="✅ 应用到编辑器\n将右侧 AI 优化结果替换到主窗口的编辑区（需要再点[保存]才能持久化）。")
        self._saveas_btn = _sbtn("💾 另存为",       self._saveas,  "#f9e2af",    tk.DISABLED,
              tip="💾 另存为\n将 AI 优化结果作为新的 Prompt 保存到列表（会弹出对话框要求输入标题），不影响原始 Prompt。")
        _sbtn("✕ 关闭", self.destroy, ACCENT_RED,
              tip="✕ 关闭\n关闭 AI 优化窗口，回到主界面。")

        # ── 变体选择区（动态插入，先占位） ────────────────────────
        # 注意：必须作为 bottom_area 的子控件，否则 paned(expand) 会占满空间
        # 此处先创建占位，等 bottom_area 创建后再重建

        # ── 底部固定区（状态栏 + 变体选择 + 关键词 + 评分 + 负面推荐，必须在 paned 前 pack） ──
        bottom_area = InsightsPanel(self).frame

        # ── 变体选择区（放在 bottom_area 最顶部，紧贴结果区下方） ──
        self._variant_frame = tk.Frame(bottom_area, bg=BG_BASE)
        # 不 pack，按需 pack/pack_forget

        # ── 状态栏 ──────────────────────────────────────────────────
        self._status_lbl = tk.Label(bottom_area, text="", bg=BG_BASE, fg=ACCENT_YELLOW,
                                    font=("微软雅黑", 9))
        self._status_lbl.pack(anchor="w", padx=12, pady=(2, 2))

        # ── 关键词 chip 区（动态显示） ─────────────────────────────
        self._kw_frame = tk.Frame(bottom_area, bg=BG_BASE)

        # ── 负面词推荐区（动态显示） ───────────────────────────────
        self._neg_rec_frame = tk.Frame(bottom_area, bg=BG_BASE)

        # ── 合规检验区（动态显示） ─────────────────────────────────
        self._compliance_frame = tk.Frame(bottom_area, bg=BG_BASE)

        # ── 评分区（动态显示） ─────────────────────────────────────
        self._score_frame = tk.Frame(bottom_area, bg=BG_BASE)
        score_hdr = tk.Frame(self._score_frame, bg=BG_BASE)
        score_hdr.pack(fill=tk.X, padx=6)
        tk.Label(score_hdr, text="🎯 AI 评分与建议", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        self._improve_btn = tk.Button(
            score_hdr, text="⚡ 按建议优化", command=self._improve_by_score,
            bg=ACCENT_ORANGE, fg=DARK_TEXT, relief=tk.FLAT,
            font=("微软雅黑", 8, "bold"), padx=8, pady=1,
            cursor="hand2", activebackground=ACCENT_ORANGE, state=tk.DISABLED,
        )
        self._improve_btn.pack(side=tk.RIGHT, padx=(0, 6))
        Tooltip(self._improve_btn, "⚡ 按建议优化\n让 AI 参考上方的评分建议，对原始 Prompt 进行针对性优化，结果输出到右侧结果区。")
        tk.Button(score_hdr, text="✕", command=self._score_frame.pack_forget,
                  bg=BG_HOVER, fg=FG_MUTED, relief=tk.FLAT,
                  font=("微软雅黑", 8), padx=4, pady=0,
                  cursor="hand2", activebackground=BG_HOVER).pack(side=tk.RIGHT)
        self._score_text = tk.Text(self._score_frame, bg=BG_SURFACE, fg=ACCENT_YELLOW,
                                   relief=tk.FLAT, font=("微软雅黑", 9),
                                   wrap=tk.WORD, padx=8, pady=6, height=12,
                                   state=tk.DISABLED)
        self._score_text.pack(fill=tk.X, padx=6, pady=(2, 6))

        body_header = tk.Frame(self, bg=BG_BASE)
        body_header.pack(fill=tk.X, padx=12, pady=(0, 4))
        tk.Label(body_header, text="输入", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 8, "bold")).pack(side=tk.LEFT)
        tk.Label(body_header, text="结果", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 8, "bold")).pack(side=tk.RIGHT)

        # ── 主分割 ──────────────────────────────────────────────────
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 2))
        self._orig_text, self._orig_zh_text = self._make_left_pane(paned)
        self._result_text, self._result_zh_text = self._make_right_pane(paned)

        # 填入原始内容
        self._orig_text.insert("1.0", self._current)

    def _make_left_pane(self, paned):
        frame = tk.Frame(paned, bg=BG_BASE)
        paned.add(frame, weight=1)
        vpaned = ttk.PanedWindow(frame, orient=tk.VERTICAL)
        vpaned.pack(fill=tk.BOTH, expand=True)

        en_f = tk.Frame(vpaned, bg=BG_BASE)
        vpaned.add(en_f, weight=2)
        tk.Label(en_f, text="原始 Prompt（可编辑）", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9)).pack(anchor="w")
        en_text = tk.Text(en_f, bg=BG_SURFACE, fg=FG_MUTED, relief=tk.FLAT,
                          font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6)
        en_text.pack(fill=tk.BOTH, expand=True)

        zh_f = tk.Frame(vpaned, bg=BG_BASE)
        vpaned.add(zh_f, weight=1)
        tk.Label(zh_f, text="🀄 原始中文翻译（AI 自动）", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=("微软雅黑", 9)).pack(anchor="w")
        zh_text = tk.Text(zh_f, bg=BG_BASE, fg=ACCENT_YELLOW, relief=tk.FLAT,
                          font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=4,
                          state=tk.DISABLED)
        zh_text.pack(fill=tk.BOTH, expand=True)
        return en_text, zh_text

    def _make_right_pane(self, paned):
        frame = tk.Frame(paned, bg=BG_BASE)
        paned.add(frame, weight=1)
        vpaned = ttk.PanedWindow(frame, orient=tk.VERTICAL)
        vpaned.pack(fill=tk.BOTH, expand=True)

        en_f = tk.Frame(vpaned, bg=BG_BASE)
        vpaned.add(en_f, weight=2)

        ResultPanel.build_header(
            en_f,
            self._diff_var,
            self._toggle_diff,
            self._copy_result,
        )

        en_text = tk.Text(en_f, bg=BG_SURFACE, fg=ACCENT_GREEN, relief=tk.FLAT,
                          font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                          state=tk.DISABLED)
        en_text.pack(fill=tk.BOTH, expand=True)
        en_text.tag_config("added",   foreground="#a6e3a1")   # 亮绿（新增）
        en_text.tag_config("removed", foreground=ACCENT_RED,
                           font=("微软雅黑", 9, "overstrike"))  # 红色删除线
        en_text.tag_config("normal",  foreground=ACCENT_GREEN)

        zh_f = tk.Frame(vpaned, bg=BG_BASE)
        vpaned.add(zh_f, weight=1)
        tk.Label(zh_f, text="🀄 优化结果中文翻译（AI 自动）", bg=BG_BASE, fg=ACCENT_YELLOW,
                 font=("微软雅黑", 9)).pack(anchor="w")
        zh_text = tk.Text(zh_f, bg=BG_BASE, fg=ACCENT_YELLOW, relief=tk.FLAT,
                          font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=4,
                          state=tk.DISABLED)
        zh_text.pack(fill=tk.BOTH, expand=True)
        return en_text, zh_text

    # ─────────────────────────────────────────────────────────────
    #  内部工具
    # ─────────────────────────────────────────────────────────────
    def _get_orig(self) -> str:
        return self._orig_text.get("1.0", tk.END).strip()

    def _set_result(self, text: str):
        """写入结果文本框，同时更新 _raw_result。"""
        self._raw_result = text
        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)
        self._result_text.insert("1.0", text)
        self._result_text.config(state=tk.DISABLED)

    def _set_status(self, msg: str, delay_clear: int = 0):
        self._status_lbl.config(text=msg)
        if delay_clear:
            self.after(delay_clear, lambda: self._status_lbl.config(text=""))

    def _set_busy(self, busy: bool):
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        for b in self._action_btns:
            b.config(state=state)
        # 再优化单独管理（只在有结果时启用）
        if not busy and self._raw_result and not self._raw_result.startswith("（"):
            self._iterate_btn.config(state=tk.NORMAL)
        elif busy:
            self._iterate_btn.config(state=tk.DISABLED)

    def _enable_apply(self):
        self._apply_btn.config(state=tk.NORMAL)
        self._saveas_btn.config(state=tk.NORMAL)
        self._iterate_btn.config(state=tk.NORMAL)

    def _translate(self, source: str, target_widget: tk.Text, on_done=None):
        if not source:
            return
        ai_url, ai_key, ai_model = get_ai_config()
        messages = [
            {"role": "system", "content":
                "你是专业翻译。将英文 Prompt 翻译为通顺的中文，逐词/逐短语对应，"
                "保留括号内容，输出仅翻译文本，无需任何解释。"},
            {"role": "user", "content": source},
        ]

        def _on_ok(zh):
            def _show():
                target_widget.config(state=tk.NORMAL)
                target_widget.delete("1.0", tk.END)
                target_widget.insert("1.0", zh)
                target_widget.config(state=tk.DISABLED)
                if on_done:
                    on_done()
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, messages, temperature=0.3,
                on_success=_on_ok, on_error=lambda _: None)

    def _auto_translate_original(self):
        if not self._current:
            return
        self._orig_zh_text.config(state=tk.NORMAL)
        self._orig_zh_text.insert("1.0", "（翻译中…）")
        self._orig_zh_text.config(state=tk.DISABLED)
        self._translate(self._current, self._orig_zh_text)

    def _show_result_zh(self, text: str, final_status: str = ""):
        """触发结果中文翻译，翻译完更新状态栏。"""
        self._result_zh_text.config(state=tk.NORMAL)
        self._result_zh_text.delete("1.0", tk.END)
        self._result_zh_text.insert("1.0", "（翻译中…）")
        self._result_zh_text.config(state=tk.DISABLED)
        self._translate(text, self._result_zh_text,
                        on_done=lambda: self._set_status(final_status) if final_status else None)

    def _clean_result_text(self) -> str:
        """返回不含差异标注的干净结果。"""
        return self._raw_result

    # ─────────────���───────────────────────────────────────────────
    #  主 AI 优化
    # ─────────────────────────────────────────────────────────────
    def _run_ai(self):
        try:
            request = self._ai_service.prepare_action(
                "optimize_current",
                original=self._get_orig(),
                direction=self._preset_var.get(),
                custom_direction=self._custom_var.get(),
                length=self._length_var.get(),
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return

        self._set_status("⏳ 正在请求 AI，请稍候…")
        self._set_busy(True)
        self._set_result("（等待回复…）")
        self._result_zh_text.config(state=tk.NORMAL)
        self._result_zh_text.delete("1.0", tk.END)
        self._result_zh_text.config(state=tk.DISABLED)
        self._clear_variant_ui()

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._set_result(text)
                self._enable_apply()
                self._push_history(request.history_label, text)
                self._set_busy(False)
                self._show_result_zh(text, "✓ AI 优化完成")
                if self._diff_var.get():
                    self._apply_diff_highlight()
                self._set_status("✓ AI 优化完成，中文翻译中…")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._set_result(f"[请求失败]\n{msg}")
                self._set_status("✗ 请求失败，请检查 API Key 和网络")
                self._set_busy(False)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages,
                temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    # ─────────────────────────────────────────────────────────────
    #  功能 1：继续优化（迭代）
    # ─────────────────────────────────────────────────────────────
    def _iterate(self):
        result = self._clean_result_text()
        if not result or result.startswith("（") or result.startswith("[请求失败]"):
            messagebox.showinfo("提示", "还没有可用的优化结果", parent=self)
            return
        self._orig_text.delete("1.0", tk.END)
        self._orig_text.insert("1.0", result)
        # 同步更新原始中文翻译
        self._orig_zh_text.config(state=tk.NORMAL)
        self._orig_zh_text.delete("1.0", tk.END)
        self._orig_zh_text.insert("1.0", "（翻译中…）")
        self._orig_zh_text.config(state=tk.DISABLED)
        self._translate(result, self._orig_zh_text)
        self._set_status("🔄 已将结果填入原始框，发送中…")
        self._run_ai()

    # ─────────────────────────────────────────────────────────────
    #  功能 2：AI 评分
    # ─────────────────────────────────────────────────────────────
    def _score(self):
        try:
            request = self._ai_service.prepare_action("score", original=self._get_orig())
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return
        self._set_status("⏳ AI 评分中…")
        self._score_frame.pack(fill=tk.X, padx=12, pady=(2, 4))
        self._score_text.config(state=tk.NORMAL)
        self._score_text.delete("1.0", tk.END)
        self._score_text.insert("1.0", "（评分中…）")
        self._score_text.config(state=tk.DISABLED)

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._score_text.config(state=tk.NORMAL)
                self._score_text.delete("1.0", tk.END)
                self._score_text.insert("1.0", text)
                self._score_text.config(state=tk.DISABLED)
                self._improve_btn.config(state=tk.NORMAL)
                self._set_status("✓ 评分完成，可点击「⚡ 按建议优化」进行改进")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._score_text.config(state=tk.NORMAL)
                self._score_text.delete("1.0", tk.END)
                self._score_text.insert("1.0", f"[请求失败]\n{msg}")
                self._score_text.config(state=tk.DISABLED)
                self._set_status("✗ 评分失败")
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages, temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    # ─────────────────────────────────────────────────────────────
    #  功能 2b：按评分建议优化
    # ─────────────────────────────────────────────────────────────
    def _improve_by_score(self):
        self._score_text.config(state=tk.NORMAL)
        score_feedback = self._score_text.get("1.0", tk.END).strip()
        self._score_text.config(state=tk.DISABLED)
        try:
            request = self._ai_service.prepare_action(
                "improve_by_score",
                original=self._get_orig(),
                feedback="" if score_feedback.startswith("（") else score_feedback,
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return

        self._set_status("⏳ 正在根据评分建议优化…")
        self._set_busy(True)
        self._set_result("（根据评分建议优化中…）")
        self._result_zh_text.config(state=tk.NORMAL)
        self._result_zh_text.delete("1.0", tk.END)
        self._result_zh_text.config(state=tk.DISABLED)

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._set_result(text)
                self._enable_apply()
                self._push_history(request.history_label, text)
                self._set_busy(False)
                self._show_result_zh(text, "✓ 按评分建议优化完成")
                if self._diff_var.get():
                    self._apply_diff_highlight()
                self._set_status("✓ 按评分建议优化完成，中文翻译中…")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._set_result(f"[请求失败]\n{msg}")
                self._set_status("✗ 请求失败")
                self._set_busy(False)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages,
                temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    # ─────────────────────────────────────────────────────────────
    #  功能 4：中文转英文
    # ─────────────────────────────────────────────────────────────
    def _zh_to_en(self):
        try:
            request = self._ai_service.prepare_action(
                "zh_to_en",
                original=self._get_orig(),
                length=self._length_var.get(),
            )
        except AIOptimizeValidationError:
            messagebox.showinfo("提示", "请在原始框输入中文描述", parent=self)
            return
        self._set_status("⏳ 中文→英文 Prompt 生成中…")
        self._set_busy(True)
        self._set_result("（生成中…）")
        self._result_zh_text.config(state=tk.NORMAL)
        self._result_zh_text.delete("1.0", tk.END)
        self._result_zh_text.config(state=tk.DISABLED)

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._set_result(text)
                self._enable_apply()
                self._push_history(request.history_label, text)
                self._set_busy(False)
                self._show_result_zh(text, "✓ 中文→英文 Prompt 已生成")
                if self._diff_var.get():
                    self._apply_diff_highlight()
                self._set_status("✓ 中文→英文完成，中文对照翻译中…")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._set_result(f"[请求失败]\n{msg}")
                self._set_status("✗ 请求失败")
                self._set_busy(False)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages,
                temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    # ─────────────────────────────────────────────────────────────
    #  功能 5：生成 3 变体
    # ─────────────────────────────────────────────────────────────
    def _gen_variants(self):
        try:
            request = self._ai_service.prepare_action(
                "generate_variants",
                original=self._get_orig(),
                direction=self._preset_var.get(),
                custom_direction=(
                    self._custom_var.get().strip()
                    or "优化英文语法和流畅度，保持原意"
                ),
                length=self._length_var.get(),
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return

        self._set_status("⏳ 生成 3 个变体中…")
        self._set_busy(True)
        self._set_result("（生成变体中…）")
        self._clear_variant_ui()

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                variants = self._parse_variants(text)
                if len(variants) < 2:
                    # 解析失败，直接显示原始回复，仍可应用
                    self._set_result(text)
                    self._enable_apply()
                    self._set_busy(False)
                    self._show_result_zh(text, "✓ 完成（变体格式未识别，显示原始结果）")
                    self._set_status("⚠ 变体格式未识别，显示原始结果，可手动复制使用")
                    return
                self._variants = variants
                self._set_result(variants[0])   # 默认显示第一个
                self._enable_apply()
                self._set_busy(False)
                # 每个变体都入历史
                for i, v in enumerate(reversed(variants)):
                    self._push_history(f"变体{len(variants)-i}", v)
                self._build_variant_ui()        # 构建单选 UI
                self._show_result_zh(variants[0], "✓ 3 个变体已生成")
                if self._diff_var.get():
                    self._apply_diff_highlight()
                self._set_status("✓ 3 个变体已生成，点击下方单选按钮切换")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._set_result(f"[请求失败]\n{msg}")
                self._set_status("✗ 请求失败")
                self._set_busy(False)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages,
                temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    def _parse_variants(self, text: str):
        return self._ai_service.parse_variants(text)

    def _build_variant_ui(self):
        """在变体区渲染 RadioButton，self._variants 必须已填充。"""
        # 先清除旧子控件但不碰 self._variants
        for w in self._variant_frame.winfo_children():
            w.destroy()
        self._variant_frame.pack(fill=tk.X, padx=12, pady=(0, 4))

        tk.Label(self._variant_frame, text="选择变体:", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        self._variant_var.set("0")
        for i, v in enumerate(self._variants):
            preview = v[:28].replace("\n", " ")
            tk.Radiobutton(
                self._variant_frame,
                text=f"  变体{i+1}: {preview}{'…' if len(v) > 28 else ''}",
                variable=self._variant_var, value=str(i),
                bg=BG_BASE, fg=FG_PRIMARY, activebackground=BG_BASE,
                selectcolor=BG_CARD, font=("微软雅黑", 8),
                command=lambda idx=i: self._select_variant(idx),
            ).pack(side=tk.LEFT, padx=(4, 0))

        # 对比按钮
        tk.Button(
            self._variant_frame, text="📊 对比查看", command=self._open_variant_compare,
            bg=ACCENT_PURPLE, fg=DARK_TEXT, relief=tk.FLAT,
            font=("微软雅黑", 8, "bold"), padx=8, pady=2,
            cursor="hand2", activebackground=ACCENT_PURPLE,
        ).pack(side=tk.RIGHT, padx=(0, 4))

    def _open_variant_compare(self):
        """弹出变体对比窗口，三栏并列显示，含中文翻译。"""
        if not self._variants:
            return
        win = tk.Toplevel(self)
        win.title("📊 变体对比")
        win.geometry("1100x680")
        win.configure(bg=BG_BASE)
        win.resizable(True, True)
        win.minsize(700, 460)

        colors = [ACCENT_GREEN, ACCENT_CYAN, ACCENT_ORANGE]

        tk.Label(win, text="点击任意变体右上角的「✅ 使用此变体」将其填入优化结果区",
                 bg=BG_BASE, fg=FG_MUTED, font=("微软雅黑", 9)).pack(anchor="w", padx=14, pady=(10, 6))

        cols_frame = tk.Frame(win, bg=BG_BASE)
        cols_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        for i, variant_text in enumerate(self._variants):
            col = tk.Frame(cols_frame, bg=BG_BASE)
            col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 6, 0))

            hdr = tk.Frame(col, bg=BG_BASE)
            hdr.pack(fill=tk.X, pady=(0, 4))
            tk.Label(hdr, text=f"变体 {i+1}", bg=BG_BASE, fg=colors[i % len(colors)],
                     font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)

            def _use(idx=i, w=win):
                self._select_variant(idx)
                self._variant_var.set(str(idx))
                w.destroy()

            tk.Button(hdr, text="✅ 使用此变体", command=_use,
                      bg=ACCENT_GREEN, fg=DARK_TEXT, relief=tk.FLAT,
                      font=("微软雅黑", 8, "bold"), padx=8, pady=1,
                      cursor="hand2", activebackground=ACCENT_GREEN).pack(side=tk.RIGHT)

            def _copy(t=variant_text):
                import pyperclip
                pyperclip.copy(t)

            tk.Button(hdr, text="📋", command=_copy,
                      bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                      font=("微软雅黑", 8), padx=6, pady=1,
                      cursor="hand2", activebackground=BG_HOVER).pack(side=tk.RIGHT, padx=(0, 4))

            # 英文内容区
            vpaned = ttk.PanedWindow(col, orient=tk.VERTICAL)
            vpaned.pack(fill=tk.BOTH, expand=True)

            en_f = tk.Frame(vpaned, bg=BG_BASE)
            vpaned.add(en_f, weight=3)
            tk.Label(en_f, text="🔤 英文", bg=BG_BASE, fg=colors[i % len(colors)],
                     font=("微软雅黑", 8)).pack(anchor="w")
            txt = tk.Text(en_f, bg=BG_SURFACE, fg=colors[i % len(colors)],
                          relief=tk.FLAT, font=("微软雅黑", 9),
                          wrap=tk.WORD, padx=10, pady=8)
            txt.pack(fill=tk.BOTH, expand=True)
            txt.insert("1.0", variant_text)
            txt.config(state=tk.DISABLED)

            # 中文翻译区
            zh_f = tk.Frame(vpaned, bg=BG_BASE)
            vpaned.add(zh_f, weight=2)
            tk.Label(zh_f, text="🀄 中文翻译", bg=BG_BASE, fg=ACCENT_YELLOW,
                     font=("微软雅黑", 8)).pack(anchor="w")
            zh_txt = tk.Text(zh_f, bg=BG_BASE, fg=ACCENT_YELLOW,
                             relief=tk.FLAT, font=("微软雅黑", 9),
                             wrap=tk.WORD, padx=10, pady=6,
                             state=tk.DISABLED)
            zh_txt.pack(fill=tk.BOTH, expand=True)
            zh_txt.config(state=tk.NORMAL)
            zh_txt.insert("1.0", "（翻译中…）")
            zh_txt.config(state=tk.DISABLED)

            # 触发翻译
            self._translate(variant_text, zh_txt)

    def _clear_variant_ui(self):
        """隐藏变体 UI 并清空列表。"""
        self._variant_frame.pack_forget()
        self._variants.clear()
        self._variant_var.set("")

    def _select_variant(self, idx: int):
        if 0 <= idx < len(self._variants):
            self._set_result(self._variants[idx])
            self._show_result_zh(self._variants[idx])
            if self._diff_var.get():
                self._apply_diff_highlight()

    # ─────────────────────────────────────────────────────────────
    #  功能 6：历史记录
    # ─────────────────────────────────────────────────────────────
    def _push_history(self, direction: str, result: str):
        self._history.insert(0, (direction, result))
        if len(self._history) > 10:
            self._history = self._history[:10]
        self._rebuild_history_menu()

    def _rebuild_history_menu(self):
        self._history_menu.delete(0, tk.END)
        if not self._history:
            self._history_menu.add_command(label="（暂无历史记录）", state=tk.DISABLED)
            return
        for i, (direction, result) in enumerate(self._history):
            preview = result[:20].replace("\n", " ")
            label = f"#{i+1} {direction[:14]}… | {preview}…"
            self._history_menu.add_command(
                label=label,
                command=lambda r=result: self._restore_history(r),
            )

    def _restore_history(self, result: str):
        self._set_result(result)
        self._enable_apply()
        self._show_result_zh(result)
        if self._diff_var.get():
            self._apply_diff_highlight()
        self._set_status("✓ 已从历史记录恢复", 2000)

    # ─────────────────────────────────────────────────────────────
    #  功能 7：关键词提取
    # ─────────────────────────────────────────────────────────────
    def _extract_keywords(self):
        try:
            request = self._ai_service.prepare_action(
                "extract_keywords",
                original=self._get_orig(),
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return
        self._set_status("⏳ 提取关键词中…")

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                keywords = self._ai_service.parse_keywords(text)
                self._build_kw_ui(keywords)
                self._set_status(f"✓ 提取到 {len(keywords)} 个关键词，点击可复制")
            self.after(0, _show)

        def _on_err(msg):
            self.after(0, lambda: self._set_status(f"✗ 提取失败: {msg[:40]}"))

        call_ai(ai_url, ai_key, ai_model, request.messages, temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    def _build_kw_ui(self, keywords):
        InsightsPanel.build_keywords(
            self._kw_frame,
            keywords,
            on_copy=self._copy_kw,
            on_close=self._kw_frame.pack_forget,
        )

    def _copy_kw(self, kw: str):
        pyperclip.copy(kw)
        self._set_status(f"✓ 已复制关键词：{kw}", 1500)

    # ─────────────────────────────────────────────────────────────
    #  功能 8：仅扩写
    # ─────────────────────────────────────────────────────────────
    def _expand_only(self):
        try:
            request = self._ai_service.prepare_action(
                "expand_only",
                original=self._get_orig(),
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return
        self._set_status("⏳ 扩写中…")
        self._set_busy(True)
        self._set_result("（扩写中…）")
        self._result_zh_text.config(state=tk.NORMAL)
        self._result_zh_text.delete("1.0", tk.END)
        self._result_zh_text.config(state=tk.DISABLED)

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._set_result(text)
                self._enable_apply()
                self._push_history(request.history_label, text)
                self._set_busy(False)
                self._show_result_zh(text, "✓ 扩写完成")
                if self._diff_var.get():
                    self._apply_diff_highlight()
                self._set_status("✓ 扩写完成，中文对照翻译中…")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._set_result(f"[请求失败]\n{msg}")
                self._set_status("✗ 请求失败")
                self._set_busy(False)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages,
                temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    # ─────────────────────────────────────────────────────────────
    #  功能 9：差异高亮
    # ─────────────────────────────────────────────────────────────
    def _toggle_diff(self):
        if self._diff_var.get():
            self._apply_diff_highlight()
        else:
            # 关闭时恢复干净文本
            self._result_text.config(state=tk.NORMAL)
            self._result_text.delete("1.0", tk.END)
            self._result_text.insert("1.0", self._raw_result)
            self._result_text.config(state=tk.DISABLED)

    def _apply_diff_highlight(self):
        orig   = self._get_orig()
        result = self._raw_result
        if not result or result.startswith("（") or result.startswith("["):
            return

        orig_words = [w.strip() for w in orig.split(",")   if w.strip()]
        res_words  = [w.strip() for w in result.split(",") if w.strip()]
        orig_set   = {w.lower() for w in orig_words}
        res_set    = {w.lower() for w in res_words}

        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)

        for i, word in enumerate(res_words):
            tag = "added" if word.lower() not in orig_set else "normal"
            self._result_text.insert(tk.END, word, tag)
            if i < len(res_words) - 1:
                self._result_text.insert(tk.END, ", ")

        removed = [w for w in orig_words if w.lower() not in res_set]
        if removed:
            self._result_text.insert(tk.END, "\n\n[已移除: ")
            for i, w in enumerate(removed):
                self._result_text.insert(tk.END, w, "removed")
                if i < len(removed) - 1:
                    self._result_text.insert(tk.END, ", ")
            self._result_text.insert(tk.END, "]")

        self._result_text.config(state=tk.DISABLED)

    # ─────────────────────────────────────────────────────────────
    #  功能 10：直接复制结果
    # ─────────────────────────────────────────────────────────────
    def _copy_result(self):
        result = self._clean_result_text()
        if not result or result.startswith("（") or result.startswith("[请求失败]"):
            self._set_status("⚠ 没有可复制的结果", 1500)
            return
        pyperclip.copy(result)
        self._set_status("✓ 已复制到剪贴板", 1500)

    # ─────────────────────────────────────────────────────────────
    #  应用 / 另存为
    # ─────────────────────────────────────────────────────────────
    def _apply(self):
        result = self._clean_result_text()
        if not result or result.startswith("[请求失败]"):
            messagebox.showinfo("提示", "还没有可用的优化结果", parent=self)
            return
        if self._on_apply:
            self._on_apply(result)
        self.destroy()

    def _saveas(self):
        result = self._clean_result_text()
        if not result or result.startswith("[请求失败]"):
            messagebox.showinfo("提示", "还没有可用的优化结果", parent=self)
            return
        if self._on_saveas:
            self._on_saveas(result)

    # ─────────────────────────────────────────────────────────────
    #  功能 11：引导式创作
    # ─────────────────────────────────────────────────────────────
    def _guided_create(self):
        GuidedCreateDialog(self, on_result=lambda t: (
            self._set_result(t),
            self._enable_apply(),
            self._push_history("引导式创作", t),
            self._show_result_zh(t, "✓ 引导创作完成"),
        ))

    # ─────────────────────────────────────────────────────────────
    #  功能 12：负面词智能推荐
    # ────────────────────────────────────��────────────────────────
    def _recommend_negative(self):
        try:
            request = self._ai_service.prepare_action(
                "recommend_negative",
                original=self._get_orig(),
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return
        self._set_status("⏳ AI 推荐负面词中…")

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._build_neg_rec_ui(text)
                self._set_status("✓ 负面词推荐完成，点击词块可复制")
            self.after(0, _show)

        def _on_err(msg):
            self.after(0, lambda: self._set_status(f"✗ 负面词推荐失败: {msg[:40]}"))

        call_ai(ai_url, ai_key, ai_model, request.messages, temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    def _build_neg_rec_ui(self, text: str):
        def _copy_all(words):
            pyperclip.copy(", ".join(words))
            self._set_status("✓ 已复制全部负面词", 1500)

        InsightsPanel.build_negative_recommendations(
            self._neg_rec_frame,
            self._ai_service.parse_negative_groups(text),
            on_copy=self._copy_kw,
            on_copy_all=_copy_all,
            on_close=self._neg_rec_frame.pack_forget,
        )

    # ─────────────────────────────────────────────────────────────
    #  功能 13：描述转 Prompt
    # ─────────────────────────────────────────────────────────────
    def _desc_to_prompt(self):
        def _on_result(t):
            self._set_result(t)
            self._enable_apply()
            self._push_history("描述转Prompt", t)
            self._show_result_zh(t, "✓ 描述转Prompt完成")

        def _on_replace_orig(t):
            self._orig_text.delete("1.0", tk.END)
            self._orig_text.insert("1.0", t)
            self._orig_zh_text.config(state=tk.NORMAL)
            self._orig_zh_text.delete("1.0", tk.END)
            self._orig_zh_text.insert("1.0", "（翻译中…）")
            self._orig_zh_text.config(state=tk.DISABLED)
            self._translate(t, self._orig_zh_text)
            self._set_status("✓ 已生成到原始 Prompt 框", 2000)

        def _on_merge_orig(t):
            current = self._orig_text.get("1.0", tk.END).strip()
            merged = (current + ", " + t) if current else t
            self._orig_text.delete("1.0", tk.END)
            self._orig_text.insert("1.0", merged)
            self._orig_zh_text.config(state=tk.NORMAL)
            self._orig_zh_text.delete("1.0", tk.END)
            self._orig_zh_text.insert("1.0", "（翻译中…）")
            self._orig_zh_text.config(state=tk.DISABLED)
            self._translate(merged, self._orig_zh_text)
            self._set_status("✓ 已合入原始 Prompt 框", 2000)

        DescToPromptDialog(self,
                           on_result=_on_result,
                           on_replace_orig=_on_replace_orig,
                           on_merge_orig=_on_merge_orig)

    # ─────────────────────────────────────────────────────────────
    #  功能 14：合规检验
    # ─────────────────────────────────────────────────────────────
    def _compliance_check(self):
        try:
            request = self._ai_service.prepare_action(
                "compliance_check",
                original=self._get_orig(),
            )
        except AIOptimizeValidationError as exc:
            messagebox.showinfo("提示", str(exc), parent=self)
            return
        self._set_status("⏳ 合规检验中…")
        self._compliance_frame.pack(fill=tk.X, padx=12, pady=(2, 4))
        for w in self._compliance_frame.winfo_children():
            w.destroy()

        # 标题行
        hdr = tk.Frame(self._compliance_frame, bg=BG_BASE)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🛡 合规检验结果", bg=BG_BASE, fg="#94e2d5",
                 font=("微软雅黑", 9, "bold")).pack(side=tk.LEFT)
        tk.Button(hdr, text="✕ 关闭", command=self._compliance_frame.pack_forget,
                  bg=BG_HOVER, fg=FG_MUTED, relief=tk.FLAT,
                  font=("微软雅黑", 8), padx=4, pady=0,
                  cursor="hand2", activebackground=BG_HOVER).pack(side=tk.RIGHT)

        self._compliance_text = tk.Text(
            self._compliance_frame, bg=BG_SURFACE, fg="#94e2d5",
            relief=tk.FLAT, font=("微软雅黑", 9),
            wrap=tk.WORD, padx=8, pady=6, height=6,
            state=tk.DISABLED,
        )
        self._compliance_text.pack(fill=tk.X, padx=6, pady=(4, 4))
        self._compliance_text.tag_config("violation", foreground=ACCENT_RED, font=("微软雅黑", 9, "bold"))
        self._compliance_text.tag_config("warning",   foreground=ACCENT_YELLOW)
        self._compliance_text.tag_config("ok",        foreground=ACCENT_GREEN)
        self._compliance_text.tag_config("normal",    foreground="#94e2d5")

        self._compliance_text.config(state=tk.NORMAL)
        self._compliance_text.delete("1.0", tk.END)
        self._compliance_text.insert("1.0", "（检验中…）")
        self._compliance_text.config(state=tk.DISABLED)

        # 按建议修复按钮
        fix_row = tk.Frame(self._compliance_frame, bg=BG_BASE)
        fix_row.pack(fill=tk.X, padx=6, pady=(0, 6))
        self._compliance_fix_btn = tk.Button(
            fix_row, text="⚡ 按建议修复 Prompt", command=self._compliance_fix,
            bg=ACCENT_ORANGE, fg=DARK_TEXT, relief=tk.FLAT,
            font=("微软雅黑", 8, "bold"), padx=10, pady=2,
            cursor="hand2", activebackground=ACCENT_ORANGE, state=tk.DISABLED,
        )
        self._compliance_fix_btn.pack(side=tk.LEFT)
        Tooltip(self._compliance_fix_btn,
                "⚡ 按建议修复\n让 AI 根据合规检验结果，将违规词替换为安全的近义词，修复后填入结果区。")
        self._compliance_raw = ""

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._compliance_raw = text
                self._compliance_text.config(state=tk.NORMAL)
                self._compliance_text.delete("1.0", tk.END)
                # 简单高亮：含"违规"/"风险"/"禁止"行用红色
                for line in text.split("\n"):
                    low = line.lower()
                    if any(k in line for k in ["违规", "风险", "禁止", "敏感", "❌"]):
                        self._compliance_text.insert(tk.END, line + "\n", "violation")
                    elif "建议" in line or "修复" in line or "替换" in line:
                        self._compliance_text.insert(tk.END, line + "\n", "warning")
                    elif "通过" in line or "无需" in line or "✅" in line:
                        self._compliance_text.insert(tk.END, line + "\n", "ok")
                    else:
                        self._compliance_text.insert(tk.END, line + "\n", "normal")
                self._compliance_text.config(state=tk.DISABLED)
                self._compliance_fix_btn.config(state=tk.NORMAL)
                self._set_status("✓ 合规检验完成")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._compliance_text.config(state=tk.NORMAL)
                self._compliance_text.delete("1.0", tk.END)
                self._compliance_text.insert("1.0", f"[检验失败]\n{msg}", "violation")
                self._compliance_text.config(state=tk.DISABLED)
                self._set_status("✗ 合规检验失败")
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages, temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)

    def _compliance_fix(self):
        try:
            request = self._ai_service.prepare_action(
                "compliance_fix",
                original=self._get_orig(),
                feedback=self._compliance_raw,
            )
        except AIOptimizeValidationError:
            return
        self._set_status("⏳ 正在修复违规内容…")
        self._set_busy(True)
        self._set_result("（合规修复中…）")

        ai_url, ai_key, ai_model = get_ai_config()

        def _on_ok(text):
            def _show():
                self._set_result(text)
                self._enable_apply()
                self._push_history(request.history_label, text)
                self._set_busy(False)
                self._show_result_zh(text, "✓ 合规修复完成")
                if self._diff_var.get():
                    self._apply_diff_highlight()
                self._set_status("✓ 合规修复完成，请核查结果区")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._set_result(f"[请求失败]\n{msg}")
                self._set_status("✗ 修复失败")
                self._set_busy(False)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, request.messages,
                temperature=request.temperature,
                on_success=_on_ok, on_error=_on_err)


class GuidedCreateDialog(tk.Toplevel):

    GUIDE_QUESTIONS = [
        ("画面主体", "描述你想要的主体：人物、动物或物体（例：一位红发少女、一只白色猫咪）"),
        ("场景环境", "描述场景和背景：地点、时间、天气（例：樱花林中、夜晚城市街道）"),
        ("情绪氛围", "描述你想要的情绪和氛围（例：温馨浪漫、神秘暗黑、轻快活泼）"),
        ("画面风格", "描述画面风格（例：写实摄影、水彩插画、赛博朋克、日系动漫）"),
        ("特殊要求", "有没有特殊要求？如构图、光线、色调（例：特写镜头、金色逆光、低饱和度）"),
    ]

    def __init__(self, parent, on_result=None):
        super().__init__(parent)
        self.title("🧙 引导式创作")
        self.geometry("680x480")
        self.configure(bg=BG_BASE)
        self.resizable(True, True)
        self.minsize(520, 380)
        self.grab_set()

        self._on_result = on_result
        self._answers   = []
        self._step      = 0
        self._parent_dialog = parent

        self._build_ui()
        self._show_step()

    def _build_ui(self):
        from shared.ui_kit import BG_BASE, BG_SURFACE, BG_CARD, BG_HOVER, FG_PRIMARY, FG_MUTED, ACCENT_BLUE, ACCENT_GREEN, ACCENT_CYAN, DARK_TEXT

        top = tk.Frame(self, bg=BG_BASE)
        top.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Label(top, text="🧙 引导式创作 — 逐步问答生成 Prompt",
                 bg=BG_BASE, fg=FG_PRIMARY, font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(top, text="✕ 关闭", command=self.destroy,
                  bg=ACCENT_RED, fg=DARK_TEXT, relief=tk.FLAT,
                  font=("微软雅黑", 9, "bold"), padx=10, pady=2,
                  cursor="hand2", activebackground=ACCENT_RED).pack(side=tk.RIGHT)

        # 进度条区
        self._prog_frame = tk.Frame(self, bg=BG_BASE)
        self._prog_frame.pack(fill=tk.X, padx=14, pady=(0, 8))

        # 问答历史（左侧）
        content = tk.Frame(self, bg=BG_BASE)
        content.pack(fill=tk.BOTH, expand=True, padx=14)

        # 历史区
        hist_frame = tk.Frame(content, bg=BG_BASE)
        hist_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        tk.Label(hist_frame, text="问答历史", bg=BG_BASE, fg=FG_MUTED,
                 font=("微软雅黑", 8)).pack(anchor="w")
        self._hist_text = tk.Text(hist_frame, bg=BG_SURFACE, fg=FG_MUTED,
                                  relief=tk.FLAT, font=("微软雅黑", 9),
                                  wrap=tk.WORD, padx=8, pady=6,
                                  state=tk.DISABLED, height=6)
        self._hist_text.pack(fill=tk.BOTH, expand=True)

        # 当前问题区
        q_frame = tk.Frame(content, bg=BG_BASE)
        q_frame.pack(fill=tk.X, pady=(0, 6))
        self._q_label = tk.Label(q_frame, text="", bg=BG_BASE, fg=ACCENT_CYAN,
                                 font=("微软雅黑", 9, "bold"), wraplength=600, justify=tk.LEFT)
        self._q_label.pack(anchor="w", pady=(0, 4))
        self._q_hint  = tk.Label(q_frame, text="", bg=BG_BASE, fg=FG_MUTED,
                                 font=("微软雅黑", 8), wraplength=600, justify=tk.LEFT)
        self._q_hint.pack(anchor="w", pady=(0, 6))

        self._ans_var = tk.StringVar()
        self._ans_entry = tk.Entry(q_frame, textvariable=self._ans_var, bg=BG_CARD, fg=FG_PRIMARY,
                                   insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                   font=("微软雅黑", 10))
        self._ans_entry.pack(fill=tk.X, ipady=6)
        self._ans_entry.bind("<Return>", lambda _e: self._next())

        btn_row = tk.Frame(content, bg=BG_BASE)
        btn_row.pack(fill=tk.X, pady=(6, 12))
        self._skip_btn = tk.Button(btn_row, text="跳过", command=self._skip,
                                   bg=BG_HOVER, fg=FG_PRIMARY, relief=tk.FLAT,
                                   font=("微软雅黑", 9), padx=10, pady=3,
                                   cursor="hand2", activebackground=BG_HOVER)
        self._skip_btn.pack(side=tk.LEFT, padx=(0, 6))
        self._next_btn = tk.Button(btn_row, text="下一步 ▶", command=self._next,
                                   bg=ACCENT_BLUE, fg=DARK_TEXT, relief=tk.FLAT,
                                   font=("微软雅黑", 9, "bold"), padx=14, pady=3,
                                   cursor="hand2", activebackground=ACCENT_BLUE)
        self._next_btn.pack(side=tk.LEFT)
        self._status_lbl = tk.Label(btn_row, text="", bg=BG_BASE, fg=ACCENT_YELLOW,
                                    font=("微软雅黑", 9))
        self._status_lbl.pack(side=tk.LEFT, padx=10)

    def _show_step(self):
        total = len(self.GUIDE_QUESTIONS)
        # 进度
        for w in self._prog_frame.winfo_children():
            w.destroy()
        for i in range(total):
            color = ACCENT_GREEN if i < self._step else (ACCENT_BLUE if i == self._step else BG_CARD)
            tk.Label(self._prog_frame, text=f"  {i+1}  ",
                     bg=color, fg=DARK_TEXT if color != BG_CARD else FG_MUTED,
                     font=("微软雅黑", 8, "bold"), relief=tk.FLAT, padx=4).pack(side=tk.LEFT, padx=2)

        if self._step < total:
            key, hint = self.GUIDE_QUESTIONS[self._step]
            self._q_label.config(text=f"问题 {self._step+1}/{total}：{key}")
            self._q_hint.config(text=f"提示：{hint}")
            self._ans_var.set("")
            self._ans_entry.config(state=tk.NORMAL)
            self._next_btn.config(text="下一步 ▶" if self._step < total-1 else "生成 Prompt 🚀",
                                  bg=ACCENT_BLUE if self._step < total-1 else ACCENT_GREEN)
            self._ans_entry.focus_set()

    def _next(self):
        ans = self._ans_var.get().strip()
        if not ans:
            ans = "（未填写）"
        self._record(ans)

    def _skip(self):
        self._record("（跳过）")

    def _record(self, ans):
        key, _ = self.GUIDE_QUESTIONS[self._step]
        self._answers.append((key, ans))
        self._append_hist(f"Q{self._step+1} {key}：{ans}\n")
        self._step += 1
        if self._step >= len(self.GUIDE_QUESTIONS):
            self._generate()
        else:
            self._show_step()

    def _append_hist(self, text):
        self._hist_text.config(state=tk.NORMAL)
        self._hist_text.insert(tk.END, text)
        self._hist_text.see(tk.END)
        self._hist_text.config(state=tk.DISABLED)

    def _generate(self):
        self._ans_entry.config(state=tk.DISABLED)
        self._next_btn.config(state=tk.DISABLED)
        self._skip_btn.config(state=tk.DISABLED)
        self._status_lbl.config(text="⏳ AI 生成中…")
        self._q_label.config(text="正在生成完整 Prompt…")
        self._q_hint.config(text="")

        from shared.config import get_ai_config
        from features.ai_optimize.client import call_ai

        answers_str = "\n".join(f"{k}：{v}" for k, v in self._answers)
        ai_url, ai_key, ai_model = get_ai_config()
        messages = [
            {"role": "system", "content":
                "你是专业的 AI 绘画/摄影 Prompt 生成专家。"
                "用户会提供 5 个维度的描述，请将其综合为一段完整、专业的英文 Prompt。"
                "格式：逗号分隔关键词，包含主体+场景+风格+情绪+质量词。"
                "只输出英文 Prompt，不要有任何解释或中文。"},
            {"role": "user", "content": f"请根据以下信息生成英文 Prompt：\n{answers_str}"},
        ]

        def _on_ok(text):
            def _show():
                self._status_lbl.config(text="✓ 已生成！")
                self._append_hist(f"\n生成结果：\n{text}\n")
                if self._on_result:
                    self._on_result(text)
                self.after(1200, self.destroy)
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._status_lbl.config(text=f"✗ 失败：{msg[:40]}")
                self._next_btn.config(state=tk.NORMAL)
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, messages, on_success=_on_ok, on_error=_on_err)


# ─────────────────────────────────────────────────────────────────
#  描述转 Prompt 弹窗
# ─────────────────────────────────────────────────────────────────
class DescToPromptDialog(tk.Toplevel):

    def __init__(self, parent, on_result=None, on_replace_orig=None, on_merge_orig=None):
        super().__init__(parent)
        self.title("📖 描述转 Prompt")
        self.geometry("640x440")
        self.configure(bg=BG_BASE)
        self.resizable(True, True)
        self.minsize(500, 360)
        self.grab_set()

        self._on_result       = on_result
        self._on_replace_orig = on_replace_orig
        self._on_merge_orig   = on_merge_orig
        self._build_ui()

    def _build_ui(self):
        top = tk.Frame(self, bg=BG_BASE)
        top.pack(fill=tk.X, padx=14, pady=(12, 6))
        tk.Label(top, text="📖 描述转 Prompt — 将自然语言提炼为英文提示词",
                 bg=BG_BASE, fg=FG_PRIMARY, font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(top, text="✕ 关闭", command=self.destroy,
                  bg=ACCENT_RED, fg=DARK_TEXT, relief=tk.FLAT,
                  font=("微软雅黑", 9, "bold"), padx=10, pady=2,
                  cursor="hand2", activebackground=ACCENT_RED).pack(side=tk.RIGHT)

        tk.Label(self, text="输入描述（中文/英文均可，可以是小说片段、场景说明、简单描述）：",
                 bg=BG_BASE, fg=FG_MUTED, font=("微软雅黑", 9)).pack(anchor="w", padx=14, pady=(0, 4))

        self._input_text = tk.Text(self, bg=BG_CARD, fg=FG_PRIMARY,
                                   insertbackground=FG_PRIMARY, relief=tk.FLAT,
                                   font=("微软雅黑", 9), wrap=tk.WORD, padx=8, pady=6,
                                   height=6)
        self._input_text.pack(fill=tk.X, padx=14, pady=(0, 8))

        btn_row = tk.Frame(self, bg=BG_BASE)
        btn_row.pack(fill=tk.X, padx=14, pady=(0, 6))
        self._convert_btn = tk.Button(btn_row, text="🔄 转换",
                                      command=self._convert,
                                      bg=ACCENT_BLUE, fg=DARK_TEXT, relief=tk.FLAT,
                                      font=("微软雅黑", 9, "bold"), padx=14, pady=3,
                                      cursor="hand2", activebackground=ACCENT_BLUE)
        self._convert_btn.pack(side=tk.LEFT)
        self._status_lbl = tk.Label(btn_row, text="", bg=BG_BASE, fg=ACCENT_YELLOW,
                                    font=("微软雅黑", 9))
        self._status_lbl.pack(side=tk.LEFT, padx=10)

        tk.Label(self, text="转换结果预览：",
                 bg=BG_BASE, fg=FG_MUTED, font=("微软雅黑", 9)).pack(anchor="w", padx=14, pady=(0, 4))

        self._result_text = tk.Text(self, bg=BG_SURFACE, fg=ACCENT_GREEN,
                                    relief=tk.FLAT, font=("微软雅黑", 9),
                                    wrap=tk.WORD, padx=8, pady=6,
                                    height=5, state=tk.DISABLED)
        self._result_text.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 8))

        act_row = tk.Frame(self, bg=BG_BASE)
        act_row.pack(fill=tk.X, padx=14, pady=(0, 12))
        self._use_btn = tk.Button(act_row, text="✅ 填入结果区",
                                  command=self._use_result,
                                  bg=ACCENT_GREEN, fg=DARK_TEXT, relief=tk.FLAT,
                                  font=("微软雅黑", 9, "bold"), padx=12, pady=3,
                                  cursor="hand2", activebackground=ACCENT_GREEN,
                                  state=tk.DISABLED)
        self._use_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._replace_btn = tk.Button(act_row, text="📝 生成到原始框",
                                      command=self._replace_orig,
                                      bg=ACCENT_BLUE, fg=DARK_TEXT, relief=tk.FLAT,
                                      font=("微软雅黑", 9, "bold"), padx=12, pady=3,
                                      cursor="hand2", activebackground=ACCENT_BLUE,
                                      state=tk.DISABLED)
        self._replace_btn.pack(side=tk.LEFT, padx=(0, 6))

        self._merge_btn = tk.Button(act_row, text="🔗 合入原始框",
                                    command=self._merge_orig,
                                    bg=ACCENT_CYAN, fg=DARK_TEXT, relief=tk.FLAT,
                                    font=("微软雅黑", 9, "bold"), padx=12, pady=3,
                                    cursor="hand2", activebackground=ACCENT_CYAN,
                                    state=tk.DISABLED)
        self._merge_btn.pack(side=tk.LEFT)
        self._raw = ""

    def _convert(self):
        desc = self._input_text.get("1.0", tk.END).strip()
        if not desc:
            self._status_lbl.config(text="⚠ 请先输入描述内容")
            return
        self._convert_btn.config(state=tk.DISABLED)
        self._status_lbl.config(text="⏳ 转换中…")
        self._result_text.config(state=tk.NORMAL)
        self._result_text.delete("1.0", tk.END)
        self._result_text.insert("1.0", "（转换中…）")
        self._result_text.config(state=tk.DISABLED)

        from shared.config import get_ai_config
        from features.ai_optimize.client import call_ai

        ai_url, ai_key, ai_model = get_ai_config()
        messages = [
            {"role": "system", "content":
                "你是专业的 AI 绘画 Prompt 生成专家。"
                "用户会给你一段自然语言描述（中文或英文），"
                "请将其提炼为英文 Prompt（逗号分隔关键词，主体+场景+风格+质量词结构）。"
                "只输出英文 Prompt，不要任何解释或中文。"},
            {"role": "user", "content": desc},
        ]

        def _on_ok(text):
            def _show():
                self._raw = text
                self._result_text.config(state=tk.NORMAL)
                self._result_text.delete("1.0", tk.END)
                self._result_text.insert("1.0", text)
                self._result_text.config(state=tk.DISABLED)
                self._use_btn.config(state=tk.NORMAL)
                self._replace_btn.config(state=tk.NORMAL)
                self._merge_btn.config(state=tk.NORMAL)
                self._convert_btn.config(state=tk.NORMAL)
                self._status_lbl.config(text="✓ 转换完成")
            self.after(0, _show)

        def _on_err(msg):
            def _show():
                self._result_text.config(state=tk.NORMAL)
                self._result_text.delete("1.0", tk.END)
                self._result_text.insert("1.0", f"[失败]\n{msg}")
                self._result_text.config(state=tk.DISABLED)
                self._convert_btn.config(state=tk.NORMAL)
                self._status_lbl.config(text="✗ 转换失败")
            self.after(0, _show)

        call_ai(ai_url, ai_key, ai_model, messages, on_success=_on_ok, on_error=_on_err)

    def _use_result(self):
        if self._raw and self._on_result:
            self._on_result(self._raw)
        self.destroy()

    def _replace_orig(self):
        if self._raw and self._on_replace_orig:
            self._on_replace_orig(self._raw)
        self.destroy()

    def _merge_orig(self):
        if self._raw and self._on_merge_orig:
            self._on_merge_orig(self._raw)
        self.destroy()
