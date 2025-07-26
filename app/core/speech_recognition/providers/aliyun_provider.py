import asyncio
import json
import time
from typing import Dict, Any, Optional

from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from ....utils.logger import logger
from ..base_provider import BaseSpeechProvider


class AliyunSpeechProvider(BaseSpeechProvider):
    """阿里云语音识别服务商"""
    
    def validate_config(self) -> None:
        """验证阿里云配置信息"""
        required_keys = ["access_key_id", "access_key_secret", "app_key"]
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"阿里云语音识别缺少必要配置: {key}")
    
    @property
    def provider_name(self) -> str:
        return "aliyun"
    
    @property
    def supported_formats(self) -> list[str]:
        return ["mp3", "wav", "pcm", "opus", "amr", "m4a"]
    
    def _get_config_value(self, key: str, default=None):
        """从配置获取值"""
        return self.config.get(key, default)
    
    def _create_client(self) -> AcsClient:
        """创建阿里云客户端"""
        region_id = self._get_config_value("region_id")
        if not region_id:
            raise ValueError("阿里云语音识别缺少必要配置: region_id")
        
        return AcsClient(
            self.config["access_key_id"],
            self.config["access_key_secret"],
            region_id
        )
    
    async def _submit_recognition_task(self, client: AcsClient, file_url: str) -> Optional[str]:
        """提交语音识别任务"""
        try:
            # 从配置获取参数
            domain = self._get_config_value("domain")
            api_version = self._get_config_value("api_version")
            product = self._get_config_value("product")
            
            if not all([domain, api_version, product]):
                raise ValueError("阿里云语音识别缺少必要配置: domain, api_version, product")
            
            # 创建提交任务请求
            post_request = CommonRequest()
            post_request.set_domain(domain)
            post_request.set_version(api_version)
            post_request.set_product(product)
            post_request.set_action_name("SubmitTask")
            post_request.set_method('POST')
            
            # 构建任务参数
            task = {
                "appkey": self.config["app_key"],
                "file_link": file_url,
                "version": self._get_config_value("version"),
                "enable_words": self._get_config_value("enable_words", False),
            }
            
            # 可选参数
            if self._get_config_value("auto_split", False):
                task["auto_split"] = True
            
            task_json = json.dumps(task)
            logger.info(f"提交阿里云语音识别任务: {task_json}")
            
            post_request.add_body_params("Task", task_json)
            
            # 提交请求
            response = client.do_action_with_exception(post_request)
            response_data = json.loads(response)
            
            logger.info(f"任务提交响应: {response_data}")
            
            status_text = response_data.get("StatusText")
            if status_text == "SUCCESS":
                task_id = response_data.get("TaskId")
                logger.info(f"语音识别任务提交成功，任务ID: {task_id}")
                return task_id
            else:
                logger.error(f"语音识别任务提交失败: {response_data}")
                return None
                
        except ServerException as e:
            logger.error(f"阿里云服务器错误: {e}")
            return None
        except ClientException as e:
            logger.error(f"阿里云客户端错误: {e}")
            return None
        except Exception as e:
            logger.error(f"提交识别任务失败: {e}")
            return None
    
    async def _get_recognition_result(self, client: AcsClient, task_id: str) -> Optional[str]:
        """获取语音识别结果"""
        try:
            # 从配置获取参数
            domain = self._get_config_value("domain")
            api_version = self._get_config_value("api_version")
            product = self._get_config_value("product")
            max_wait_time = self._get_config_value("max_wait_time", 300)
            poll_interval = self._get_config_value("poll_interval", 10)
            
            if not all([domain, api_version, product]):
                raise ValueError("阿里云语音识别缺少必要配置: domain, api_version, product")
            
            # 创建查询结果请求
            get_request = CommonRequest()
            get_request.set_domain(domain)
            get_request.set_version(api_version)
            get_request.set_product(product)
            get_request.set_action_name("GetTaskResult")
            get_request.set_method('GET')
            get_request.add_query_param("TaskId", task_id)
            
            start_time = time.time()
            
            # 轮询查询结果
            while time.time() - start_time < max_wait_time:
                try:
                    response = client.do_action_with_exception(get_request)
                    response_data = json.loads(response)
                    
                    logger.info(f"查询结果响应: {response_data}")
                    
                    status_text = response_data.get("StatusText")
                    
                    if status_text in ["RUNNING", "QUEUEING"]:
                        logger.info(f"任务状态: {status_text}，等待 {poll_interval} 秒后重试...")
                        await asyncio.sleep(poll_interval)
                        continue
                    elif status_text == "SUCCESS":
                        logger.info("语音识别成功完成")
                        result = response_data.get("Result")
                        return self._extract_text_from_result(result)
                    elif status_text == "SUCCESS_WITH_NO_VALID_FRAGMENT":
                        logger.warning("识别成功但没有有效的语音片段")
                        return ""
                    else:
                        logger.error(f"语音识别失败，状态: {status_text}")
                        return None
                        
                except ServerException as e:
                    logger.error(f"查询结果时服务器错误: {e}")
                    await asyncio.sleep(poll_interval)
                except ClientException as e:
                    logger.error(f"查询结果时客户端错误: {e}")
                    await asyncio.sleep(poll_interval)
            
            logger.error(f"语音识别超时 ({max_wait_time}秒)")
            return None
            
        except Exception as e:
            logger.error(f"获取识别结果失败: {e}")
            return None
    
    def _extract_text_from_result(self, result_data) -> str:
        """从识别结果中提取文本"""
        try:
            if not result_data:
                return ""
            
            # 检查result_data的类型
            if isinstance(result_data, str):
                # 如果是字符串，需要解析JSON
                result = json.loads(result_data)
            elif isinstance(result_data, dict):
                # 如果已经是字典，直接使用
                result = result_data
            else:
                logger.error(f"未知的result_data类型: {type(result_data)}")
                return ""
            
            # 提取句子文本
            sentences = result.get("Sentences", [])
            if not sentences:
                logger.warning("识别结果中没有Sentences")
                return ""
            
            # 拼接所有句子的文本
            texts = []
            for sentence in sentences:
                text = sentence.get("Text", "").strip()
                if text:
                    texts.append(text)
            
            final_text = " ".join(texts)
            logger.info(f"提取的文本内容: {final_text}")
            
            return final_text
            
        except json.JSONDecodeError as e:
            logger.error(f"解析识别结果JSON失败: {e}")
            return ""
        except Exception as e:
            logger.error(f"提取文本失败: {e}")
            return ""
    
    async def recognize_audio(self, audio_url: str, language: str = "zh") -> str:
        """
        使用阿里云API识别音频
        
        Args:
            audio_url: 音频文件的公开访问URL
            language: 识别语言 (zh/en)
            
        Returns:
            识别出的文本内容
        """
        try:
            logger.info(f"开始阿里云语音识别: {audio_url}")
            
            # 验证配置
            self.validate_config()
            
            # 创建阿里云客户端
            client = self._create_client()
            
            # 提交识别任务
            task_id = await self._submit_recognition_task(client, audio_url)
            if not task_id:
                return ""
            
            # 获取识别结果
            result_text = await self._get_recognition_result(client, task_id)
            
            if result_text is None:
                logger.error("阿里云语音识别失败")
                return ""
            
            logger.info(f"阿里云语音识别完成，识别出 {len(result_text)} 个字符")
            return result_text
            
        except Exception as e:
            logger.error(f"阿里云语音识别发生错误: {e}")
            return ""