import abc
from typing import Optional, Dict, Any


class BaseSpeechProvider(abc.ABC):
    """语音识别服务商基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化语音识别服务商
        
        Args:
            config: 服务商配置信息
        """
        self.config = config
        self.validate_config()
    
    @abc.abstractmethod
    def validate_config(self) -> None:
        """验证配置信息是否完整"""
        pass
    
    @abc.abstractmethod
    async def recognize_audio(self, audio_file_path: str, language: str = "zh") -> str:
        """
        识别音频文件中的语音内容
        
        Args:
            audio_file_path: 音频文件路径
            language: 识别语言，默认为中文
            
        Returns:
            识别出的文本内容
        """
        pass
    
    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """服务商名称"""
        pass
    
    @property 
    @abc.abstractmethod
    def supported_formats(self) -> list[str]:
        """支持的音频格式"""
        pass
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        file_extension = file_path.lower().split('.')[-1]
        return file_extension in self.supported_formats 