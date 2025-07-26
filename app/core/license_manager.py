"""
License Manager - 许可证管理系统
支持年度订阅激活、许可证验证、到期检查等功能
"""

import hashlib
import json
import os
import time
from datetime import datetime
from typing import Dict, Optional, Tuple
import platform
import requests

from ..utils.logger import logger


class LicenseManager:
    """许可证管理器"""
    
    def __init__(self, app):
        self.app = app
        self.config_path = os.path.join(app.run_path, "config", "license.json")
        self.machine_id = self._generate_machine_id()
        self.license_data = self._load_license()
        self.activation_api_url = None  # 后续配置激活接口URL
        
    def _generate_machine_id(self) -> str:
        """生成唯一的机器标识"""
        try:
            # 获取机器特征信息
            machine_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'node': platform.node(),
            }
            
            # 生成机器指纹
            machine_str = json.dumps(machine_info, sort_keys=True)
            machine_hash = hashlib.sha256(machine_str.encode()).hexdigest()
            
            return machine_hash[:16]  # 取前16位作为机器ID
        except Exception as e:
            logger.warning(f"生成机器ID失败，使用随机ID: {e}")
            import uuid
            return str(uuid.uuid4())[:16]
    
    def _load_license(self) -> Dict:
        """加载许可证数据"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"加载许可证失败: {e}")
        
        return {}
    
    def _save_license(self, license_data: Dict) -> bool:
        """保存许可证数据"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(license_data, f, ensure_ascii=False, indent=2)
            self.license_data = license_data
            return True
        except Exception as e:
            logger.error(f"保存许可证失败: {e}")
            return False
    
    def get_license_status(self) -> Dict:
        """获取许可证状态"""
        if not self.license_data:
            return {
                'status': 'unlicensed',
                'message': '未激活',
                'is_valid': False,
                'days_remaining': 0,
                'license_type': 'trial',
                'features': self._get_trial_features()
            }
        
        try:
            # 验证许可证
            if not self._verify_license():
                return {
                    'status': 'invalid',
                    'message': '许可证无效',
                    'is_valid': False,
                    'days_remaining': 0,
                    'license_type': 'trial',
                    'features': self._get_trial_features()
                }
            
            # 检查到期时间
            expire_time = self.license_data.get('expire_time', 0)
            current_time = time.time()
            
            if current_time > expire_time:
                return {
                    'status': 'expired',
                    'message': '许可证已过期',
                    'is_valid': False,
                    'days_remaining': 0,
                    'license_type': self.license_data.get('license_type', 'trial'),
                    'features': self._get_trial_features()
                }
            
            days_remaining = int((expire_time - current_time) / 86400)
            
            return {
                'status': 'active',
                'message': f'许可证有效，剩余 {days_remaining} 天',
                'is_valid': True,
                'days_remaining': days_remaining,
                'license_type': self.license_data.get('license_type', 'professional'),
                'features': self._get_licensed_features(),
                'user_info': {
                    'email': self.license_data.get('email', ''),
                    'company': self.license_data.get('company', ''),
                    'activated_time': self.license_data.get('activated_time', '')
                }
            }
            
        except Exception as e:
            logger.error(f"获取许可证状态失败: {e}")
            return {
                'status': 'error',
                'message': f'许可证检查失败: {e}',
                'is_valid': False,
                'days_remaining': 0,
                'license_type': 'trial',
                'features': self._get_trial_features()
            }
    
    def _verify_license(self) -> bool:
        """验证许可证"""
        try:
            # 检查必要字段
            required_fields = ['license_key', 'machine_id', 'expire_time', 'signature']
            for field in required_fields:
                if field not in self.license_data:
                    logger.error(f"许可证缺少必要字段: {field}")
                    return False
            
            # 验证机器ID
            if self.license_data['machine_id'] != self.machine_id:
                logger.error("机器ID不匹配")
                return False
            
            # 验证签名
            signature_data = {
                'license_key': self.license_data['license_key'],
                'machine_id': self.license_data['machine_id'],
                'expire_time': self.license_data['expire_time'],
                'license_type': self.license_data.get('license_type', 'professional')
            }
            
            expected_signature = self._generate_signature(signature_data)
            if self.license_data['signature'] != expected_signature:
                logger.error("许可证签名验证失败")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"许可证验证失败: {e}")
            return False
    
    def _generate_signature(self, data: Dict) -> str:
        """生成签名"""
        # 将数据转换为字符串并排序
        data_str = json.dumps(data, sort_keys=True)
        # 添加盐值
        salted_data = f"streamvault_{data_str}_license"
        # 生成SHA256哈希
        return hashlib.sha256(salted_data.encode()).hexdigest()
    
    def _get_trial_features(self) -> Dict:
        """获取试用版功能限制"""
        return {
            'max_recordings': 5,
            'max_storage_gb': 10,
            'speech_recognition': False,
            'advanced_features': False,
            'api_access': False,
        }
    
    def _get_licensed_features(self) -> Dict:
        """获取授权版功能"""
        license_type = self.license_data.get('license_type', 'professional')
        
        if license_type == 'professional':
            return {
                'max_recordings': 100,
                'max_storage_gb': 500,
                'speech_recognition': True,
                'advanced_features': True,
                'api_access': True,
            }
        elif license_type == 'enterprise':
            return {
                'max_recordings': -1,  # 无限制
                'max_storage_gb': -1,  # 无限制
                'speech_recognition': True,
                'advanced_features': True,
                'api_access': True,
            }
        else:
            return self._get_trial_features()
    
    async def activate_license(self, license_key: str, email: str = "", company: str = "") -> Tuple[bool, str]:
        """激活许可证"""
        try:
            logger.info(f"开始激活许可证: {license_key[:8]}...")
            
            # 准备激活请求数据
            activation_data = {
                'license_key': license_key,
                'machine_id': self.machine_id,
                'email': email,
                'company': company,
                'platform': platform.platform(),
                'timestamp': int(time.time())
            }
            
            # 如果配置了激活接口，调用远程激活
            if self.activation_api_url:
                success, message, license_data = await self._activate_remote(activation_data)
            else:
                # 本地激活（用于测试）
                success, message, license_data = self._activate_local(activation_data)
            
            if success and license_data:
                # 保存许可证
                if self._save_license(license_data):
                    logger.info("许可证激活成功")
                    return True, "激活成功"
                else:
                    return False, "保存许可证失败"
            else:
                return False, message
                
        except Exception as e:
            logger.error(f"激活许可证失败: {e}")
            return False, f"激活失败: {e}"
    
    async def _activate_remote(self, activation_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """远程激活"""
        try:
            # 发送激活请求
            response = requests.post(
                self.activation_api_url,
                json=activation_data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return True, result.get('message', '激活成功'), result.get('license_data')
                else:
                    return False, result.get('message', '激活失败'), None
            else:
                return False, f"激活服务器错误: {response.status_code}", None
                
        except requests.RequestException as e:
            logger.error(f"远程激活请求失败: {e}")
            return False, f"网络请求失败: {e}", None
        except Exception as e:
            logger.error(f"远程激活失败: {e}")
            return False, f"激活失败: {e}", None
    
    def _activate_local(self, activation_data: Dict) -> Tuple[bool, str, Optional[Dict]]:
        """本地激活（用于测试和开发）"""
        try:
            license_key = activation_data['license_key']
            
            # 简单的许可证密钥验证（实际应该由服务器验证）
            if len(license_key) < 16:
                return False, "许可证密钥格式无效", None
            
            # 生成测试许可证数据
            current_time = time.time()
            expire_time = current_time + (365 * 24 * 60 * 60)  # 1年后到期
            
            license_data = {
                'license_key': license_key,
                'machine_id': activation_data['machine_id'],
                'email': activation_data.get('email', ''),
                'company': activation_data.get('company', ''),
                'license_type': 'professional',
                'activated_time': datetime.now().isoformat(),
                'expire_time': expire_time,
            }
            
            # 生成签名
            signature_data = {
                'license_key': license_data['license_key'],
                'machine_id': license_data['machine_id'],
                'expire_time': license_data['expire_time'],
                'license_type': license_data['license_type']
            }
            license_data['signature'] = self._generate_signature(signature_data)
            
            return True, "本地激活成功", license_data
            
        except Exception as e:
            logger.error(f"本地激活失败: {e}")
            return False, f"本地激活失败: {e}", None
    
    def deactivate_license(self) -> bool:
        """停用许可证"""
        try:
            if os.path.exists(self.config_path):
                os.remove(self.config_path)
            self.license_data = {}
            logger.info("许可证已停用")
            return True
        except Exception as e:
            logger.error(f"停用许可证失败: {e}")
            return False
    
    def check_feature_access(self, feature_name: str) -> bool:
        """检查功能访问权限"""
        status = self.get_license_status()
        if not status['is_valid']:
            return False
        
        features = status.get('features', {})
        return features.get(feature_name, False)
    
    def set_activation_api_url(self, url: str):
        """设置激活API地址"""
        self.activation_api_url = url
        logger.info(f"激活API地址已设置: {url}")
    
    def get_machine_id(self) -> str:
        """获取机器ID"""
        return self.machine_id 