"""
语音识别管理器
统一管理各种语音识别服务商和OSS文件上传
"""

import asyncio
import os
from typing import Optional

from ...utils.logger import logger
from ..oss import OSSManager

from .providers import AliyunSpeechProvider, TencentSpeechProvider
from .subtitle_generator import SubtitleGenerator
from ...utils import utils


class SpeechRecognitionManager:
    """语音识别管理器"""
    
    def __init__(self, app):
        self.app = app
        self.settings = app.settings
        self.subtitle_generator = SubtitleGenerator()
        self.subprocess_start_info = app.subprocess_start_up_info
        
        # 注册语音识别提供商
        self.providers = {
            "aliyun": AliyunSpeechProvider,
            "tencent": TencentSpeechProvider,
        }
        
        # 初始化OSS管理器
        self.oss_manager = OSSManager(self.settings)
    
    def is_enabled(self) -> bool:
        """检查语音识别功能是否启用"""
        return self.settings.default_config.get("speech_recognition_enabled", False)
    
    def get_provider_config(self, provider_name: str) -> dict:
        """获取指定服务商的配置"""
        config_prefix = f"speech_recognition_{provider_name}_"
        config = {}
        
        for key, value in self.settings.default_config.items():
            if key.startswith(config_prefix):
                config_key = key[len(config_prefix):]
                config[config_key] = value
        
        return config
    
    def create_provider(self, provider_name: str):
        """创建语音识别服务商实例"""
        if provider_name not in self.providers:
            raise ValueError(f"不支持的语音识别服务商: {provider_name}")
        
        provider_class = self.providers[provider_name]
        config = self.get_provider_config(provider_name)
        
        try:
            return provider_class(config)
        except ValueError as e:
            logger.error(f"创建{provider_name}服务商失败: {e}")
            return None
    
    async def convert_video_to_audio(self, video_file_path: str, audio_format: str = "mp3") -> Optional[str]:
        """
        将视频文件转换为音频文件
        
        Args:
            video_file_path: 视频文件路径
            audio_format: 目标音频格式
            
        Returns:
            转换后的音频文件路径，失败返回None
        """
        try:
            # 规范化路径，统一使用系统原生路径分隔符
            video_file_path = os.path.normpath(video_file_path)
            
            if not os.path.exists(video_file_path):
                logger.error(f"视频文件不存在: {video_file_path}")
                return None
            
            # 生成音频文件路径
            video_dir = os.path.dirname(video_file_path)
            video_name = os.path.splitext(os.path.basename(video_file_path))[0]
            audio_file_path = os.path.join(video_dir, f"{video_name}_audio.{audio_format}")
            
            # 如果音频文件已存在，直接返回
            if os.path.exists(audio_file_path):
                logger.info(f"音频文件已存在: {audio_file_path}")
                return audio_file_path
            
            # 使用FFmpeg提取音频
            command = [
                "ffmpeg",
                "-i", video_file_path,
                "-vn",  # 不包含视频流
                "-acodec", "libmp3lame" if audio_format == "mp3" else "pcm_s16le",
                "-ar", "16000",  # 采样率16kHz (适合语音识别)
                "-ac", "1",      # 单声道
                "-y",            # 覆盖输出文件
                audio_file_path
            ]
            
            logger.info(f"开始提取音频: {video_file_path} -> {audio_file_path}")
            
            # 执行转换命令
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                startupinfo=self.subprocess_start_info
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"音频提取成功: {audio_file_path}")
                return audio_file_path
            else:
                error_msg = stderr.decode('utf-8') if stderr else "未知错误"
                logger.error(f"音频提取失败: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"视频转音频异常: {e}")
            return None
    
    async def recognize_and_save_subtitle(self, video_file_path: str) -> bool:
        """
        对视频进行语音识别并生成字幕文件
        
        Args:
            video_file_path: 视频文件路径
            
        Returns:
            是否成功生成字幕
        """
        try:
            if not self.is_enabled():
                logger.debug("语音识别功能未启用")
                return False
            
            # 获取服务商配置
            provider_name = self.settings.default_config.get("speech_recognition_provider", "aliyun")
            language = self.settings.default_config.get("speech_recognition_language", "zh")
            subtitle_format = self.settings.default_config.get("speech_recognition_format", "srt")
            delete_audio = self.settings.default_config.get("speech_recognition_delete_audio", True)
            
            # 创建服务商实例
            provider = self.create_provider(provider_name)
            if not provider:
                logger.error(f"无法创建语音识别服务商: {provider_name}")
                return False
            
            logger.info(f"开始语音识别: {video_file_path}")
            
            # 转换视频为音频
            audio_file_path = await self.convert_video_to_audio(video_file_path)
            if not audio_file_path:
                return False
            
            # 上传音频文件到OSS获取公开访问URL
            audio_url = await self.oss_manager.upload_file(audio_file_path)
            if not audio_url:
                logger.error("音频文件上传失败，无法进行语音识别")
                return False
            
            # 执行语音识别
            recognized_text = await provider.recognize_audio(audio_url, language)
            if not recognized_text.strip():
                logger.warning("语音识别结果为空")
                return False
            
            # 生成字幕文件
            subtitle_file_path = await self.generate_subtitle_file(
                video_file_path, recognized_text, subtitle_format
            )
            
            if subtitle_file_path:
                logger.success(f"语音识别完成，字幕文件: {subtitle_file_path}")
                
                # 清理音频文件
                if delete_audio and os.path.exists(audio_file_path):
                    try:
                        os.remove(audio_file_path)
                        logger.info(f"已删除临时音频文件: {audio_file_path}")
                    except Exception as e:
                        logger.warning(f"删除音频文件失败: {e}")
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"语音识别处理异常: {e}")
            return False
    
    async def generate_subtitle_file(self, video_file_path: str, text: str, format_type: str = "srt") -> Optional[str]:
        """
        生成字幕文件
        
        Args:
            video_file_path: 视频文件路径  
            text: 识别出的文本
            format_type: 字幕格式 (srt, vtt, txt)
            
        Returns:
            字幕文件路径，失败返回None
        """
        try:
            video_dir = os.path.dirname(video_file_path)
            video_name = os.path.splitext(os.path.basename(video_file_path))[0]
            subtitle_file_path = os.path.join(video_dir, f"{video_name}.{format_type}")
            
            if format_type.lower() == "srt":
                # 生成SRT格式字幕
                subtitle_content = self.subtitle_generator.generate_srt(text)
            elif format_type.lower() == "vtt":
                # 生成VTT格式字幕
                subtitle_content = self.subtitle_generator.generate_vtt(text)
            elif format_type.lower() == "txt":
                # 生成纯文本格式
                subtitle_content = text
            else:
                logger.error(f"不支持的字幕格式: {format_type}")
                return None
            
            # 写入字幕文件
            with open(subtitle_file_path, "w", encoding="utf-8") as f:
                f.write(subtitle_content)
            
            logger.info(f"字幕文件生成成功: {subtitle_file_path}")
            return subtitle_file_path
            
        except Exception as e:
            logger.error(f"生成字幕文件异常: {e}")
            return None 