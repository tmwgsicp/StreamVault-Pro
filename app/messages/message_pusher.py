from asyncio import create_task

from ..utils.logger import logger
from .notification_service import NotificationService


class MessagePusher:
    def __init__(self, settings):
        self.settings = settings
        self.notifier = NotificationService()

    async def push_messages(self, msg_title: str, push_content: str):
        """Push messages to all enabled notification services"""
        if self.settings.default_config.get("dingtalk_enabled"):
            create_task(
                self.notifier.send_to_dingtalk(
                    url=self.settings.default_config.get("dingtalk_webhook_url"),
                    content=push_content,
                    number=self.settings.default_config.get("dingtalk_at_objects"),
                    is_atall=self.settings.default_config.get("dingtalk_at_all"),
                )
            )
            logger.info("Push DingTalk message successfully")

        if self.settings.default_config.get("wechat_enabled"):
            create_task(
                self.notifier.send_to_wechat(
                    url=self.settings.default_config.get("wechat_webhook_url"), title=msg_title, content=push_content
                )
            )
            logger.info("Push Wechat message successfully")

        if self.settings.default_config.get("wecom_enabled"):
            create_task(
                self.notifier.send_to_wecom(
                    url=self.settings.default_config.get("wecom_webhook_url"),
                    title=msg_title,
                    content=push_content
                )
            )
            logger.info("Push WeCom message successfully")

        if self.settings.default_config.get("feishu_enabled"):
            create_task(
                self.notifier.send_to_feishu(
                    url=self.settings.default_config.get("feishu_webhook_url"),
                    title=msg_title,
                    content=push_content,
                    secret=self.settings.default_config.get("feishu_secret", "")
                )
            )
            logger.info("Push Feishu message successfully")

        if self.settings.default_config.get("bark_enabled"):
            create_task(
                self.notifier.send_to_bark(
                    api=self.settings.default_config.get("bark_webhook_url"),
                    title=msg_title,
                    content=push_content,
                    level=self.settings.default_config.get("bark_interrupt_level"),
                    sound=self.settings.default_config.get("bark_sound"),
                )
            )
            logger.info("Push Bark message successfully")

        if self.settings.default_config.get("ntfy_enabled"):
            create_task(
                self.notifier.send_to_ntfy(
                    api=self.settings.default_config.get("ntfy_server_url"),
                    title=msg_title,
                    content=push_content,
                    tags=self.settings.default_config.get("ntfy_tags"),
                    action_url=self.settings.default_config.get("ntfy_action_url"),
                    email=self.settings.default_config.get("ntfy_email"),
                )
            )
            logger.info("Push Ntfy message successfully")

        if self.settings.default_config.get("telegram_enabled"):
            create_task(
                self.notifier.send_to_telegram(
                    chat_id=self.settings.default_config.get("telegram_chat_id"),
                    token=self.settings.default_config.get("telegram_api_token"),
                    content=push_content,
                )
            )
            logger.info("Push Telegram message successfully")

        if self.settings.default_config.get("email_enabled"):
            create_task(
                self.notifier.send_to_email(
                    email_host=self.settings.default_config.get("smtp_server"),
                    login_email=self.settings.default_config.get("email_username"),
                    password=self.settings.default_config.get("email_password"),
                    sender_email=self.settings.default_config.get("sender_email"),
                    sender_name=self.settings.default_config.get("sender_name"),
                    to_email=self.settings.default_config.get("recipient_email"),
                    title=msg_title,
                    content=push_content,
                )
            )
            logger.info("Push Email message successfully")

        if self.settings.default_config.get("serverchan_enabled"):
            create_task(
                self.notifier.send_to_serverchan(
                    sendkey=self.settings.default_config.get("serverchan_sendkey"),
                    title=msg_title,
                    content=push_content,
                    channel=self.settings.default_config.get("serverchan_channel", 9),
                    tags=self.settings.default_config.get("serverchan_tags", "直播通知"),
                )
            )
            logger.info("Push ServerChan message successfully")
