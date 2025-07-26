import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

import flet as ft

from ...utils.logger import logger
from ..base_page import PageBase
from ..components.transcript_dialog import TranscriptDialog


class TranscriptsPage(PageBase):
    def __init__(self, app):
        super().__init__(app)
        self.page_name = "transcripts"
        self.transcript_items = []
        self.filtered_items = []
        self.search_field = None
        self.filter_dropdown = None
        self.transcript_list = None
        self.selected_items = set()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._ = {}
        self.page_initialized = False
        self.stats_row = None
        self.load_language()
        self.app.language_manager.add_observer(self)

    def load_language(self):
        language = self.app.language_manager.language
        for key in ("transcripts_page", "base", "recording_card"):
            self._.update(language.get(key, {}))

    async def load(self):
        """加载文案管理页面"""
        # 如果页面已经初始化，直接刷新数据即可
        if self.page_initialized and self.content_area.controls:
            await self.load_transcripts()
            return
        
        # 首次加载：清空现有内容并设置完整UI
        self.content_area.controls.clear()
        
        # 设置UI
        await self.setup_ui()
        
        # 确保UI已经渲染到页面
        self.content_area.update()
        await asyncio.sleep(0.1)  # 给UI渲染一点时间
        
        # 标记为已初始化
        self.page_initialized = True
        
        # 加载数据
        await self.load_transcripts()

    async def setup_ui(self):
        """设置用户界面"""
        # 页面标题
        title_row = ft.Row([
            ft.Text(
                self._["page_title"] if "page_title" in self._ else "文案管理", 
                theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                weight=ft.FontWeight.BOLD
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                tooltip=self._["refresh_transcripts"] if "refresh_transcripts" in self._ else "刷新",
                on_click=self.refresh_transcripts,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_100)
            ),
            ft.IconButton(
                icon=ft.Icons.DOWNLOAD,
                tooltip=self._["export_all"] if "export_all" in self._ else "导出全部",
                on_click=self.export_all_transcripts,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100)
            ),
        ])

        # 搜索和筛选区域
        self.search_field = ft.TextField(
            label=self._["search_transcripts"] if "search_transcripts" in self._ else "搜索文案",
            width=300,
            on_change=self.on_search_change,
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
        )

        self.filter_dropdown = ft.Dropdown(
            label=self._["filter_by_date"] if "filter_by_date" in self._ else "按日期筛选",
            width=150,
            options=[
                ft.dropdown.Option("all", self._["filter_all"] if "filter_all" in self._ else "全部"),
                ft.dropdown.Option("today", self._["filter_today"] if "filter_today" in self._ else "今天"),
                ft.dropdown.Option("week", self._["filter_week"] if "filter_week" in self._ else "本周"),
                ft.dropdown.Option("month", self._["filter_month"] if "filter_month" in self._ else "本月"),
            ],
            value="all",
            on_change=self.on_filter_change,
        )

        # 批量操作按钮
        action_buttons = ft.Row([
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.SELECT_ALL, size=16),
                    ft.Text("全选", size=12)
                ], spacing=5, tight=True),
                on_click=self.select_all_items,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            ),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.CLEAR, size=16),
                    ft.Text("清空选择", size=12)
                ], spacing=5, tight=True),
                on_click=self.clear_selection,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREY_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            ),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_SWEEP, size=16),
                    ft.Text("批量删除", size=12)
                ], spacing=5, tight=True),
                on_click=self.batch_delete_transcripts,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_600,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            ),
        ], spacing=10)

        filter_row = ft.Row([
            self.search_field,
            self.filter_dropdown,
            ft.Container(expand=True),
            action_buttons,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # 文案列表区域
        self.transcript_list = ft.ListView(expand=True, spacing=8, padding=ft.Padding(10, 5, 10, 5))
        
        # 列表容器
        list_container = ft.Container(
            content=self.transcript_list,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.WHITE if self.app.page.theme_mode == ft.ThemeMode.LIGHT else ft.Colors.GREY_900,
        )

        # 统计信息
        self.stats_row = ft.Row([
            ft.Icon(ft.Icons.DESCRIPTION, size=16, color=ft.Colors.GREY_600),
            ft.Text("正在加载文案数据...", size=12, color=ft.Colors.GREY_600),
        ], spacing=5)

        # 添加所有组件到页面
        page_column = ft.Column([
            title_row,
            ft.Divider(height=1, thickness=1),
            filter_row,
            ft.Container(height=5),
            self.stats_row,
            ft.Container(height=5),
            list_container,
        ], expand=True, spacing=10)

        self.content_area.controls.append(
            ft.Container(content=page_column, padding=20, expand=True)
        )

    async def load_transcripts(self):
        """加载所有文案数据"""
        try:
            # 显示加载状态
            self.show_loading_state()
            
            # 在后台线程中扫描文件
            self.transcript_items = await asyncio.get_event_loop().run_in_executor(
                self.executor, self._scan_transcript_files
            )
            
            # 更新统计信息
            self.update_stats()
            
            # 应用筛选并显示结果
            await self.apply_filters()
            
        except Exception as e:
            logger.error(f"加载文案失败: {e}")
            await self.show_empty_state("加载文案失败", f"错误详情: {str(e)}")

    def show_loading_state(self):
        """显示加载状态"""
        try:
            loading_container = ft.Container(
                content=ft.Column([
                    ft.ProgressRing(width=40, height=40),
                    ft.Text("正在扫描文案文件...", size=16, color=ft.Colors.GREY_600),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15),
                height=200,
                alignment=ft.alignment.center
            )
            
            # 确保transcript_list存在且已正确初始化
            if self.transcript_list and hasattr(self.transcript_list, 'controls'):
                self.transcript_list.controls = [loading_container]
                # 只有在页面已经渲染的情况下才调用update
                if self.page_initialized and hasattr(self.transcript_list, 'page') and self.transcript_list.page:
                    self.transcript_list.update()
        except Exception as e:
            logger.error(f"显示加载状态失败: {e}")
            # 如果加载状态显示失败，直接跳过

    def update_stats(self):
        """更新统计信息"""
        total_count = len(self.transcript_items)
        total_words = sum(item.get('word_count', 0) for item in self.transcript_items)
        
        if total_count == 0:
            stats_text = "暂无文案内容"
        else:
            stats_text = f"共找到 {total_count} 个文案文件，总计 {total_words:,} 字"
        
        if self.stats_row and len(self.stats_row.controls) > 1:
            self.stats_row.controls[1].value = stats_text
            self.stats_row.update()

    def _scan_transcript_files(self) -> List[Dict]:
        """扫描所有文案文件"""
        transcript_items = []
        
        # 获取视频保存路径
        try:
            save_path = self.app.settings.get_video_save_path()
        except:
            save_path = self.app.settings.default_config.get("video_save_path", "")
        
        if not save_path or not os.path.exists(save_path):
            return transcript_items
        
        # 递归扫描所有文案文件
        for root, dirs, files in os.walk(save_path):
            for file in files:
                if file.endswith(('.txt', '.srt', '.vtt', '.lrc')):
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        
                        # 读取文件内容
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 提取纯文本内容
                        if file.endswith('.srt'):
                            text_content = self._extract_text_from_srt(content)
                        elif file.endswith('.vtt'):
                            text_content = self._extract_text_from_vtt(content)
                        else:
                            text_content = content
                        
                        if text_content.strip():
                            # 计算字数
                            word_count = len(text_content.replace('\n', '').replace(' ', ''))
                            
                            # 生成预览文本（前100字符）
                            preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
                            
                            transcript_items.append({
                                'file_path': file_path,
                                'file_name': file,
                                'folder_name': os.path.basename(root),
                                'content': text_content,
                                'preview': preview.replace('\n', ' '),
                                'word_count': word_count,
                                'created_time': datetime.fromtimestamp(stat.st_ctime),
                                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                                'file_size': stat.st_size,
                            })
                    except Exception as e:
                        logger.warning(f"读取文案文件失败 {file_path}: {e}")
        
        # 按修改时间排序
        transcript_items.sort(key=lambda x: x['modified_time'], reverse=True)
        return transcript_items

    def _extract_text_from_srt(self, srt_content: str) -> str:
        """从SRT字幕文件中提取纯文本"""
        lines = srt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            if line.isdigit() or '-->' in line or not line:
                continue
            text_lines.append(line)
        
        return '\n'.join(text_lines)

    def _extract_text_from_vtt(self, vtt_content: str) -> str:
        """从VTT字幕文件中提取纯文本"""
        lines = vtt_content.split('\n')
        text_lines = []
        skip_header = True
        
        for line in lines:
            line = line.strip()
            # 跳过WebVTT头部
            if skip_header and (line.startswith('WEBVTT') or line.startswith('NOTE') or not line):
                continue
            skip_header = False
            
            if '-->' in line or not line:
                continue
            text_lines.append(line)
        
        return '\n'.join(text_lines)

    async def apply_filters(self):
        """应用搜索和筛选条件"""
        filtered_items = self.transcript_items.copy()
        
        # 应用日期筛选
        filter_value = self.filter_dropdown.value if self.filter_dropdown else "all"
        if filter_value != "all":
            now = datetime.now()
            if filter_value == "today":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                filtered_items = [item for item in filtered_items if item['modified_time'] >= start_date]
            elif filter_value == "week":
                start_date = now - timedelta(days=7)
                filtered_items = [item for item in filtered_items if item['modified_time'] >= start_date]
            elif filter_value == "month":
                start_date = now - timedelta(days=30)
                filtered_items = [item for item in filtered_items if item['modified_time'] >= start_date]
        
        # 应用搜索筛选
        search_term = self.search_field.value.strip() if self.search_field else ""
        if search_term:
            filtered_items = [
                item for item in filtered_items
                if search_term.lower() in item['content'].lower() or 
                   search_term.lower() in item['folder_name'].lower() or
                   search_term.lower() in item['file_name'].lower()
            ]
        
        self.filtered_items = filtered_items
        await self.update_transcript_list()

    async def update_transcript_list(self):
        """更新文案列表显示"""
        try:
            # 确保transcript_list存在且已正确初始化
            if not self.transcript_list or not hasattr(self.transcript_list, 'controls'):
                logger.warning("文案列表组件未正确初始化")
                return
                
            self.transcript_list.controls.clear()
            self.selected_items.clear()
            
            if not self.filtered_items:
                await self.show_empty_state()
                return
            
            for i, item in enumerate(self.filtered_items):
                card = self.create_transcript_card(item, i)
                self.transcript_list.controls.append(card)
            
            # 只有在页面已经渲染且组件已添加到页面时才调用update
            if self.page_initialized and hasattr(self.transcript_list, 'page') and self.transcript_list.page:
                self.transcript_list.update()
        except Exception as e:
            logger.error(f"更新文案列表失败: {e}")
            await self.show_empty_state("加载失败", f"更新列表时出错: {str(e)}")

    async def show_empty_state(self, title="暂无文案内容", description="完成录制并启用语音识别后，这里会显示生成的文案内容"):
        """显示空状态"""
        empty_container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.DESCRIPTION, size=64, color=ft.Colors.GREY_400),
                ft.Text(
                    title,
                    size=20,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.GREY_600,
                    weight=ft.FontWeight.BOLD
                ),
                ft.Text(
                    description,
                    size=14,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.GREY_500
                ),
                ft.Container(height=20),
                ft.ElevatedButton(
                    text="刷新列表",
                    icon=ft.Icons.REFRESH,
                    on_click=self.refresh_transcripts,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_100,
                        color=ft.Colors.BLUE_700,
                    )
                ),
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15),
            height=350,
            alignment=ft.alignment.center
        )
        
        try:
            if self.transcript_list and hasattr(self.transcript_list, 'controls'):
                self.transcript_list.controls = [empty_container]
                # 只有在页面已经渲染且组件已添加到页面时才调用update
                if self.page_initialized and hasattr(self.transcript_list, 'page') and self.transcript_list.page:
                    self.transcript_list.update()
        except Exception as e:
            logger.error(f"显示空状态失败: {e}")

    def create_transcript_card(self, item: Dict, index: int) -> ft.Card:
        """创建增强的文案卡片"""
        # 选择框
        checkbox = ft.Checkbox(
            value=index in self.selected_items,
            on_change=lambda e, idx=index: self.on_item_select(e, idx)
        )
        
        # 文案信息
        title_text = ft.Text(
            f"{item['folder_name']} / {item['file_name']}",
            size=14,
            weight=ft.FontWeight.BOLD,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        
        preview_text = ft.Text(
            item['preview'],
            size=12,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
            color=ft.Colors.GREY_700,
        )
        
        # 文件信息行
        info_row = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.ACCESS_TIME, size=12, color=ft.Colors.GREY_500),
                ft.Text(f"生成: {item['modified_time'].strftime('%Y-%m-%d %H:%M')}", size=10, color=ft.Colors.GREY_600),
            ], spacing=3, tight=True),
            ft.Row([
                ft.Icon(ft.Icons.TEXT_FIELDS, size=12, color=ft.Colors.GREY_500),
                ft.Text(f"{item['word_count']} 字", size=10, color=ft.Colors.GREY_600),
            ], spacing=3, tight=True),
            ft.Row([
                ft.Icon(ft.Icons.STORAGE, size=12, color=ft.Colors.GREY_500),
                ft.Text(f"{item['file_size'] / 1024:.1f} KB", size=10, color=ft.Colors.GREY_600),
            ], spacing=3, tight=True),
        ], spacing=15)
        
        # 操作按钮
        actions = ft.Row([
            ft.IconButton(
                icon=ft.Icons.VISIBILITY,
                tooltip="查看完整内容",
                on_click=lambda e, item=item: self.view_full_transcript(e, item),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE_100,
                    color=ft.Colors.BLUE_700,
                    shape=ft.CircleBorder(),
                )
            ),
            ft.IconButton(
                icon=ft.Icons.COPY,
                tooltip="复制文案",
                on_click=lambda e, item=item: self.copy_transcript(e, item),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_100,
                    color=ft.Colors.GREEN_700,
                    shape=ft.CircleBorder(),
                )
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                tooltip="删除文案",
                on_click=lambda e, item=item, idx=index: self.delete_transcript(e, item, idx),
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.RED_100,
                    color=ft.Colors.RED_700,
                    shape=ft.CircleBorder(),
                )
            ),
        ], spacing=5, tight=True)
        
        # 卡片内容
        card_content = ft.Container(
            content=ft.Row([
                checkbox,
                ft.Column([
                    title_text,
                    preview_text,
                    info_row,
                ], expand=True, spacing=5),
                actions,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=15,
            border_radius=8,
        )
        
        return ft.Card(
            content=card_content, 
            elevation=2,
            surface_tint_color=ft.Colors.BLUE_50
        )

    async def on_search_change(self, e):
        """搜索内容变化"""
        await self.apply_filters()

    async def on_filter_change(self, e):
        """筛选条件变化"""
        await self.apply_filters()

    def on_item_select(self, e, index: int):
        """选择项目"""
        if e.data == "true":
            self.selected_items.add(index)
        else:
            self.selected_items.discard(index)

    async def select_all_items(self, e):
        """全选"""
        self.selected_items = set(range(len(self.filtered_items)))
        await self.update_transcript_list()

    async def clear_selection(self, e):
        """清空选择"""
        self.selected_items.clear()
        await self.update_transcript_list()

    async def view_full_transcript(self, e, item: Dict):
        """查看完整文案"""
        try:
            # 创建一个临时的recording对象，包含所有必要的属性
            class TempRecording:
                def __init__(self, item):
                    self.title = item['folder_name']
                    self.recording_dir = os.path.dirname(item['file_path'])
                    # 添加文案对话框需要的其他属性
                    self.rec_id = f"temp_{item['file_name']}"
                    self.url = ""
                    self.streamer_name = item['folder_name']
                    self.quality = "OD"
                    self.record_format = "ts"
                    self.status_info = "stopped"
            
            temp_recording = TempRecording(item)
            
            # 使用TranscriptDialog显示文案
            dialog = TranscriptDialog(self.app, temp_recording)
            dialog.open = True
            self.app.dialog_area.content = dialog
            self.app.page.update()
            
        except Exception as ex:
            logger.error(f"查看文案失败: {ex}")
            await self.app.snack_bar.show_snack_bar(f"查看文案失败: {str(ex)}", bgcolor=ft.Colors.RED)

    async def copy_transcript(self, e, item: Dict):
        """复制文案"""
        try:
            # 使用同步剪贴板API
            self.app.page.set_clipboard(item['content'])
            await self.app.snack_bar.show_snack_bar("文案已复制到剪贴板", bgcolor=ft.Colors.GREEN)
        except Exception as ex:
            logger.error(f"复制文案失败: {ex}")
            await self.app.snack_bar.show_snack_bar("复制失败")

    async def delete_transcript(self, e, item: Dict, index: int):
        """删除单个文案"""
        async def confirm_delete(e):
            try:
                os.remove(item['file_path'])
                self.transcript_items = [t for t in self.transcript_items if t['file_path'] != item['file_path']]
                self.update_stats()
                await self.apply_filters()
                await self.app.snack_bar.show_snack_bar("文案已删除", bgcolor=ft.Colors.GREEN)
            except Exception as ex:
                logger.error(f"删除文案失败: {ex}")
                await self.app.snack_bar.show_snack_bar("删除失败")
            dialog.open = False
            self.app.page.update()

        async def cancel_delete(e):
            dialog.open = False
            self.app.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text(f"确定要删除文案文件「{item['file_name']}」吗？\n此操作无法撤销。"),
            actions=[
                ft.TextButton("取消", on_click=cancel_delete),
                ft.TextButton("删除", on_click=confirm_delete),
            ],
            modal=True,
        )
        
        dialog.open = True
        self.app.dialog_area.content = dialog
        self.app.page.update()

    async def batch_delete_transcripts(self, e):
        """批量删除文案"""
        if not self.selected_items:
            await self.app.snack_bar.show_snack_bar("请先选择要删除的文案")
            return

        async def confirm_batch_delete(e):
            try:
                deleted_count = 0
                selected_items = [self.filtered_items[i] for i in self.selected_items]
                
                for item in selected_items:
                    try:
                        os.remove(item['file_path'])
                        self.transcript_items = [t for t in self.transcript_items if t['file_path'] != item['file_path']]
                        deleted_count += 1
                    except Exception as ex:
                        logger.error(f"删除文案失败 {item['file_path']}: {ex}")
                
                self.selected_items.clear()
                self.update_stats()
                await self.apply_filters()
                await self.app.snack_bar.show_snack_bar(f"已删除 {deleted_count} 个文案", bgcolor=ft.Colors.GREEN)
                
            except Exception as ex:
                logger.error(f"批量删除失败: {ex}")
                await self.app.snack_bar.show_snack_bar("批量删除失败")
            
            dialog.open = False
            self.app.page.update()

        async def cancel_batch_delete(e):
            dialog.open = False
            self.app.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("确认批量删除"),
            content=ft.Text(f"确定要删除选中的 {len(self.selected_items)} 个文案吗？\n此操作无法撤销。"),
            actions=[
                ft.TextButton("取消", on_click=cancel_batch_delete),
                ft.TextButton("删除", on_click=confirm_batch_delete),
            ],
            modal=True,
        )
        
        dialog.open = True
        self.app.dialog_area.content = dialog
        self.app.page.update()

    async def export_all_transcripts(self, e):
        """导出所有文案"""
        if not self.transcript_items:
            await self.app.snack_bar.show_snack_bar("暂无文案可导出")
            return

        try:
            # 合并所有文案内容
            all_content = []
            for item in self.transcript_items:
                all_content.append(f"# {item['folder_name']} / {item['file_name']}")
                all_content.append(f"生成时间: {item['modified_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                all_content.append(f"字数: {item['word_count']}")
                all_content.append("")
                all_content.append(item['content'])
                all_content.append("")
                all_content.append("-" * 50)
                all_content.append("")

            combined_content = "\n".join(all_content)

            if hasattr(self.app, 'is_web') and self.app.is_web:
                # Web端复制到剪贴板
                self.app.page.set_clipboard(combined_content)
                await self.app.snack_bar.show_snack_bar("所有文案内容已复制，您可以粘贴到文档中保存", bgcolor=ft.Colors.BLUE)
            else:
                # 桌面端保存到文件
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    
                    def save_file():
                        try:
                            root = tk.Tk()
                            root.withdraw()
                            
                            filename = filedialog.asksaveasfilename(
                                defaultextension=".txt",
                                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                                initialname="所有文案内容.txt"
                            )
                            
                            if filename:
                                with open(filename, 'w', encoding='utf-8') as f:
                                    f.write(combined_content)
                                return filename
                            root.destroy()
                            return None
                        except Exception as ex:
                            logger.error(f"保存文件错误: {ex}")
                            return "error"
                    
                    # 在后台线程执行文件对话框
                    result = await asyncio.get_event_loop().run_in_executor(None, save_file)
                    
                    if result == "error":
                        await self.app.snack_bar.show_snack_bar("导出失败", bgcolor=ft.Colors.RED)
                    elif result:
                        await self.app.snack_bar.show_snack_bar(f"文案已导出到: {result}", bgcolor=ft.Colors.GREEN)
                    
                except Exception as desktop_error:
                    logger.error(f"桌面端导出失败: {desktop_error}")
                    # 备用方案：复制到剪贴板
                    self.app.page.set_clipboard(combined_content)
                    await self.app.snack_bar.show_snack_bar("文案已复制到剪贴板（导出失败）", bgcolor=ft.Colors.ORANGE)

        except Exception as ex:
            logger.error(f"导出文案失败: {ex}")
            await self.app.snack_bar.show_snack_bar("导出失败")

    async def refresh_transcripts(self, e):
        """刷新文案列表"""
        # 显示加载状态
        self.show_loading_state()
        
        # 重新加载数据
        await self.load_transcripts()
        
        await self.app.snack_bar.show_snack_bar("文案列表已刷新", bgcolor=ft.Colors.GREEN) 