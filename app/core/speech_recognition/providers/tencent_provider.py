"""
腾讯云语音识别服务商
基于官方SDK tencentcloud-sdk-python-asr实现
"""

import asyncio
import json
import time
from typing import Optional

from ....utils.logger import logger
from ..base_provider import BaseSpeechProvider

try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.asr.v20190614 import asr_client, models
    TENCENT_SDK_AVAILABLE = True
except ImportError:
    TENCENT_SDK_AVAILABLE = False
    logger.warning("腾讯云SDK未安装，请运行: pip install tencentcloud-sdk-python-asr")


class TencentSpeechProvider(BaseSpeechProvider):
    """腾讯云语音识别服务商"""
    
    def validate_config(self) -> None:
        """验证腾讯云配置信息"""
        if not TENCENT_SDK_AVAILABLE:
            raise ValueError("腾讯云SDK未安装，请运行: pip install tencentcloud-sdk-python-asr==3.0.1394")
        
        required_keys = ["secret_id", "secret_key"]
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"腾讯云语音识别缺少必要配置: {key}")
    
    @property
    def provider_name(self) -> str:
        return "tencent"
    
    @property
    def supported_formats(self) -> list[str]:
        return ["mp3", "wav", "pcm", "m4a", "flac", "opus", "amr"]
    
    def _get_config_value(self, key: str, default=None):
        """从配置获取值"""
        return self.config.get(key, default)
    
    def _create_client(self) -> "asr_client.AsrClient":
        """创建腾讯云ASR客户端"""
        try:
            # 实例化一个认证对象
            cred = credential.Credential(
                self.config["secret_id"],
                self.config["secret_key"]
            )
            
            # 实例化一个http选项
            httpProfile = HttpProfile()
            httpProfile.endpoint = "asr.tencentcloudapi.com"
            
            # 实例化一个client选项
            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            
            # 实例化要请求产品的client对象
            region = self._get_config_value("region", "")  # 地域参数，可为空
            client = asr_client.AsrClient(cred, region, clientProfile)
            
            return client
            
        except Exception as e:
            logger.error(f"创建腾讯云ASR客户端失败: {e}")
            raise
    
    async def _create_recognition_task(self, client: "asr_client.AsrClient", audio_url: str, language: str) -> Optional[int]:
        """创建语音识别任务"""
        try:
            # 实例化一个请求对象
            req = models.CreateRecTaskRequest()
            
            # 从配置获取参数
            engine_model_type_zh = self._get_config_value("engine_model_type_zh", "16k_zh")
            engine_model_type_en = self._get_config_value("engine_model_type_en", "16k_en")
            channel_num = self._get_config_value("channel_num", 1)
            res_text_format = self._get_config_value("res_text_format", 0)
            source_type = self._get_config_value("source_type", 0)  # 0表示音频URL
            
            # 构建请求参数
            params = {
                "EngineModelType": engine_model_type_zh if language == "zh" else engine_model_type_en,
                "ChannelNum": channel_num,
                "ResTextFormat": res_text_format,
                "SourceType": source_type,
                "Url": audio_url
            }
            
            req.from_json_string(json.dumps(params))
            
            logger.info(f"创建腾讯云识别任务，参数: {params}")
            
            # 返回的resp是一个CreateRecTaskResponse的实例，与请求对象对应
            resp = client.CreateRecTask(req)
            result = json.loads(resp.to_json_string())
            
            logger.info(f"任务创建响应: {result}")
            
            if "Data" in result and "TaskId" in result["Data"]:
                task_id = result["Data"]["TaskId"]
                logger.info(f"腾讯云识别任务创建成功，任务ID: {task_id}")
                return task_id
            else:
                logger.error(f"任务创建失败，响应: {result}")
                return None
                
        except TencentCloudSDKException as err:
            logger.error(f"腾讯云SDK异常: {err}")
            return None
        except Exception as e:
            logger.error(f"创建识别任务失败: {e}")
            return None
    
    async def _get_recognition_result(self, client: "asr_client.AsrClient", task_id: int) -> Optional[str]:
        """轮询获取识别结果"""
        try:
            max_wait_time = self._get_config_value("max_wait_time", 300)
            poll_interval = self._get_config_value("poll_interval", 5)
            start_time = time.time()
            
            logger.info(f"开始轮询任务结果，任务ID: {task_id}")
            
            while time.time() - start_time < max_wait_time:
                try:
                    # 实例化一个请求对象
                    req = models.DescribeTaskStatusRequest()
                    
                    # 构建查询参数
                    params = {
                        "TaskId": task_id
                    }
                    
                    req.from_json_string(json.dumps(params))
                    
                    # 返回的resp是一个DescribeTaskStatusResponse的实例，与请求对象对应
                    resp = client.DescribeTaskStatus(req)
                    result = json.loads(resp.to_json_string())
                    
                    logger.debug(f"查询结果响应: {result}")
                    
                    if "Data" in result:
                        data = result["Data"]
                        status = data.get("StatusStr", "")
                        
                        logger.info(f"腾讯云任务状态: {status}")
                        
                        if status == "success":
                            # 任务完成，提取结果
                            logger.info("腾讯云识别任务成功完成")
                            return self._extract_text_from_result(data)
                        elif status == "failed":
                            error_msg = data.get("ErrorMsg", "未知错误")
                            logger.error(f"腾讯云识别任务失败: {error_msg}")
                            return None
                        elif status in ["waiting", "doing"]:
                            # 任务进行中，继续等待
                            logger.info(f"任务进行中，状态: {status}，等待 {poll_interval} 秒后重试")
                            await asyncio.sleep(poll_interval)
                            continue
                        else:
                            logger.warning(f"未知任务状态: {status}")
                            await asyncio.sleep(poll_interval)
                            continue
                    else:
                        logger.error(f"查询响应格式异常: {result}")
                        await asyncio.sleep(poll_interval)
                        continue
                        
                except TencentCloudSDKException as err:
                    logger.error(f"查询任务状态时SDK异常: {err}")
                    await asyncio.sleep(poll_interval)
                    continue
                except Exception as e:
                    logger.error(f"查询任务状态失败: {e}")
                    await asyncio.sleep(poll_interval)
                    continue
            
            logger.error(f"腾讯云语音识别超时 ({max_wait_time}秒)")
            return None
            
        except Exception as e:
            logger.error(f"获取识别结果失败: {e}")
            return None
    
    def _extract_text_from_result(self, data: dict) -> str:
        """从识别结果中提取文本"""
        try:
            # 腾讯云返回的Result字段是字符串格式，包含时间戳
            # 格式如: '[0:3.600,0:9.002]  那你将他带来，是想借机对她如何？\n'
            result = data.get("Result", "")
            
            if not result:
                logger.warning("腾讯云识别结果为空")
                return ""
            
            # 如果Result是字符串（实际情况）
            if isinstance(result, str):
                # 移除时间戳标记，格式为 [开始时间,结束时间]
                import re
                # 匹配时间戳模式: [数字:数字.数字,数字:数字.数字]
                text = re.sub(r'\[\d+:\d+\.\d+,\d+:\d+\.\d+\]\s*', '', result)
                text = text.strip()
                logger.info(f"提取的文本内容: {text}")
                return text
            
            # 如果Result是数组（备用处理）
            elif isinstance(result, list):
                texts = []
                for item in result:
                    if isinstance(item, dict):
                        text = item.get("VoiceTextStr", "").strip()
                        if text:
                            texts.append(text)
                    elif isinstance(item, str):
                        # 处理字符串类型的项目
                        text = re.sub(r'\[\d+:\d+\.\d+,\d+:\d+\.\d+\]\s*', '', item)
                        text = text.strip()
                        if text:
                            texts.append(text)
                
                final_text = " ".join(texts)
                logger.info(f"提取的文本内容: {final_text}")
                return final_text
            
            else:
                logger.error(f"未知的Result格式: {type(result)}")
                return ""
            
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            return ""
    
    async def recognize_audio(self, audio_url: str, language: str = "zh") -> str:
        """
        使用腾讯云API识别音频
        
        Args:
            audio_url: 音频文件的公开访问URL
            language: 识别语言 (zh/en)
            
        Returns:
            识别出的文本内容
        """
        try:
            logger.info(f"开始腾讯云语音识别: {audio_url}")
            
            # 验证配置
            self.validate_config()
            
            # 创建腾讯云客户端
            client = self._create_client()
            
            # 创建识别任务
            task_id = await self._create_recognition_task(client, audio_url, language)
            if task_id is None:
                return ""
            
            # 轮询获取识别结果
            result_text = await self._get_recognition_result(client, task_id)
            
            if result_text is None:
                logger.error("腾讯云语音识别失败")
                return ""
            
            logger.info(f"腾讯云语音识别完成，识别出 {len(result_text)} 个字符")
            return result_text
            
        except Exception as e:
            logger.error(f"腾讯云语音识别发生错误: {e}")
            return ""