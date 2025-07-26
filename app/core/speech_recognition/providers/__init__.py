"""
语音识别服务商模块
"""

# 语音识别提供商
from ..base_provider import BaseSpeechProvider
from .aliyun_provider import AliyunSpeechProvider
from .tencent_provider import TencentSpeechProvider

__all__ = [
    "BaseSpeechProvider",
    "AliyunSpeechProvider", 
    "TencentSpeechProvider",
] 