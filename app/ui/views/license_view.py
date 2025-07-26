"""
License View - 许可证管理界面
"""

import flet as ft
from datetime import datetime

from ..base_page import PageBase
from ...utils.logger import logger


class LicenseView(PageBase):
    def __init__(self, app):
        super().__init__(app)
        self.page_name = "license"
        self.license_manager = None
        self.license_key_field = None
        self.email_field = None
        self.company_field = None
        self.status_card = None
        self.features_card = None
        self._ = {}
        self.load_language()
        self._init_license_manager()
    
    def _init_license_manager(self):
        """初始化许可证管理器"""
        try:
            if not hasattr(self.app, 'license_manager'):
                from ...core.license_manager import LicenseManager
                self.app.license_manager = LicenseManager(self.app)
            self.license_manager = self.app.license_manager
        except Exception as e:
            logger.error(f"初始化许可证管理器失败: {e}")
    
    def load_language(self):
        language = self.app.language_manager.language
        for key in ("license_page", "base"):
            self._.update(language.get(key, {}))
    
    async def load(self):
        """加载许可证管理页面"""
        self.app.content_area.controls.clear()
        
        page_content = ft.Column([
            self.create_header(),
            ft.Divider(),
            self.create_activation_section(),
            ft.Divider(),
            self.create_status_section(),
        ], expand=True, spacing=20, scroll=ft.ScrollMode.AUTO)
        
        self.app.content_area.controls.append(
            ft.Container(content=page_content, padding=20, expand=True)
        )
        
        await self.refresh_license_status()
        self.app.content_area.update()
    
    def create_header(self) -> ft.Control:
        """创建页面头部"""
        return ft.Row([
            ft.Icon(ft.icons.VERIFIED_USER, size=32, color=ft.colors.BLUE),
            ft.Text(
                self._.get("license_management", "许可证管理"),
                theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                weight=ft.FontWeight.BOLD
            ),
            ft.Container(expand=True),
            ft.IconButton(
                icon=ft.icons.REFRESH,
                tooltip=self._.get("refresh_status", "刷新状态"),
                on_click=self.refresh_license_status
            )
        ])
    
    def create_activation_section(self) -> ft.Control:
        """创建激活区域"""
        self.license_key_field = ft.TextField(
            label=self._.get("license_key", "许可证密钥"),
            hint_text=self._.get("enter_license_key", "请输入您的许可证密钥"),
            width=400,
            password=True,
            can_reveal_password=True
        )
        
        self.email_field = ft.TextField(
            label=self._.get("email", "邮箱"),
            hint_text=self._.get("enter_email", "请输入您的邮箱地址"),
            width=300
        )
        
        self.company_field = ft.TextField(
            label=self._.get("company", "公司名称"),
            hint_text=self._.get("enter_company", "请输入公司名称（可选）"),
            width=300
        )
        
        machine_id = self.license_manager.get_machine_id() if self.license_manager else "unknown"
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        self._.get("activate_license", "激活许可证"),
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        self._.get("activation_description", "请输入您的许可证密钥以激活软件"),
                        color=ft.colors.GREY_600
                    ),
                    ft.Divider(),
                    self.license_key_field,
                    ft.Row([self.email_field, self.company_field], spacing=20),
                    ft.Text(f"{self._.get('machine_id', '机器ID')}: {machine_id}", 
                           size=12, color=ft.colors.GREY_600),
                    ft.Row([
                        ft.ElevatedButton(
                            text=self._.get("activate", "激活"),
                            icon=ft.icons.VERIFIED_USER,
                            bgcolor=ft.colors.GREEN,
                            color=ft.colors.WHITE,
                            on_click=self.activate_license
                        ),
                        ft.TextButton(
                            text=self._.get("deactivate", "停用"),
                            icon=ft.icons.CANCEL,
                            on_click=self.deactivate_license
                        ),
                        ft.TextButton(
                            text=self._.get("purchase_license", "购买许可证"),
                            icon=ft.icons.SHOPPING_CART,
                            on_click=self.open_purchase_page
                        )
                    ], spacing=10)
                ], spacing=15),
                padding=20
            )
        )
    
    def create_status_section(self) -> ft.Control:
        """创建状态区域"""
        self.status_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text(
                        self._.get("license_status", "许可证状态"),
                        theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(self._.get("loading", "加载中..."))
                ], spacing=10),
                padding=20
            )
        )
        return self.status_card
    
    async def activate_license(self, e):
        """激活许可证"""
        if not self.license_manager:
            await self.show_error("许可证管理器未初始化")
            return
        
        license_key = self.license_key_field.value.strip()
        if not license_key:
            await self.show_error(self._.get("please_enter_license_key", "请输入许可证密钥"))
            return
        
        email = self.email_field.value.strip()
        company = self.company_field.value.strip()
        
        try:
            success, message = await self.license_manager.activate_license(
                license_key, email, company
            )
            
            if success:
                await self.show_success(message)
                await self.refresh_license_status()
            else:
                await self.show_error(message)
        
        except Exception as ex:
            await self.show_error(f"激活失败: {ex}")
    
    async def deactivate_license(self, e):
        """停用许可证"""
        if not self.license_manager:
            return
        
        async def confirm_deactivate(e):
            if self.license_manager.deactivate_license():
                await self.show_success(self._.get("deactivate_success", "许可证已停用"))
                await self.refresh_license_status()
            else:
                await self.show_error(self._.get("deactivate_failed", "停用失败"))
            confirm_dialog.open = False
            self.page.update()
        
        async def cancel_deactivate(e):
            confirm_dialog.open = False
            self.page.update()
        
        confirm_dialog = ft.AlertDialog(
            title=ft.Text(self._.get("confirm", "确认")),
            content=ft.Text(self._.get("confirm_deactivate", "确定要停用当前许可证吗？")),
            actions=[
                ft.TextButton(text=self._.get("cancel", "取消"), on_click=cancel_deactivate),
                ft.TextButton(text=self._.get("confirm", "确认"), on_click=confirm_deactivate)
            ]
        )
        
        self.app.dialog_area.content = confirm_dialog
        confirm_dialog.open = True
        self.page.update()
    
    async def refresh_license_status(self, e=None):
        """刷新许可证状态"""
        if not self.license_manager:
            return
        
        try:
            status = self.license_manager.get_license_status()
            await self.update_status_card(status)
        except Exception as ex:
            logger.error(f"刷新许可证状态失败: {ex}")
    
    async def update_status_card(self, status: dict):
        """更新状态卡片"""
        status_text = status.get('message', '未知状态')
        status_color = self.get_status_color(status.get('status', 'unknown'))
        
        status_controls = [
            ft.Row([
                ft.Icon(
                    self.get_status_icon(status.get('status', 'unknown')),
                    color=status_color,
                    size=24
                ),
                ft.Text(status_text, size=16, weight=ft.FontWeight.BOLD, color=status_color)
            ], spacing=10)
        ]
        
        if status.get('is_valid'):
            user_info = status.get('user_info', {})
            if user_info.get('email'):
                status_controls.append(ft.Text(f"邮箱: {user_info['email']}", size=14))
            if user_info.get('company'):
                status_controls.append(ft.Text(f"公司: {user_info['company']}", size=14))
            
            days_remaining = status.get('days_remaining', 0)
            if days_remaining > 0:
                status_controls.append(
                    ft.Text(f"剩余天数: {days_remaining} 天", size=14, color=ft.colors.ORANGE)
                )
        
        # 显示功能信息
        features = status.get('features', {})
        feature_items = [
            ('speech_recognition', '语音识别', lambda x: "✓" if x else "✗"),
            ('advanced_features', '高级功能', lambda x: "✓" if x else "✗"),
            ('max_recordings', '最大录制数量', lambda x: f"{x}" if x != -1 else "无限制"),
        ]
        
        status_controls.append(ft.Divider())
        status_controls.append(ft.Text("功能权限:", weight=ft.FontWeight.BOLD))
        
        for key, label, formatter in feature_items:
            value = features.get(key, False)
            formatted_value = formatter(value)
            color = ft.colors.GREEN if (isinstance(value, bool) and value) or (isinstance(value, int) and value != 0) else ft.colors.RED
            
            status_controls.append(
                ft.Row([
                    ft.Text(label, size=14, expand=True),
                    ft.Text(formatted_value, size=14, color=color, weight=ft.FontWeight.BOLD)
                ])
            )
        
        self.status_card.content = ft.Container(
            content=ft.Column([
                ft.Text(
                    self._.get("license_status", "许可证状态"),
                    theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                    weight=ft.FontWeight.BOLD
                ),
                *status_controls
            ], spacing=10),
            padding=20
        )
        
        if hasattr(self, 'page'):
            self.page.update()
    
    def get_status_color(self, status: str) -> str:
        """获取状态颜色"""
        color_map = {
            'active': ft.colors.GREEN,
            'expired': ft.colors.RED,
            'invalid': ft.colors.RED,
            'unlicensed': ft.colors.ORANGE,
            'error': ft.colors.RED
        }
        return color_map.get(status, ft.colors.GREY)
    
    def get_status_icon(self, status: str) -> str:
        """获取状态图标"""
        icon_map = {
            'active': ft.icons.CHECK_CIRCLE,
            'expired': ft.icons.ERROR,
            'invalid': ft.icons.ERROR,
            'unlicensed': ft.icons.WARNING,
            'error': ft.icons.ERROR
        }
        return icon_map.get(status, ft.icons.HELP)
    
    async def open_purchase_page(self, e):
        """打开购买页面"""
        import webbrowser
        try:
            webbrowser.open("https://github.com/tmwgsicp/StreamVault-Pro")
            await self.show_success(self._.get("purchase_page_opened", "购买页面已在浏览器中打开"))
        except Exception as ex:
            await self.show_error(f"打开购买页面失败: {ex}")
    
    async def show_success(self, message: str):
        """显示成功消息"""
        await self.app.snack_bar.show_snack_bar(message, bgcolor=ft.colors.GREEN)
    
    async def show_error(self, message: str):
        """显示错误消息"""
        await self.app.snack_bar.show_snack_bar(message, bgcolor=ft.colors.RED) 