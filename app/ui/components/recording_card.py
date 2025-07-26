import asyncio
import os.path
from functools import partial

import flet as ft

from ...models.recording_model import Recording
from ...models.recording_status_model import RecordingStatus
from ...utils import utils
from ...utils.logger import logger
from ..views.storage_view import StoragePage
from .card_dialog import CardDialog
from .recording_dialog import RecordingDialog
from .video_player import VideoPlayer
from .transcript_dialog import TranscriptDialog


class RecordingCardManager:
    def __init__(self, app):
        self.app = app
        self.cards_obj = {}
        self.update_duration_tasks = {}
        self.selected_cards = {}
        self.app.language_manager.add_observer(self)
        self._ = {}
        self.load()
        self.pubsub_subscribe()

    def load(self):
        language = self.app.language_manager.language
        for key in ("recording_card", "recording_manager", "base", "home_page", "video_quality", "storage_page"):
            self._.update(language.get(key, {}))

    def pubsub_subscribe(self):
        self.app.page.pubsub.subscribe_topic("update", self.subscribe_update_card)
        self.app.page.pubsub.subscribe_topic("delete", self.subscribe_remove_cards)

    async def create_card(self, recording: Recording, layout_mode: str = "auto"):
        """Create a card for a given recording."""
        rec_id = recording.rec_id
        if not self.cards_obj.get(rec_id):
            if self.app.recording_enabled:
                self.app.page.run_task(self.app.record_manager.check_if_live, recording)
            else:
                recording.status_info = RecordingStatus.NOT_RECORDING_SPACE
        card_data = self._create_card_components(recording, layout_mode)
        self.cards_obj[rec_id] = card_data
        self.start_update_task(recording)
        return card_data["card"]

    def _create_card_components(self, recording: Recording, layout_mode: str = "auto"):
        """create card components."""
        # 创建主要操作按钮（高亮显示）
        record_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(self.get_icon_for_recording_state(recording), size=16),
                ft.Text(self.get_text_for_recording_state(recording), size=12)
            ], spacing=5, tight=True),
            tooltip=self.get_tip_for_recording_state(recording),
            on_click=partial(self.recording_button_on_click, recording=recording),
            bgcolor=self.get_recording_button_color(recording),
            color=ft.Colors.WHITE,
            height=35,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=2,
            )
        )

        monitor_button = ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(self.get_icon_for_monitor_state(recording), size=16),
                ft.Text(self.get_text_for_monitor_state(recording), size=12)
            ], spacing=5, tight=True),
            tooltip=self.get_tip_for_monitor_state(recording),
            on_click=partial(self.monitor_button_on_click, recording=recording),
            bgcolor=self.get_monitor_button_color(recording),
            color=ft.Colors.WHITE,
            height=35,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                elevation=2,
            )
        )

        # 创建功能按钮组
        # 根据布局模式决定按钮大小
        if layout_mode == "grid" or (layout_mode == "auto" and self.app.current_page.is_grid_view):
            icon_size = 14  # 减小图标以适应6个按钮一行显示
            button_padding = ft.Padding(4, 4, 4, 4)  # 减小内边距
        else:
            icon_size = 18
            button_padding = ft.Padding(8, 8, 8, 8)
        
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            tooltip=self._["edit_record_config"],
            on_click=partial(self.edit_recording_button_click, recording=recording),
            icon_size=icon_size,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_GREY_100,
                color=ft.Colors.BLUE_GREY_700,
                shape=ft.CircleBorder(),
                padding=button_padding,
            )
        )

        preview_button = ft.IconButton(
            icon=ft.Icons.PLAY_CIRCLE_OUTLINE,
            tooltip=self._["preview_video"],
            on_click=partial(self.preview_video_button_on_click, recording=recording),
            icon_size=icon_size,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.PURPLE_100,
                color=ft.Colors.PURPLE_700,
                shape=ft.CircleBorder(),
                padding=button_padding,
            )
        )

        open_folder_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OUTLINED,
            tooltip=self._["open_folder"],
            on_click=partial(self.recording_dir_button_on_click, recording=recording),
            icon_size=icon_size,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.ORANGE_100,
                color=ft.Colors.ORANGE_700,
                shape=ft.CircleBorder(),
                padding=button_padding,
            )
        )
        
        recording_info_button = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip=self._["recording_info"],
            on_click=partial(self.recording_info_button_on_click, recording=recording),
            icon_size=icon_size,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL_100,
                color=ft.Colors.TEAL_700,
                shape=ft.CircleBorder(),
                padding=button_padding,
            )
        )
        
        transcript_button = ft.IconButton(
            icon=ft.Icons.SUBTITLES_OUTLINED,
            tooltip=self._["view_transcript"],
            on_click=partial(self.transcript_button_on_click, recording=recording),
            icon_size=icon_size,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.INDIGO_100,
                color=ft.Colors.INDIGO_700,
                shape=ft.CircleBorder(),
                padding=button_padding,
            )
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip=self._["delete_monitor"],
            on_click=partial(self.recording_delete_button_click, recording=recording),
            icon_size=icon_size,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_100,
                color=ft.Colors.RED_700,
                shape=ft.CircleBorder(),
                padding=button_padding,
            )
        )

        # 主播信息区域
        status_prefix = ""
        if not recording.monitor_status:
            status_prefix = f"[{self._['monitor_stopped']}] "
        
        display_title = f"{status_prefix}{recording.title}"
        display_title_label = ft.Text(
            display_title, 
            size=16, 
            selectable=True, 
            max_lines=2, 
            overflow=ft.TextOverflow.ELLIPSIS,
            weight=ft.FontWeight.BOLD if recording.recording or recording.is_live else ft.FontWeight.W_500,
            color=ft.Colors.GREY_800,
        )

        # 平台和质量信息
        platform_info = self.extract_platform_from_url(recording.url)
        quality_info = self._.get(recording.quality, recording.quality)
        
        # 平台芯片
        platform_chip = ft.Container(
            content=ft.Row([
                ft.Icon(self.get_platform_icon(platform_info), size=12, color=ft.Colors.WHITE),
                ft.Text(platform_info, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ], spacing=3, tight=True),
            bgcolor=self.get_platform_color(platform_info),
            border_radius=10,
            padding=ft.Padding(8, 3, 8, 3),
        )
        
        # 质量芯片
        quality_chip = ft.Container(
            content=ft.Text(quality_info, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_600,
            border_radius=10,
            padding=ft.Padding(8, 3, 8, 3),
        )
        
        # 录制格式芯片
        format_chip = ft.Container(
            content=ft.Text(recording.record_format, size=9, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700),
            bgcolor=ft.Colors.GREY_200,
            border_radius=8,
            padding=ft.Padding(6, 2, 6, 2),
        )
        
        info_chips = ft.Row([
            platform_chip,
            quality_chip,
            format_chip,
        ], spacing=5, tight=True)

        # 状态和统计信息
        duration_text = self.app.record_manager.get_duration(recording)
        speed_text = recording.speed
        created_time, last_record_time = self.get_recording_time_info(recording)
        
        # 第一行：时长和速度
        stats_row1 = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.TIMER, size=14, color=ft.Colors.GREY_600),
                ft.Text(self.format_duration_text(duration_text), size=12, color=ft.Colors.GREY_700)
            ], spacing=3, tight=True),
            ft.Row([
                ft.Icon(ft.Icons.SPEED, size=14, color=ft.Colors.GREY_600),
                ft.Text(self.get_speed_display(speed_text), size=12, color=ft.Colors.GREY_700)
            ], spacing=3, tight=True),
        ], spacing=15, tight=True)
        
        # 第二行：时间信息
        stats_row2 = ft.Row([
            ft.Row([
                ft.Icon(ft.Icons.ADD_CIRCLE_OUTLINE, size=12, color=ft.Colors.GREY_500),
                ft.Text(f"添加: {created_time}", size=10, color=ft.Colors.GREY_600)
            ], spacing=3, tight=True),
            ft.Row([
                ft.Icon(ft.Icons.RADIO_BUTTON_CHECKED, size=12, color=ft.Colors.GREY_500),
                ft.Text(f"录制: {last_record_time}", size=10, color=ft.Colors.GREY_600)
            ], spacing=3, tight=True),
        ], spacing=15, tight=True)

        # 状态标签
        status_label = self.create_enhanced_status_label(recording)

        # 头部区域（标题 + 状态）
        header_row = ft.Row([
            ft.Column([
                display_title_label,
                info_chips,
            ], spacing=5, tight=True, expand=True),
            status_label if status_label else ft.Container(width=0),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, tight=True)

        # 根据布局模式决定按钮排列方式
        if layout_mode == "grid" or (layout_mode == "auto" and self.app.current_page.is_grid_view):
            # 网格模式：紧凑布局，所有功能按钮放在一行
            main_actions = ft.Row([
                record_button,
                monitor_button,
            ], spacing=8, tight=True, alignment=ft.MainAxisAlignment.START)

            # 网格模式下所有功能按钮放在一行，使用更小的间距
            all_function_actions = ft.Row([
                open_folder_button,
                recording_info_button,
                transcript_button,
                preview_button,
                edit_button,
                delete_button,
            ], spacing=2, tight=True, alignment=ft.MainAxisAlignment.START)

            # 紧凑的网格布局
            card_content = ft.Column([
                header_row,
                ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                stats_row1,
                stats_row2,
                ft.Container(height=2),
                main_actions,
                ft.Container(height=2),
                all_function_actions,
            ], spacing=3, tight=True)
            
        else:
            # 列表模式：横向展开布局
            main_actions = ft.Row([
                record_button,
                monitor_button,
            ], spacing=12, tight=True, alignment=ft.MainAxisAlignment.START)

            # 列表模式下所有功能按钮放在一行
            all_function_actions = ft.Row([
                open_folder_button,
                recording_info_button,  
                transcript_button,
                ft.VerticalDivider(width=1),
                preview_button,
                edit_button,
                delete_button,
            ], spacing=6, tight=True, alignment=ft.MainAxisAlignment.START)

            # 宽松的列表布局
            card_content = ft.Column([
                header_row,
                ft.Divider(height=1, thickness=1, color=ft.Colors.GREY_300),
                ft.Row([
                    ft.Column([
                        stats_row1,
                        stats_row2,
                    ], spacing=3, tight=True, expand=True),
                    main_actions,
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=3),
                all_function_actions,
            ], spacing=6, tight=True)

        # 根据布局模式调整容器属性
        if layout_mode == "grid" or (layout_mode == "auto" and self.app.current_page.is_grid_view):
            # 网格模式：紧凑内边距
            container_padding = ft.Padding(12, 10, 12, 10)
        else:
            # 列表模式：宽松内边距
            container_padding = ft.Padding(16, 14, 16, 14)
        
        card_container = ft.Container(
            content=card_content,
            padding=container_padding,
            on_click=partial(self.recording_card_on_click, recording=recording),
            bgcolor=self.get_enhanced_card_background_color(recording),
            border_radius=12,
            border=ft.border.all(1.5, self.get_enhanced_card_border_color(recording)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )
        
        card = ft.Card(
            key=str(recording.rec_id), 
            content=card_container,
            elevation=0,  # 使用容器的阴影而不是卡片阴影
        )

        # 构建返回字典，处理不同布局模式
        result = {
            "card": card,
            "display_title_label": display_title_label,
            "duration_label": stats_row1.controls[0].controls[1],  # duration text
            "speed_label": stats_row1.controls[1].controls[1],     # speed text
            "created_time_label": stats_row2.controls[0].controls[1],  # created time text
            "last_record_label": stats_row2.controls[1].controls[1],   # last record time text
            "record_button": record_button,
            "open_folder_button": open_folder_button,
            "recording_info_button": recording_info_button,
            "transcript_button": transcript_button,
            "edit_button": edit_button,
            "monitor_button": monitor_button,
            "preview_button": preview_button,
            "delete_button": delete_button,
            "status_label": status_label,
            "layout_mode": layout_mode,
        }
        
        # 根据布局模式添加不同的功能按钮引用
        result.update({
            "all_function_actions": all_function_actions,
        })
        
        return result
        
    def get_card_background_color(self, recording: Recording):
        is_dark_mode = self.app.page.theme_mode == ft.ThemeMode.DARK
        if recording.selected:
            return ft.Colors.GREY_800 if is_dark_mode else ft.Colors.GREY_400
        return None

    @staticmethod
    def get_card_border_color(recording: Recording):
        """Get the border color of the card."""
        if recording.recording:
            return ft.Colors.GREEN
        elif recording.status_info == RecordingStatus.RECORDING_ERROR:
            return ft.Colors.RED
        elif not recording.is_live and recording.monitor_status:
            return ft.Colors.AMBER
        elif not recording.monitor_status:
            return ft.Colors.GREY
        return ft.Colors.TRANSPARENT

    def get_enhanced_card_background_color(self, recording: Recording):
        """获取增强卡片的背景颜色"""
        is_dark_mode = self.app.page.theme_mode == ft.ThemeMode.DARK
        
        if recording.selected:
            return ft.Colors.BLUE_50 if not is_dark_mode else ft.Colors.BLUE_GREY_800
        elif recording.recording:
            return ft.Colors.GREEN_50 if not is_dark_mode else ft.Colors.GREEN_900
        elif recording.status_info == RecordingStatus.RECORDING_ERROR:
            return ft.Colors.RED_50 if not is_dark_mode else ft.Colors.RED_900
        else:
            return ft.Colors.WHITE if not is_dark_mode else ft.Colors.GREY_850

    def get_enhanced_card_border_color(self, recording: Recording):
        """获取增强卡片的边框颜色"""
        if recording.recording:
            return ft.Colors.GREEN_400
        elif recording.status_info == RecordingStatus.RECORDING_ERROR:
            return ft.Colors.RED_400
        elif not recording.is_live and recording.monitor_status:
            return ft.Colors.ORANGE_400
        elif recording.selected:
            return ft.Colors.BLUE_400
        else:
            return ft.Colors.GREY_200

    def get_text_for_recording_state(self, recording: Recording):
        """获取录制状态按钮的文本"""
        if recording.recording:
            return self._["stop_recording"]
        else:
            return self._["start_recording"]

    def get_recording_button_color(self, recording: Recording):
        """获取录制按钮的颜色"""
        if recording.recording:
            return ft.Colors.RED_600
        else:
            return ft.Colors.GREEN_600

    def get_text_for_monitor_state(self, recording: Recording):
        """获取监控状态按钮的文本"""
        if recording.monitor_status:
            return self._["stop_monitoring"]
        else:
            return self._["start_monitoring"]

    def get_monitor_button_color(self, recording: Recording):
        """获取监控按钮的颜色"""
        if recording.monitor_status:
            return ft.Colors.ORANGE_600
        else:
            return ft.Colors.BLUE_600

    def extract_platform_from_url(self, url: str) -> str:
        """从URL中提取平台信息"""
        if not url:
            return "未知"
        
        url_lower = url.lower()
        if "douyin" in url_lower or "tiktok" in url_lower:
            return "抖音"
        elif "bilibili" in url_lower or "b23.tv" in url_lower:
            return "B站"
        elif "youtube" in url_lower or "youtu.be" in url_lower:
            return "YouTube"
        elif "twitch" in url_lower:
            return "Twitch"
        elif "huya" in url_lower:
            return "虎牙"
        elif "douyu" in url_lower:
            return "斗鱼"
        elif "kuaishou" in url_lower:
            return "快手"
        elif "xiaohongshu" in url_lower or "xhs" in url_lower:
            return "小红书"
        elif "weibo" in url_lower:
            return "微博"
        elif "yy" in url_lower:
            return "YY"
        elif "bigo" in url_lower:
            return "BIGO"
        elif "inke" in url_lower:
            return "映客"
        else:
            return "其他"

    def get_platform_color(self, platform: str) -> str:
        """获取平台对应的颜色"""
        platform_colors = {
            "抖音": ft.Colors.BLACK,
            "B站": ft.Colors.PINK,
            "YouTube": ft.Colors.RED,
            "Twitch": ft.Colors.PURPLE,
            "虎牙": ft.Colors.ORANGE,
            "斗鱼": ft.Colors.BLUE,
            "快手": ft.Colors.YELLOW_800,
            "小红书": ft.Colors.RED_300,
            "微博": ft.Colors.ORANGE_600,
            "YY": ft.Colors.GREEN,
            "BIGO": ft.Colors.BLUE_400,
            "映客": ft.Colors.PURPLE_300,
        }
        return platform_colors.get(platform, ft.Colors.GREY_600)

    def get_platform_icon(self, platform: str) -> str:
        """获取平台对应的图标"""
        platform_icons = {
            "抖音": ft.Icons.MUSIC_NOTE,
            "B站": ft.Icons.PLAY_CIRCLE,
            "YouTube": ft.Icons.PLAY_ARROW,
            "Twitch": ft.Icons.VIDEOGAME_ASSET,
            "虎牙": ft.Icons.SPORTS_ESPORTS,
            "斗鱼": ft.Icons.GAMEPAD,
            "快手": ft.Icons.FLASH_ON,
            "小红书": ft.Icons.FAVORITE,
            "微博": ft.Icons.CHAT_BUBBLE,
            "YY": ft.Icons.MIC,
            "BIGO": ft.Icons.VIDEO_CALL,
            "映客": ft.Icons.CAMERA_ALT,
        }
        return platform_icons.get(platform, ft.Icons.LANGUAGE)

    def format_duration_text(self, duration_text: str) -> str:
        """格式化时长文本"""
        if not duration_text or duration_text in ["未开始", "等待中"]:
            return "未开始"
        
        # 如果已经是格式化的文本，直接返回
        if any(unit in duration_text for unit in ["分钟", "秒", "小时"]):
            return duration_text
        
        try:
            # 尝试解析秒数
            seconds = int(float(duration_text))
            if seconds < 60:
                return f"{seconds}秒"
            elif seconds < 3600:
                minutes = seconds // 60
                secs = seconds % 60
                return f"{minutes}分钟{secs}秒" if secs > 0 else f"{minutes}分钟"
            else:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                if minutes > 0:
                    return f"{hours}小时{minutes}分钟"
                else:
                    return f"{hours}小时"
        except (ValueError, TypeError):
            return duration_text

    def get_speed_display(self, speed_text: str) -> str:
        """格式化速度显示"""
        if not speed_text or speed_text in ["等待中", "未开始", "0", ""]:
            return "等待中"
        
        try:
            # 尝试解析为数字 (KB/s)
            speed_kb = float(speed_text.replace("KB/s", "").replace("MB/s", "").strip())
            
            if "MB/s" in speed_text:
                return f"{speed_kb:.1f}MB/s"
            elif speed_kb >= 1024:
                speed_mb = speed_kb / 1024
                return f"{speed_mb:.1f}MB/s"
            else:
                return f"{speed_kb:.0f}KB/s"
        except (ValueError, TypeError):
            return speed_text if speed_text else "等待中"



    def get_recording_time_info(self, recording: Recording) -> tuple:
        """获取录制时间信息"""
        import datetime
        
        # 获取创建时间
        created_time = "未知"
        if hasattr(recording, 'created_at') and recording.created_at:
            try:
                if isinstance(recording.created_at, str):
                    created_dt = datetime.datetime.fromisoformat(recording.created_at)
                else:
                    created_dt = recording.created_at
                created_time = created_dt.strftime("%m-%d %H:%M")
            except:
                created_time = "未知"
        
        # 获取最后录制时间
        last_record_time = "从未录制"
        if recording.recording_dir and os.path.exists(recording.recording_dir):
            try:
                # 查找最新的视频文件
                video_files = []
                for root, _, files in os.walk(recording.recording_dir):
                    for file in files:
                        if file.endswith(('.mp4', '.flv', '.ts', '.mkv', '.avi')):
                            video_files.append(os.path.join(root, file))
                
                if video_files:
                    # 按修改时间排序，获取最新的
                    latest_file = max(video_files, key=os.path.getmtime)
                    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(latest_file))
                    last_record_time = last_modified.strftime("%m-%d %H:%M")
            except:
                last_record_time = "未知"
        
        return created_time, last_record_time

    def create_enhanced_status_label(self, recording: Recording):
        """创建增强的状态标签"""
        if recording.recording:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=12, color=ft.Colors.WHITE),
                    ft.Text(self._["status_recording"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.RED_600,
                border_radius=20,
                padding=ft.Padding(10, 5, 10, 5),
            )
        elif recording.status_info == RecordingStatus.RECORDING_ERROR:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.ERROR, size=12, color=ft.Colors.WHITE),
                    ft.Text(self._["status_error"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.RED_600,
                border_radius=20,
                padding=ft.Padding(10, 5, 10, 5),
            )
        elif recording.is_live and recording.monitor_status:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.LIVE_TV, size=12, color=ft.Colors.WHITE),
                    ft.Text(self._["status_live"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.GREEN_600,
                border_radius=20,
                padding=ft.Padding(10, 5, 10, 5),
            )
        elif not recording.is_live and recording.monitor_status:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.VISIBILITY, size=12, color=ft.Colors.BLACK),
                    ft.Text(self._["status_monitoring"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.ORANGE_400,
                border_radius=20,
                padding=ft.Padding(10, 5, 10, 5),
            )
        elif not recording.monitor_status:
            return ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.PAUSE, size=12, color=ft.Colors.WHITE),
                    ft.Text(self._["status_stopped"], size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ], spacing=3, tight=True),
                bgcolor=ft.Colors.GREY_600,
                border_radius=20,
                padding=ft.Padding(10, 5, 10, 5),
            )
        return None

    def create_status_label(self, recording: Recording):
        if recording.recording:
            return ft.Container(
                content=ft.Text(self._["recording"], color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.GREEN,
                border_radius=5,
                padding=5,
                width=60,
                height=26,
                alignment=ft.alignment.center,
            )
        elif recording.status_info == RecordingStatus.RECORDING_ERROR:
            return ft.Container(
                content=ft.Text(self._["recording_error"], color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.RED,
                border_radius=5,
                padding=5,
                width=60,
                height=26,
                alignment=ft.alignment.center,
            )
        elif not recording.is_live and recording.monitor_status:
            return ft.Container(
                content=ft.Text(self._["offline"], color=ft.Colors.BLACK, size=12, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.AMBER,
                border_radius=5,
                padding=5,
                width=60,
                height=26,
                alignment=ft.alignment.center,
            )
        elif not recording.monitor_status:
            return ft.Container(
                content=ft.Text(self._["no_monitor"], color=ft.Colors.WHITE, size=12, weight=ft.FontWeight.BOLD),
                bgcolor=ft.Colors.GREY,
                border_radius=5,
                padding=5,
                width=60,
                height=26,
                alignment=ft.alignment.center,
            )
        return None

    async def update_card(self, recording):
        """Update only the recordings cards in the scrollable content area."""
        if recording.rec_id in self.cards_obj:
            try:
                recording_card = self.cards_obj[recording.rec_id]
                
                # 更新标题
                status_prefix = ""
                if not recording.monitor_status:
                    status_prefix = f"[{self._['monitor_stopped']}] "
                
                display_title = f"{status_prefix}{recording.title}"
                if recording_card.get("display_title_label"):
                    recording_card["display_title_label"].value = display_title
                    title_label_weight = ft.FontWeight.BOLD if recording.recording or recording.is_live else ft.FontWeight.W_500
                    recording_card["display_title_label"].weight = title_label_weight
                
                # 更新状态标签
                new_status_label = self.create_enhanced_status_label(recording)
                if recording_card["card"] and recording_card["card"].content and recording_card["card"].content.content:
                    header_row = recording_card["card"].content.content.controls[0]  # 头部行
                    if len(header_row.controls) > 1 and new_status_label:
                        header_row.controls[1] = new_status_label
                    elif new_status_label and len(header_row.controls) == 1:
                        header_row.controls.append(new_status_label)
                    elif not new_status_label and len(header_row.controls) > 1:
                        header_row.controls[1] = ft.Container(width=0)
                
                recording_card["status_label"] = new_status_label
                
                # 更新时长和速度
                if recording_card.get("duration_label"):
                    duration_text = self.app.record_manager.get_duration(recording)
                    recording_card["duration_label"].value = self.format_duration_text(duration_text)
                
                if recording_card.get("speed_label"):
                    recording_card["speed_label"].value = self.get_speed_display(recording.speed)
                
                # 更新时间信息
                if recording_card.get("created_time_label") and recording_card.get("last_record_label"):
                    created_time, last_record_time = self.get_recording_time_info(recording)
                    recording_card["created_time_label"].value = f"添加: {created_time}"
                    recording_card["last_record_label"].value = f"录制: {last_record_time}"
                
                # 更新录制按钮
                if recording_card.get("record_button"):
                    # 更新按钮图标和文本
                    button_content = recording_card["record_button"].content
                    if button_content and hasattr(button_content, 'controls'):
                        button_content.controls[0].name = self.get_icon_for_recording_state(recording)  # 图标
                        button_content.controls[1].value = self.get_text_for_recording_state(recording)  # 文本
                    
                    recording_card["record_button"].tooltip = self.get_tip_for_recording_state(recording)
                    recording_card["record_button"].bgcolor = self.get_recording_button_color(recording)
                
                # 更新监控按钮
                if recording_card.get("monitor_button"):
                    # 更新按钮图标和文本
                    button_content = recording_card["monitor_button"].content
                    if button_content and hasattr(button_content, 'controls'):
                        button_content.controls[0].name = self.get_icon_for_monitor_state(recording)  # 图标
                        button_content.controls[1].value = self.get_text_for_monitor_state(recording)  # 文本
                    
                    recording_card["monitor_button"].tooltip = self.get_tip_for_monitor_state(recording)
                    recording_card["monitor_button"].bgcolor = self.get_monitor_button_color(recording)
                
                # 更新卡片容器样式
                if recording_card["card"] and recording_card["card"].content:
                    recording_card["card"].content.bgcolor = self.get_enhanced_card_background_color(recording)
                    recording_card["card"].content.border = ft.border.all(1, self.get_enhanced_card_border_color(recording))
                    recording_card["card"].update()
            except Exception as e:
                logger.error(f"Error updating card: {e}")

    async def update_monitor_state(self, recording: Recording):
        """Update the monitor button state based on the current monitoring status."""
        if recording.monitor_status:
            recording.update(
                {
                    "recording": False,
                    "monitor_status": not recording.monitor_status,
                    "status_info": RecordingStatus.STOPPED_MONITORING,
                    "display_title": f"[{self._['monitor_stopped']}] {recording.title}",
                }
            )
            self.app.record_manager.stop_recording(recording)
            self.app.page.run_task(self.app.snack_bar.show_snack_bar, self._["stop_monitor_tip"])
        else:
            recording.update(
                {
                    "monitor_status": not recording.monitor_status,
                    "status_info": RecordingStatus.MONITORING,
                    "display_title": f"{recording.title}",
                }
            )
            self.app.page.run_task(self.app.record_manager.check_if_live, recording)
            self.app.page.run_task(self.app.snack_bar.show_snack_bar, self._["start_monitor_tip"], ft.Colors.GREEN)

        await self.update_card(recording)
        self.app.page.pubsub.send_others_on_topic("update", recording)
        self.app.page.run_task(self.app.record_manager.persist_recordings)

    async def show_recording_info_dialog(self, recording: Recording):
        """Display a dialog with detailed information about the recording."""
        dialog = CardDialog(self.app, recording)
        dialog.open = True
        self.app.dialog_area.content = dialog
        self.app.page.update()
    
    async def show_transcript_dialog(self, recording: Recording):
        """Display a dialog with transcript content for the recording."""
        try:
            logger.info(f"正在打开文案对话框: {recording.title}")
            dialog = TranscriptDialog(self.app, recording)
            dialog.open = True
            self.app.dialog_area.content = dialog
            self.app.page.update()
            logger.info("文案对话框已显示")
        except Exception as e:
            logger.error(f"显示文案对话框失败: {e}")
            await self.app.snack_bar.show_snack_bar(f"显示文案对话框失败: {e}")

    async def edit_recording_callback(self, recording_list: list[dict]):
        recording_dict = recording_list[0]
        rec_id = recording_dict["rec_id"]
        recording = self.app.record_manager.find_recording_by_id(rec_id)

        await self.app.record_manager.update_recording_card(recording, updated_info=recording_dict)
        if not recording_dict["monitor_status"]:
            recording.display_title = f"[{self._['monitor_stopped']}] " + recording.title

        recording.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
            recording.scheduled_start_time, recording.monitor_hours)

        await self.update_card(recording)
        self.app.page.pubsub.send_others_on_topic("update", recording_dict)

    async def on_toggle_recording(self, recording: Recording):
        """Toggle the recording state for a specific recording."""
        if recording and self.app.recording_enabled:
            if recording.recording:
                self.app.record_manager.stop_recording(recording)
                await self.app.snack_bar.show_snack_bar(self._["stop_record_tip"])
            else:
                if recording.monitor_status:
                    await self.app.record_manager.check_if_live(recording)
                    if recording.is_live:
                        self.app.record_manager.start_update(recording)
                        await self.app.snack_bar.show_snack_bar(self._["pre_record_tip"], bgcolor=ft.Colors.GREEN)
                    else:
                        await self.app.snack_bar.show_snack_bar(self._["is_not_live_tip"])
                else:
                    await self.app.snack_bar.show_snack_bar(self._["please_start_monitor_tip"])

            await self.update_card(recording)
            self.app.page.pubsub.send_others_on_topic("update", recording)

    async def on_delete_recording(self, recording: Recording):
        """Delete a recording from the list and update UI."""
        if recording:
            if recording.recording:
                await self.app.snack_bar.show_snack_bar(self._["please_stop_monitor_tip"])
                return
            await self.app.record_manager.delete_recording_cards([recording])
            await self.app.snack_bar.show_snack_bar(
                self._["delete_recording_success_tip"], bgcolor=ft.Colors.GREEN, duration=2000
            )

    async def remove_recording_card(self, recordings: list[Recording]):
        home_page = self.app.current_page

        existing_ids = {rec.rec_id for rec in self.app.record_manager.recordings}
        remove_ids = {rec.rec_id for rec in recordings}
        keep_ids = existing_ids - remove_ids

        cards_to_remove = [
            card_data["card"]
            for rec_id, card_data in self.cards_obj.items()
            if rec_id not in keep_ids
        ]

        home_page.recording_card_area.content.controls = [
            control
            for control in home_page.recording_card_area.content.controls
            if control not in cards_to_remove
        ]

        self.cards_obj = {
            k: v for k, v in self.cards_obj.items()
            if k in keep_ids
        }
        home_page.recording_card_area.update()

    @staticmethod
    async def update_record_hover(recording: Recording):
        return ft.Colors.GREY_400 if recording.selected else None

    @staticmethod
    def get_icon_for_recording_state(recording: Recording):
        """Return the appropriate icon based on the recording's state."""
        return ft.Icons.PLAY_CIRCLE if not recording.recording else ft.Icons.STOP_CIRCLE

    def get_tip_for_recording_state(self, recording: Recording):
        return self._["stop_record"] if recording.recording else self._["start_record"]

    @staticmethod
    def get_icon_for_monitor_state(recording: Recording):
        """Return the appropriate icon based on the monitor's state."""
        return ft.Icons.VISIBILITY if recording.monitor_status else ft.Icons.VISIBILITY_OFF

    def get_tip_for_monitor_state(self, recording: Recording):
        return self._["stop_monitor"] if recording.monitor_status else self._["start_monitor"]

    async def update_duration(self, recording: Recording):
        """Update the duration text periodically."""
        while True:
            await asyncio.sleep(1)  # Update every second
            if not recording or recording.rec_id not in self.cards_obj:  # Stop task if card is removed
                break

            if recording.recording:
                duration_label = self.cards_obj[recording.rec_id]["duration_label"]
                duration_label.value = self.app.record_manager.get_duration(recording)
                duration_label.update()

    def start_update_task(self, recording: Recording):
        """Start a background task to update the duration text."""
        self.update_duration_tasks[recording.rec_id] = self.app.page.run_task(self.update_duration, recording)

    async def on_card_click(self, recording: Recording):
        """Handle card click events."""
        recording.selected = not recording.selected
        self.selected_cards[recording.rec_id] = recording
        self.cards_obj[recording.rec_id]["card"].content.bgcolor = await self.update_record_hover(recording)
        self.cards_obj[recording.rec_id]["card"].update()

    async def recording_dir_on_click(self, recording: Recording):
        if recording.recording_dir:
            if os.path.exists(recording.recording_dir):
                if not utils.open_folder(recording.recording_dir):
                    await self.app.snack_bar.show_snack_bar(self._['no_video_file'])
            else:
                await self.app.snack_bar.show_snack_bar(self._["no_recording_folder"])

    async def edit_recording_button_click(self, _, recording: Recording):
        """Handle edit button click by showing the edit dialog with existing recording info."""

        if recording.recording or recording.monitor_status:
            await self.app.snack_bar.show_snack_bar(self._["please_stop_monitor_tip"])
            return

        await RecordingDialog(
            self.app,
            on_confirm_callback=self.edit_recording_callback,
            recording=recording,
        ).show_dialog()

    async def recording_delete_button_click(self, _, recording: Recording):
        async def confirm_dlg(_):
            self.app.page.run_task(self.on_delete_recording, recording)
            await close_dialog(None)

        async def close_dialog(_):
            delete_alert_dialog.open = False
            delete_alert_dialog.update()

        delete_alert_dialog = ft.AlertDialog(
            title=ft.Text(self._["confirm"]),
            content=ft.Text(self._["delete_confirm_tip"]),
            actions=[
                ft.TextButton(text=self._["cancel"], on_click=close_dialog),
                ft.TextButton(text=self._["sure"], on_click=confirm_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=False,
        )
        delete_alert_dialog.open = True
        self.app.dialog_area.content = delete_alert_dialog
        self.app.page.update()

    async def preview_video_button_on_click(self, _, recording: Recording):
        if self.app.is_web and recording.record_url:
            video_player = VideoPlayer(self.app)
            await video_player.preview_video(recording.record_url, is_file_path=False, room_url=recording.url)
        elif recording.recording_dir and os.path.exists(recording.recording_dir):
            video_files = []
            for root, _, files in os.walk(recording.recording_dir):
                for file in files:
                    if utils.is_valid_video_file(file):
                        video_files.append(os.path.join(root, file))

            if video_files:
                video_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest_video = video_files[0]
                await StoragePage(self.app).preview_file(latest_video, recording.url)
            else:
                await self.app.snack_bar.show_snack_bar(self._["no_video_file"])
        else:
            await self.app.snack_bar.show_snack_bar(self._["no_recording_folder"])

    async def recording_button_on_click(self, _, recording: Recording):
        await self.on_toggle_recording(recording)

    async def recording_dir_button_on_click(self, _, recording: Recording):
        await self.recording_dir_on_click(recording)

    async def recording_info_button_on_click(self, _, recording: Recording):
        await self.show_recording_info_dialog(recording)
    
    async def transcript_button_on_click(self, _, recording: Recording):
        await self.show_transcript_dialog(recording)

    async def monitor_button_on_click(self, _, recording: Recording):
        await self.update_monitor_state(recording)

    async def recording_card_on_click(self, _, recording: Recording):
        await self.on_card_click(recording)

    async def subscribe_update_card(self, _, recording: Recording):
        await self.update_card(recording)

    async def subscribe_remove_cards(self, _, recordings: list[Recording]):
        await self.remove_recording_card(recordings)
