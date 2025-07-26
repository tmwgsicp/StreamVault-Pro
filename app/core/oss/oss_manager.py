"""
对象存储管理器
支持阿里云、腾讯云OSS服务
"""

import os
import uuid
from abc import ABC, abstractmethod
from typing import Optional

from ...utils.logger import logger


class BaseOSSProvider(ABC):
    """OSS服务商基类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.validate_config()
    
    @abstractmethod
    def validate_config(self):
        """验证配置信息"""
        pass
        
    @abstractmethod 
    def get_provider_name(self) -> str:
        """获取服务商名称"""
        pass
    
    @abstractmethod
    async def upload_file(self, local_file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """上传文件到OSS"""
        pass
    
    @abstractmethod
    async def delete_file(self, object_key: str) -> bool:
        """删除OSS文件"""
        pass


class AliyunOSSProvider(BaseOSSProvider):
    """阿里云OSS服务商"""
    
    def __init__(self, config: dict):
        try:
            import oss2
            self.oss2 = oss2
            self.OssError = oss2.exceptions.OssError
        except ImportError:
            raise ImportError("请安装阿里云OSS SDK: pip install oss2")
        
        super().__init__(config)
        
        # 创建OSS认证和Bucket对象
        auth = oss2.Auth(self.config["access_key_id"], self.config["access_key_secret"])
        self.bucket = oss2.Bucket(auth, self.config["endpoint"], self.config["bucket_name"])
    
    def validate_config(self):
        """验证阿里云配置信息"""
        required_keys = ["access_key_id", "access_key_secret", "endpoint", "bucket_name"]
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"阿里云OSS缺少必要配置: {key}")
    
    def get_provider_name(self) -> str:
        return "aliyun"
    
    async def upload_file(self, local_file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """上传文件到阿里云OSS"""
        try:
            if not os.path.exists(local_file_path):
                logger.error(f"文件不存在: {local_file_path}")
                return None
            
            # 生成对象键名
            if object_key is None:
                file_ext = os.path.splitext(local_file_path)[1]
                object_key = f"speech_recognition/{uuid.uuid4().hex}{file_ext}"
            
            logger.info(f"开始上传文件到阿里云OSS: {local_file_path} -> {object_key}")
            
            with open(local_file_path, 'rb') as fileobj:
                result = self.bucket.put_object(object_key, fileobj)
            
            if result.status == 200:
                file_url = f"https://{self.config['bucket_name']}.{self.config['endpoint']}/{object_key}"
                logger.info(f"阿里云OSS上传成功: {file_url}")
                return file_url
            else:
                logger.error(f"阿里云OSS上传失败，状态码: {result.status}")
                return None
                
        except self.OssError as e:
            logger.error(f"阿里云OSS错误: {e}")
            return None
        except Exception as e:
            logger.error(f"上传文件到阿里云OSS时发生错误: {e}")
            return None
    
    async def delete_file(self, object_key: str) -> bool:
        """删除阿里云OSS文件"""
        try:
            result = self.bucket.delete_object(object_key)
            if result.status == 204:
                logger.info(f"阿里云OSS文件删除成功: {object_key}")
                return True
            else:
                logger.error(f"阿里云OSS文件删除失败，状态码: {result.status}")
                return False
        except Exception as e:
            logger.error(f"删除阿里云OSS文件时发生错误: {e}")
            return False


class TencentOSSProvider(BaseOSSProvider):
    """腾讯云COS服务商"""
    
    def __init__(self, config: dict):
        try:
            from qcloud_cos import CosConfig, CosS3Client
            from qcloud_cos.cos_exception import CosException
            self.CosConfig = CosConfig
            self.CosS3Client = CosS3Client
            self.CosException = CosException
        except ImportError:
            raise ImportError("请安装腾讯云COS SDK: pip install cos-python-sdk-v5")
        
        super().__init__(config)
        
        # 创建COS客户端
        cos_config = CosConfig(
            Region=self.config["region"],
            SecretId=self.config["secret_id"],
            SecretKey=self.config["secret_key"]
        )
        self.client = CosS3Client(cos_config)
    
    def validate_config(self):
        """验证腾讯云配置信息"""
        required_keys = ["secret_id", "secret_key", "region", "bucket_name"]
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"腾讯云COS缺少必要配置: {key}")
    
    def get_provider_name(self) -> str:
        return "tencent"
    
    async def upload_file(self, local_file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """上传文件到腾讯云COS"""
        try:
            if not os.path.exists(local_file_path):
                logger.error(f"文件不存在: {local_file_path}")
                return None
            
            # 生成对象键名
            if object_key is None:
                file_ext = os.path.splitext(local_file_path)[1]
                object_key = f"speech_recognition/{uuid.uuid4().hex}{file_ext}"
            
            logger.info(f"开始上传文件到腾讯云COS: {local_file_path} -> {object_key}")
            
            with open(local_file_path, 'rb') as fp:
                response = self.client.put_object(
                    Bucket=self.config["bucket_name"],
                    Body=fp,
                    Key=object_key,
                    StorageClass='STANDARD'
                )
            
            if response:
                file_url = f"https://{self.config['bucket_name']}.cos.{self.config['region']}.myqcloud.com/{object_key}"
                logger.info(f"腾讯云COS上传成功: {file_url}")
                return file_url
            else:
                logger.error("腾讯云COS上传失败")
                return None
                
        except self.CosException as e:
            logger.error(f"腾讯云COS错误: {e}")
            return None
        except Exception as e:
            logger.error(f"上传文件到腾讯云COS时发生错误: {e}")
            return None
    
    async def delete_file(self, object_key: str) -> bool:
        """删除腾讯云COS文件"""
        try:
            response = self.client.delete_object(
                Bucket=self.config["bucket_name"],
                Key=object_key
            )
            if response:
                logger.info(f"腾讯云COS文件删除成功: {object_key}")
                return True
            else:
                logger.error("腾讯云COS文件删除失败")
                return False
        except Exception as e:
            logger.error(f"删除腾讯云COS文件时发生错误: {e}")
            return False


class OSSManager:
    """OSS管理器"""
    
    def __init__(self, settings):
        self.settings = settings
        self.providers = {
            "aliyun": AliyunOSSProvider,
            "tencent": TencentOSSProvider,
        }
        
        # 定义各提供商所需的配置键
        self.provider_config_keys = {
            "aliyun": ["access_key_id", "access_key_secret", "endpoint", "bucket_name"],
            "tencent": ["secret_id", "secret_key", "region", "bucket_name"],
        }
        
        self.current_provider = None
    
    def _get_provider_config(self, provider_name: str) -> dict:
        """获取指定提供商的配置"""
        config_keys = self.provider_config_keys.get(provider_name, [])
        config = {}
        
        for key in config_keys:
            config_key = f"oss_{provider_name}_{key}"
            config[key] = self.settings.default_config.get(config_key, "")
        
        return config
    
    def get_provider(self) -> Optional[BaseOSSProvider]:
        """获取当前OSS提供商实例"""
        try:
            provider_name = self.settings.default_config.get("oss_provider", "aliyun")
            
            if provider_name not in self.providers:
                logger.error(f"不支持的OSS提供商: {provider_name}")
                return None
            
            # 获取提供商配置
            config = self._get_provider_config(provider_name)
            
            # 创建提供商实例
            provider_class = self.providers[provider_name]
            self.current_provider = provider_class(config)
            
            return self.current_provider
            
        except Exception as e:
            logger.error(f"获取OSS提供商失败: {e}")
            return None
    
    async def upload_file(self, local_file_path: str, object_key: Optional[str] = None) -> Optional[str]:
        """上传文件到OSS"""
        provider = self.get_provider()
        if provider is None:
            return None
        
        return await provider.upload_file(local_file_path, object_key)
    
    async def delete_file(self, object_key: str) -> bool:
        """删除OSS文件"""
        provider = self.get_provider()
        if provider is None:
            return False
        
        return await provider.delete_file(object_key)
    
    def is_enabled(self) -> bool:
        """检查OSS功能是否启用"""
        return self.settings.default_config.get("oss_enabled", False)
    
    def validate_current_provider(self) -> bool:
        """验证当前提供商配置是否完整"""
        try:
            provider = self.get_provider()
            return provider is not None
        except Exception as e:
            logger.error(f"验证OSS提供商配置失败: {e}")
            return False 