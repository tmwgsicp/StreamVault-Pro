import asyncio
import os
import re
from typing import Optional

import flet as ft

from ...utils.logger import logger


class TranscriptDialog(ft.AlertDialog):
    def __init__(self, app, recording):
        self.app = app
        self.recording = recording
        self._ = {}
        self.transcript_content = ""
        self.search_text = None
        self.content_text = None
        self.word_count_text = None
        self.load_language()
        
        # 加载文案内容
        self.load_transcript()
        
        super().__init__(
            title=ft.Text(self._["transcript_dialog_title"] + f" - {recording.title}"),
            content=self.create_content(),
            actions=self.create_actions(),
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
        )

    def load_language(self):
        language = self.app.language_manager.language
        for key in ("recording_card", "base", "transcripts_page"):
            self._.update(language.get(key, {}))

    def load_transcript(self):
        """加载文案内容"""
        try:
            if not self.recording.recording_dir or not os.path.exists(self.recording.recording_dir):
                self.transcript_content = ""
                return
            
            # 查找文案文件（支持多种格式）
            transcript_files = []
            for root, _, files in os.walk(self.recording.recording_dir):
                for file in files:
                    if file.endswith(('.txt', '.srt', '.vtt', '.lrc')):
                        transcript_files.append(os.path.join(root, file))
            
            if not transcript_files:
                self.transcript_content = ""
                return
            
            # 按修改时间排序，获取最新的文案文件
            transcript_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            latest_transcript = transcript_files[0]
            
            with open(latest_transcript, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 根据文件类型处理内容
            if latest_transcript.endswith('.srt'):
                self.transcript_content = self.extract_text_from_srt(content)
            elif latest_transcript.endswith('.vtt'):
                self.transcript_content = self.extract_text_from_vtt(content)
            else:
                self.transcript_content = content
                
        except Exception as e:
            logger.error(f"加载文案失败: {e}")
            self.transcript_content = ""

    def extract_text_from_srt(self, srt_content: str) -> str:
        """从SRT格式中提取纯文本"""
        lines = srt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            # 跳过序号行和时间戳行
            if line.isdigit() or '-->' in line or not line:
                continue
            text_lines.append(line)
        
        return '\n'.join(text_lines)

    def extract_text_from_vtt(self, vtt_content: str) -> str:
        """从VTT格式中提取纯文本"""
        lines = vtt_content.split('\n')
        text_lines = []
        skip_header = True
        
        for line in lines:
            line = line.strip()
            # 跳过WebVTT头部
            if skip_header and (line.startswith('WEBVTT') or line.startswith('NOTE') or not line):
                continue
            skip_header = False
            
            # 跳过时间戳行
            if '-->' in line or not line:
                continue
            text_lines.append(line)
        
        return '\n'.join(text_lines)

    def create_content(self):
        """创建对话框内容"""
        if not self.transcript_content.strip():
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.DESCRIPTION, size=64, color=ft.Colors.GREY_400),
                    ft.Text(
                        self._["no_transcript_available"] if "no_transcript_available" in self._ else "暂无文案内容",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.GREY_600,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "录制完成后会自动生成文案内容，支持txt、srt、vtt等格式",
                        size=14,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.Colors.GREY_500
                    ),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        text="重新扫描文案文件",
                        icon=ft.Icons.REFRESH,
                        on_click=self.refresh_transcript,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE_100,
                            color=ft.Colors.BLUE_700,
                        )
                    ),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15),
                height=500,
                width=750,
                alignment=ft.alignment.center
            )
        
        # 搜索框
        self.search_text = ft.TextField(
            label=self._["search_in_transcript"] if "search_in_transcript" in self._ else "在文案中搜索",
            hint_text="输入关键词进行搜索...",
            width=350,
            on_change=self.on_search_change,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
        )
        
        # 字数统计和文件信息
        word_count = len(self.transcript_content.replace('\n', '').replace(' ', ''))
        line_count = len([line for line in self.transcript_content.split('\n') if line.strip()])
        
        self.word_count_text = ft.Text(
            f"共 {word_count} 字 | {line_count} 行",
            size=12,
            color=ft.Colors.GREY_600
        )
        
        # 清除搜索按钮
        clear_search_btn = ft.IconButton(
            icon=ft.Icons.CLEAR,
            tooltip="清除搜索",
            on_click=self.clear_search,
            icon_size=16,
        )
        
        # 文案内容显示
        self.content_text = ft.Text(
            self.transcript_content,
            size=14,
            selectable=True,
            expand=True,
        )
        
        # 工具栏
        toolbar = ft.Row([
            self.search_text,
            clear_search_btn,
            ft.Container(expand=True),
            self.word_count_text,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        # 内容区域
        content_area = ft.Container(
            content=ft.ListView([self.content_text], expand=True, padding=ft.Padding(15, 10, 15, 10)),
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50 if self.app.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_900,
        )
        
        return ft.Container(
            content=ft.Column([
                toolbar,
                ft.Divider(height=1, thickness=1),
                content_area
            ], spacing=10),
            width=750,
            height=500,
        )

    def create_actions(self):
        """创建操作按钮"""
        actions = []
        
        if self.transcript_content.strip():
            actions.extend([
                ft.TextButton(
                    text="复制文案",
                    icon=ft.Icons.COPY,
                    on_click=self.copy_transcript
                ),
                ft.TextButton(
                    text="刷新",
                    icon=ft.Icons.REFRESH,
                    on_click=self.refresh_transcript
                ),
            ])
        
        actions.append(
            ft.TextButton(
                text=self._.get("close", "关闭"),
                on_click=self.close_dialog
            )
        )
        
        return actions

    async def refresh_transcript(self, e=None):
        """刷新文案内容"""
        try:
            self.load_transcript()
            # 重新创建内容
            self.content = self.create_content()
            self.actions = self.create_actions()
            self.update()
            await self.app.snack_bar.show_snack_bar("文案内容已刷新", bgcolor=ft.Colors.GREEN)
        except Exception as e:
            logger.error(f"刷新文案失败: {e}")
            await self.app.snack_bar.show_snack_bar("刷新失败")

    async def clear_search(self, e):
        """清除搜索"""
        if self.search_text:
            self.search_text.value = ""
            self.search_text.update()
        if self.content_text:
            self.content_text.value = self.transcript_content
            self.content_text.update()

    async def on_search_change(self, e):
        """搜索功能"""
        search_term = e.data.strip() if e.data else ""
        if not search_term:
            # 恢复原始内容
            self.content_text.value = self.transcript_content
        else:
            # 高亮搜索词
            highlighted_content = self.highlight_search_term(self.transcript_content, search_term)
            self.content_text.value = highlighted_content
        
        self.content_text.update()

    def highlight_search_term(self, content: str, search_term: str) -> str:
        """高亮搜索词（简单文本替换）"""
        if not search_term:
            return content
        
        # 使用特殊标记高亮搜索词
        pattern = re.compile(re.escape(search_term), re.IGNORECASE)
        return pattern.sub(f"🔍 {search_term} 🔍", content)

    async def copy_transcript(self, e):
        """复制文案到剪贴板"""
        try:
            # 直接使用同步API，更稳定
            self.app.page.set_clipboard(self.transcript_content)
            await self.app.snack_bar.show_snack_bar("文案已复制到剪贴板", bgcolor=ft.Colors.GREEN)
        except Exception as e:
            logger.error(f"复制文案失败: {e}")
            await self.app.snack_bar.show_snack_bar("复制失败")



    async def close_dialog(self, e):
        """关闭对话框"""
        self.open = False
        self.update() 