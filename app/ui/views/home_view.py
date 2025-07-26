import asyncio
import uuid

import flet as ft

from ...models.recording_model import Recording
from ...models.recording_status_model import RecordingStatus
from ...utils.logger import logger
from ..base_page import PageBase
from ..components.help_dialog import HelpDialog
from ..components.recording_dialog import RecordingDialog
from ..components.search_dialog import SearchDialog


class HomePage(PageBase):
    def __init__(self, app):
        super().__init__(app)
        self.page_name = "home"
        self.recording_card_area = None
        self.add_recording_dialog = None
        self.is_grid_view = app.settings.default_config.get("is_grid_view", True)
        self.loading_indicator = None
        self.app.language_manager.add_observer(self)
        self.load_language()
        self.current_filter = "all"
        self.init()

    def load_language(self):
        language = self.app.language_manager.language
        for key in ("home_page", "video_quality", "base"):
            self._.update(language.get(key, {}))

    def init(self):
        self.loading_indicator = ft.ProgressRing(
            width=40, 
            height=40, 
            stroke_width=3,
            visible=False
        )
        
        if self.is_grid_view:
            initial_content = ft.GridView(
                expand=True,
                runs_count=3,
                spacing=10,
                run_spacing=10,
                child_aspect_ratio=1.35,  # 提高比例降低卡片高度，消除底部空白
                controls=[]
            )
        else:
            initial_content = ft.Column(
                controls=[], 
                spacing=5, 
                expand=True
            )
        
        self.recording_card_area = ft.Container(
            content=initial_content,
            expand=True
        )
        self.add_recording_dialog = RecordingDialog(self.app, self.add_recording)
        self.pubsub_subscribe()

    async def load(self):
        """Load the home page content."""
        self.content_area.controls.extend(
            [
                self.create_home_title_area(),
                self.create_filter_area(),
                self.create_home_content_area()
            ]
        )
        self.content_area.update()
        
        self.recording_card_area.content.controls.clear()
        await self.add_record_cards()
        
        if self.is_grid_view:
            await self.recalculate_grid_columns()
        
        self.page.on_keyboard_event = self.on_keyboard
        self.page.on_resized = self.update_grid_layout

    def pubsub_subscribe(self):
        self.app.page.pubsub.subscribe_topic('add', self.subscribe_add_cards)
        self.app.page.pubsub.subscribe_topic('delete_all', self.subscribe_del_all_cards)

    async def toggle_view_mode(self, _):
        self.is_grid_view = not self.is_grid_view
        
        # 重新创建所有卡片以适应新的布局模式
        await self.recreate_cards_for_layout()
        
        self.app.settings.default_config["is_grid_view"] = self.is_grid_view
        self.page.run_task(self.app.config_manager.save_user_config, self.app.settings.default_config)
    
    async def recreate_cards_for_layout(self):
        """重新创建所有卡片以适应当前布局模式"""
        recordings = self.app.record_manager.recordings.copy()
        
        # 清空当前卡片
        self.app.record_card_manager.cards_obj.clear()
        
        column_width = 350
        runs_count = max(1, int(self.page.width / column_width))

        if self.is_grid_view:
            new_content = ft.GridView(
                expand=True,
                runs_count=runs_count,
                spacing=10,
                run_spacing=10,
                child_aspect_ratio=1.35,  # 提高比例降低卡片高度，消除底部空白
                controls=[]
            )
        else:
            new_content = ft.Column(
                controls=[],
                spacing=5,
                expand=True
            )

        self.recording_card_area.content = new_content

        # 重新创建所有卡片
        layout_mode = "grid" if self.is_grid_view else "list"
        for recording in recordings:
            card = await self.app.record_card_manager.create_card(recording, layout_mode)
            self.recording_card_area.content.controls.append(card)

        # 重新创建页面结构
        self.content_area.clean()
        self.content_area.controls.extend([
            self.create_home_title_area(),
            self.create_filter_area(),
            self.create_home_content_area()
        ])
        self.content_area.update()
        
        # 应用当前筛选
        await self.apply_filter()

    def create_home_title_area(self):
        return ft.Row(
            [
                ft.Text(self._["recording_list"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.GRID_VIEW if self.is_grid_view else ft.Icons.LIST,
                    tooltip=self._["toggle_view"],
                    on_click=self.toggle_view_mode
                ),
                ft.IconButton(icon=ft.Icons.SEARCH, tooltip=self._["search"], on_click=self.search_on_click),
                ft.IconButton(icon=ft.Icons.ADD, tooltip=self._["add_record"], on_click=self.add_recording_on_click),
                ft.IconButton(icon=ft.Icons.REFRESH, tooltip=self._["refresh"], on_click=self.refresh_cards_on_click),
                ft.IconButton(
                    icon=ft.Icons.PLAY_ARROW,
                    tooltip=self._["batch_start"],
                    on_click=self.start_monitor_recordings_on_click,
                ),
                ft.IconButton(
                    icon=ft.Icons.STOP, tooltip=self._["batch_stop"], on_click=self.stop_monitor_recordings_on_click
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_SWEEP,
                    tooltip=self._["batch_delete"],
                    on_click=self.delete_monitor_recordings_on_click,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
        )
    
    def create_filter_area(self):
        """Create the enhanced filter and management area"""
        # 搜索框
        self.search_field = ft.TextField(
            label=self._["search"],
            hint_text="搜索主播名称、平台或URL...",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self.on_search_change,
            width=250,
        )
        
        # 状态筛选按钮
        status_filters = ft.Row([
            self.create_filter_button("all", self._["filter_all"], ft.Colors.BLUE, ft.Icons.ALL_INCLUSIVE),
            self.create_filter_button("recording", self._["filter_recording"], ft.Colors.GREEN, ft.Icons.FIBER_MANUAL_RECORD),
            self.create_filter_button("monitoring", "监控中", ft.Colors.ORANGE, ft.Icons.VISIBILITY),
            self.create_filter_button("offline", self._["filter_offline"], ft.Colors.AMBER, ft.Icons.VISIBILITY_OFF),
            self.create_filter_button("error", self._["filter_error"], ft.Colors.RED, ft.Icons.ERROR),
            self.create_filter_button("stopped", self._["filter_stopped"], ft.Colors.GREY, ft.Icons.PAUSE),
        ], spacing=5, scroll=ft.ScrollMode.AUTO)
        
        # 平台筛选下拉菜单
        self.platform_dropdown = ft.Dropdown(
            label="平台筛选",
            hint_text="选择平台",
            options=[
                ft.dropdown.Option("all", "全部平台"),
                ft.dropdown.Option("douyin", "抖音"),
                ft.dropdown.Option("bilibili", "B站"),
                ft.dropdown.Option("youtube", "YouTube"),
                ft.dropdown.Option("twitch", "Twitch"),
                ft.dropdown.Option("huya", "虎牙"),
                ft.dropdown.Option("douyu", "斗鱼"),
                ft.dropdown.Option("kuaishou", "快手"),
                ft.dropdown.Option("other", "其他"),
            ],
            value="all",
            on_change=self.on_platform_filter_change,
            width=120,
        )
        
        # 排序选项
        self.sort_dropdown = ft.Dropdown(
            label="排序方式",
            hint_text="选择排序",
            options=[
                ft.dropdown.Option("name", "按名称"),
                ft.dropdown.Option("status", "按状态"),
                ft.dropdown.Option("platform", "按平台"),
                ft.dropdown.Option("created", "按创建时间"),
                ft.dropdown.Option("last_record", "按最后录制"),
            ],
            value="name",
            on_change=self.on_sort_change,
            width=120,
        )
        
        # 统计信息
        self.stats_text = ft.Text(
            self.get_stats_text(),
            size=12,
            color=ft.Colors.GREY_600
        )
        
        # 顶部操作栏
        top_row = ft.Row([
            ft.Text("录制管理", theme_style=ft.TextThemeStyle.TITLE_MEDIUM, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            self.search_field,
            self.platform_dropdown,
            self.sort_dropdown,
            ft.VerticalDivider(width=1),
            ft.IconButton(
                icon=ft.Icons.GRID_VIEW if self.is_grid_view else ft.Icons.LIST,
                tooltip=self._["toggle_view"],
                on_click=self.toggle_view_mode,
                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_100)
            ),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                tooltip=self._["refresh"],
                on_click=self.refresh_cards_on_click,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_100)
            ),
        ], alignment=ft.MainAxisAlignment.START, spacing=10)
        
        # 快速操作栏
        action_row = ft.Row([
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.ADD, size=16),
                    ft.Text("新增录制")
                ], spacing=5, tight=True),
                on_click=self.add_recording_on_click,
                bgcolor=ft.Colors.BLUE_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            ft.Container(width=10),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.PLAY_ARROW, size=16),
                    ft.Text("批量开始")
                ], spacing=5, tight=True),
                on_click=self.start_monitor_recordings_on_click,
                bgcolor=ft.Colors.GREEN_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.STOP, size=16),
                    ft.Text("批量停止")
                ], spacing=5, tight=True),
                on_click=self.stop_monitor_recordings_on_click,
                bgcolor=ft.Colors.ORANGE_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_SWEEP, size=16),
                    ft.Text("批量删除")
                ], spacing=5, tight=True),
                on_click=self.delete_monitor_recordings_on_click,
                bgcolor=ft.Colors.RED_600,
                color=ft.Colors.WHITE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
            ),
            ft.Container(expand=True),
            self.stats_text,
        ], alignment=ft.MainAxisAlignment.START, spacing=8)
        
        return ft.Column([
            top_row,
            ft.Container(height=8),
            ft.Text("状态筛选:", size=12, weight=ft.FontWeight.BOLD),
            status_filters,
            ft.Container(height=8),
            action_row,
            ft.Divider(height=1, thickness=1),
        ], spacing=5)
    
    def create_filter_button(self, filter_type, text, color, icon):
        """创建筛选按钮"""
        is_active = self.current_filter == filter_type
        return ft.ElevatedButton(
            content=ft.Row([
                ft.Icon(icon, size=14),
                ft.Text(text, size=12)
            ], spacing=3, tight=True),
            on_click=lambda _: self.apply_filter_by_type(filter_type),
            bgcolor=color if is_active else ft.Colors.GREY_100,
            color=ft.Colors.WHITE if is_active else ft.Colors.GREY_700,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.Padding(8, 4, 8, 4)
            ),
        )
    
    async def on_search_change(self, e):
        """搜索框变化事件"""
        query = e.control.value
        # 使用防抖优化搜索性能
        await self.debounced_search(query)
        self.update_stats()
    
    async def debounced_search(self, query: str):
        """防抖搜索，避免频繁查询"""
        # 取消之前的搜索任务
        if hasattr(self, '_search_task') and not self._search_task.done():
            self._search_task.cancel()
        
        # 创建新的搜索任务
        self._search_task = asyncio.create_task(self._perform_search(query))
        await self._search_task
    
    async def _perform_search(self, query: str):
        """执行实际的搜索操作"""
        await asyncio.sleep(0.3)  # 300ms防抖延迟
        await self.filter_recordings(query)
    
    async def on_platform_filter_change(self, e):
        """平台筛选变化事件"""
        platform = e.control.value
        await self.apply_platform_filter(platform)
        self.update_stats()
    
    async def on_sort_change(self, e):
        """排序方式变化事件"""
        sort_type = e.control.value
        await self.apply_sort(sort_type)
    
    async def apply_filter_by_type(self, filter_type):
        """应用状态筛选"""
        self.current_filter = filter_type
        await self.apply_filter()
        self.update_stats()
        # 重新创建筛选区域以更新按钮状态
        self.content_area.controls[1] = self.create_filter_area()
        self.content_area.update()
    
    async def apply_platform_filter(self, platform):
        """应用平台筛选"""
        cards_obj = self.app.record_card_manager.cards_obj
        recordings = self.app.record_manager.recordings
        
        for recording in recordings:
            card_info = cards_obj.get(recording.rec_id)
            if not card_info:
                continue
            
            # 检查是否符合平台筛选
            platform_match = True
            if platform != "all":
                recording_platform = self.extract_platform_from_url(recording.url).lower()
                platform_match = platform in recording_platform or recording_platform in platform
            
            # 检查是否符合状态筛选
            status_match = self.should_show_recording(self.current_filter, recording)
            
            card_info["card"].visible = platform_match and status_match
        
        self.recording_card_area.update()
    
    def extract_platform_from_url(self, url: str) -> str:
        """从URL中提取平台信息"""
        if not url:
            return "other"
        
        url_lower = url.lower()
        if "douyin" in url_lower or "tiktok" in url_lower:
            return "douyin"
        elif "bilibili" in url_lower:
            return "bilibili"
        elif "youtube" in url_lower:
            return "youtube"
        elif "twitch" in url_lower:
            return "twitch"
        elif "huya" in url_lower:
            return "huya"
        elif "douyu" in url_lower:
            return "douyu"
        elif "kuaishou" in url_lower:
            return "kuaishou"
        else:
            return "other"
    
    async def apply_sort(self, sort_type):
        """应用排序"""
        recordings = self.app.record_manager.recordings.copy()
        
        if sort_type == "name":
            recordings.sort(key=lambda r: r.streamer_name or "")
        elif sort_type == "status":
            recordings.sort(key=lambda r: (
                0 if r.recording else
                1 if r.is_live and r.monitor_status else
                2 if r.monitor_status else
                3
            ))
        elif sort_type == "platform":
            recordings.sort(key=lambda r: self.extract_platform_from_url(r.url))
        elif sort_type == "created":
            recordings.sort(key=lambda r: r.rec_id)  # 按创建顺序
        elif sort_type == "last_record":
            recordings.sort(key=lambda r: getattr(r, 'last_record_time', ''), reverse=True)
        
        # 重新排列卡片
        cards_obj = self.app.record_card_manager.cards_obj
        sorted_cards = []
        for recording in recordings:
            card_info = cards_obj.get(recording.rec_id)
            if card_info and card_info["card"]:
                sorted_cards.append(card_info["card"])
        
        self.recording_card_area.content.controls.clear()
        self.recording_card_area.content.controls.extend(sorted_cards)
        self.recording_card_area.update()
    
    def get_stats_text(self):
        """获取统计信息文本"""
        recordings = self.app.record_manager.recordings
        if not recordings:
            return "暂无录制项目"
        
        total = len(recordings)
        recording_count = sum(1 for r in recordings if r.recording)
        monitoring_count = sum(1 for r in recordings if r.monitor_status and not r.recording)
        live_count = sum(1 for r in recordings if r.is_live and r.monitor_status)
        
        return f"总计: {total} | 录制中: {recording_count} | 监控中: {monitoring_count} | 直播中: {live_count}"
    
    def update_stats(self):
        """更新统计信息"""
        if hasattr(self, 'stats_text'):
            self.stats_text.value = self.get_stats_text()
            self.stats_text.update()
    
    async def filter_all_on_click(self, _):
        self.current_filter = "all"
        await self.apply_filter()
    
    async def filter_recording_on_click(self, _):
        self.current_filter = "recording"
        await self.apply_filter()
    
    async def filter_error_on_click(self, _):
        self.current_filter = "error"
        await self.apply_filter()
    
    async def filter_offline_on_click(self, _):
        self.current_filter = "offline"
        await self.apply_filter()
    
    async def filter_stopped_on_click(self, _):
        self.current_filter = "stopped"
        await self.apply_filter()
    
    async def apply_filter(self):
        self.content_area.controls[1] = self.create_filter_area()
        
        cards_obj = self.app.record_card_manager.cards_obj
        recordings = self.app.record_manager.recordings
        
        for recording in recordings:
            card_info = cards_obj.get(recording.rec_id)
            if not card_info:
                continue
                
            visible = False
            if self.current_filter == "all":
                visible = True
            elif self.current_filter == "recording":
                visible = recording.recording
            elif self.current_filter == "error":
                visible = recording.status_info == RecordingStatus.RECORDING_ERROR
            elif self.current_filter == "offline":
                visible = not recording.is_live and recording.monitor_status
            elif self.current_filter == "stopped":
                visible = not recording.monitor_status
                
            card_info["card"].visible = visible
            
        self.content_area.update()
        self.recording_card_area.update()

    async def reset_cards_visibility(self):
        cards_obj = self.app.record_card_manager.cards_obj
        for card_info in cards_obj.values():
            if not card_info["card"].visible:
                card_info["card"].visible = True
                card_info["card"].update()

    @staticmethod
    def should_show_recording(filter_type, recording):
        """判断录制项目是否应该显示在当前筛选条件下"""
        if filter_type == "all":
            return True
        elif filter_type == "recording":
            return recording.recording
        elif filter_type == "monitoring":
            return recording.monitor_status and not recording.recording and recording.is_live
        elif filter_type == "error":
            return recording.status_info == RecordingStatus.RECORDING_ERROR
        elif filter_type == "offline":
            return not recording.is_live and recording.monitor_status and not recording.recording
        elif filter_type == "stopped":
            return not recording.monitor_status
        else:
            return True

    async def filter_recordings(self, query):
        recordings = self.app.record_manager.recordings
        cards_obj = self.app.record_card_manager.cards_obj

        if not query.strip():
            await self.apply_filter()
            return {}
        else:
            lower_query = query.strip().lower()
            search_ids = {
                rec.rec_id
                for rec in recordings
                if lower_query in str(rec.to_dict()).lower() or lower_query in rec.display_title
            }
            
            filtered_ids = set()
            for rec_id in search_ids:
                recording = self.app.record_manager.find_recording_by_id(rec_id)
                if not recording:
                    continue

                if self.should_show_recording(self.current_filter, recording):
                    filtered_ids.add(rec_id)

            for card_info in cards_obj.values():
                card_info["card"].visible = card_info["card"].key in filtered_ids
                card_info["card"].update()

            if not filtered_ids:
                await self.app.snack_bar.show_snack_bar(self._["not_search_result"], duration=2000)
            return filtered_ids

    def create_home_content_area(self):
        return ft.Column(
            expand=True,
            controls=[
                ft.Divider(height=1),
                ft.Container(
                    content=self.loading_indicator,
                    alignment=ft.alignment.center
                ),
                self.recording_card_area,
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    async def add_record_cards(self):
        
        self.loading_indicator.visible = True
        self.loading_indicator.update()

        cards_to_create = []
        existing_cards = []
        
        for recording in self.app.record_manager.recordings:
            if recording.rec_id not in self.app.record_card_manager.cards_obj:
                cards_to_create.append(recording)
            else:
                existing_card = self.app.record_card_manager.cards_obj[recording.rec_id]["card"]
                existing_card.visible = True
                existing_cards.append(existing_card)
        
        async def create_card_with_time_range(_recording: Recording):
            # 传递当前的视图模式
            layout_mode = "grid" if self.is_grid_view else "list"
            _card = await self.app.record_card_manager.create_card(_recording, layout_mode)
            _recording.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
                _recording.scheduled_start_time, _recording.monitor_hours
            )
            return _card, _recording
        
        if cards_to_create:
            results = await asyncio.gather(*[
                create_card_with_time_range(recording)
                for recording in cards_to_create
            ])
            
            for card, recording in results:
                self.recording_card_area.content.controls.append(card)
                self.app.record_card_manager.cards_obj[recording.rec_id]["card"] = card
        
        if existing_cards:
            self.recording_card_area.content.controls.extend(existing_cards)

        self.loading_indicator.visible = False
        self.loading_indicator.update()
        self.recording_card_area.update()
        
        if not self.app.record_manager.periodic_task_started:
            self.page.run_task(
                self.app.record_manager.setup_periodic_live_check,
                self.app.record_manager.loop_time_seconds
            )
        
        await self.apply_filter()

    async def show_all_cards(self):
        cards_obj = self.app.record_card_manager.cards_obj
        for card in cards_obj.values():
            card["card"].visible = True
        self.recording_card_area.update()
        
        await self.apply_filter()

    async def add_recording(self, recordings_info):
        default_config = self.app.settings.default_config
        logger.info(f"Add items: {len(recordings_info)}")
        
        new_recordings = []
        for recording_info in recordings_info:
            if recording_info.get("record_format"):
                recording = Recording(
                    rec_id=str(uuid.uuid4()),
                    url=recording_info["url"],
                    streamer_name=recording_info["streamer_name"],
                    quality=recording_info["quality"],
                    record_format=recording_info["record_format"],
                    segment_record=recording_info["segment_record"],
                    segment_time=recording_info["segment_time"],
                    monitor_status=recording_info["monitor_status"],
                    scheduled_recording=recording_info["scheduled_recording"],
                    scheduled_start_time=recording_info["scheduled_start_time"],
                    monitor_hours=recording_info["monitor_hours"],
                    recording_dir=recording_info["recording_dir"],
                    enabled_message_push=recording_info["enabled_message_push"]
                )
            else:
                recording = Recording(
                    rec_id=str(uuid.uuid4()),
                    url=recording_info["url"],
                    streamer_name=recording_info["streamer_name"],
                    quality=recording_info["quality"],
                    record_format=default_config.get("video_format", "TS"),
                    segment_record=default_config.get("segmented_recording_enabled", False),
                    segment_time=default_config.get("video_segment_time", "1800"),
                    monitor_status=True,
                    scheduled_recording=default_config.get("scheduled_recording", False),
                    scheduled_start_time=default_config.get("scheduled_start_time"),
                    monitor_hours=default_config.get("monitor_hours"),
                    recording_dir=None,
                    enabled_message_push=False
                )

            recording.loop_time_seconds = int(default_config.get("loop_time_seconds", 300))
            recording.update_title(self._[recording.quality])
            await self.app.record_manager.add_recording(recording)
            new_recordings.append(recording)

        if new_recordings:
            async def create_card_with_time_range(rec):
                layout_mode = "grid" if self.is_grid_view else "list"
                _card = await self.app.record_card_manager.create_card(rec, layout_mode)
                rec.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
                    rec.scheduled_start_time, rec.monitor_hours
                )
                return _card, rec

            results = await asyncio.gather(*[
                create_card_with_time_range(rec)
                for rec in new_recordings
            ])

            for card, recording in results:
                self.recording_card_area.content.controls.append(card)
                self.app.record_card_manager.cards_obj[recording.rec_id]["card"] = card
                self.app.page.pubsub.send_others_on_topic("add", recording)
            
            self.recording_card_area.update()

        await self.app.snack_bar.show_snack_bar(self._["add_recording_success_tip"], bgcolor=ft.Colors.GREEN)

    async def search_on_click(self, _e):
        """Open the search dialog when the search button is clicked."""
        search_dialog = SearchDialog(home_page=self)
        search_dialog.open = True
        self.app.dialog_area.content = search_dialog
        self.app.dialog_area.update()

    async def add_recording_on_click(self, _e):
        await self.add_recording_dialog.show_dialog()

    async def refresh_cards_on_click(self, _e):
        
        self.loading_indicator.visible = True
        self.loading_indicator.update()
        
        cards_obj = self.app.record_card_manager.cards_obj
        recordings = self.app.record_manager.recordings
        selected_cards = self.app.record_card_manager.selected_cards
        new_ids = {rec.rec_id for rec in recordings}
        to_remove = []
        for card_id, card in cards_obj.items():
            if card_id not in new_ids:
                to_remove.append(card)
                continue
            if card_id in selected_cards:
                selected_cards[card_id].selected = False
                card["card"].content.bgcolor = None
                card["card"].update()

        for card in to_remove:
            card_key = card["card"].key
            cards_obj.pop(card_key, None)
            self.recording_card_area.controls.remove(card["card"])
        await self.show_all_cards()
        
        self.loading_indicator.visible = False
        self.loading_indicator.update()
        
        await self.app.snack_bar.show_snack_bar(self._["refresh_success_tip"], bgcolor=ft.Colors.GREEN)

    async def start_monitor_recordings_on_click(self, _):
        await self.app.record_manager.check_free_space()
        if self.app.recording_enabled:
            await self.app.record_manager.start_monitor_recordings()
            await self.app.snack_bar.show_snack_bar(self._["start_recording_success_tip"], bgcolor=ft.Colors.GREEN)

    async def stop_monitor_recordings_on_click(self, _):
        await self.app.record_manager.stop_monitor_recordings()
        await self.app.snack_bar.show_snack_bar(self._["stop_recording_success_tip"])

    async def delete_monitor_recordings_on_click(self, _):
        selected_recordings = await self.app.record_manager.get_selected_recordings()
        tips = self._["batch_delete_confirm_tip"] if selected_recordings else self._["clear_all_confirm_tip"]

        async def confirm_dlg(_):

            if selected_recordings:
                await self.app.record_manager.stop_monitor_recordings(selected_recordings)
                await self.app.record_manager.delete_recording_cards(selected_recordings)
            else:
                await self.app.record_manager.stop_monitor_recordings(self.app.record_manager.recordings)
                await self.app.record_manager.clear_all_recordings()
                await self.delete_all_recording_cards()
                self.app.page.pubsub.send_others_on_topic("delete_all", None)

            self.recording_card_area.update()
            await self.app.snack_bar.show_snack_bar(
                self._["delete_recording_success_tip"], bgcolor=ft.Colors.GREEN, duration=2000
            )
            await close_dialog(None)

        async def close_dialog(_):
            batch_delete_alert_dialog.open = False
            batch_delete_alert_dialog.update()

        batch_delete_alert_dialog = ft.AlertDialog(
            title=ft.Text(self._["confirm"]),
            content=ft.Text(tips),
            actions=[
                ft.TextButton(text=self._["cancel"], on_click=close_dialog),
                ft.TextButton(text=self._["sure"], on_click=confirm_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=False,
        )

        batch_delete_alert_dialog.open = True
        self.app.dialog_area.content = batch_delete_alert_dialog
        self.page.update()

    async def delete_all_recording_cards(self):
        self.recording_card_area.content.controls.clear()
        self.recording_card_area.update()
        self.app.record_card_manager.cards_obj = {}

    async def subscribe_del_all_cards(self, *_):
        await self.delete_all_recording_cards()

    async def subscribe_add_cards(self, _, recording: Recording):
        """Handle the subscription of adding cards from other clients"""
        
        self.loading_indicator.visible = True
        self.loading_indicator.update()
        
        if recording.rec_id not in self.app.record_card_manager.cards_obj:
            layout_mode = "grid" if self.is_grid_view else "list"
            card = await self.app.record_card_manager.create_card(recording, layout_mode)
            recording.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
                recording.scheduled_start_time, recording.monitor_hours
            )
            
            self.recording_card_area.content.controls.append(card)
            self.app.record_card_manager.cards_obj[recording.rec_id]["card"] = card
            
            self.loading_indicator.visible = False
            self.loading_indicator.update()
            
            self.recording_card_area.update()

    async def update_grid_layout(self, _):
        self.page.run_task(self.recalculate_grid_columns)

    async def recalculate_grid_columns(self):
        if not self.is_grid_view:
            return

        column_width = 350
        runs_count = max(1, int(self.page.width / column_width))

        if isinstance(self.recording_card_area.content, ft.GridView):
            grid_view = self.recording_card_area.content
            grid_view.runs_count = runs_count
            grid_view.update()

    async def on_keyboard(self, e: ft.KeyboardEvent):
        if e.alt and e.key == "H":
            self.app.dialog_area.content = HelpDialog(self.app)
            self.app.dialog_area.content.open = True
            self.app.dialog_area.update()
        if self.app.current_page == self:
            if e.ctrl and e.key == "F":
                self.page.run_task(self.search_on_click, e)
            elif e.ctrl and e.key == "R":
                self.page.run_task(self.refresh_cards_on_click, e)
            elif e.alt and e.key == "N":
                self.page.run_task(self.add_recording_on_click, e)
            elif e.alt and e.key == "B":
                self.page.run_task(self.start_monitor_recordings_on_click, e)
            elif e.alt and e.key == "P":
                self.page.run_task(self.stop_monitor_recordings_on_click, e)
            elif e.alt and e.key == "D":
                self.page.run_task(self.delete_monitor_recordings_on_click, e)
