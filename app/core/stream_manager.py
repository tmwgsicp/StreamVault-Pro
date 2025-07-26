import asyncio
import os
import shutil
import subprocess
import time
from datetime import datetime
from typing import Any

from ..models.recording_status_model import RecordingStatus
from ..models.video_quality_model import VideoQuality
from ..process_manager import BackgroundService
from ..utils import utils
from ..utils.logger import logger
from . import ffmpeg_builders, platform_handlers
from .platform_handlers import StreamData


class LiveStreamRecorder:
    DEFAULT_SEGMENT_TIME = "1800"
    DEFAULT_SAVE_FORMAT = "mp4"
    DEFAULT_QUALITY = VideoQuality.OD

    def __init__(self, app, recording, recording_info):
        self.app = app
        self.settings = app.settings
        self.recording = recording
        self.recording_info = recording_info
        self.subprocess_start_info = app.subprocess_start_up_info

        self.default_config = self.settings.default_config
        self.account_config = self.settings.accounts_config
        self.platform_key = self._get_info("platform_key")
        self.cookies = self.settings.cookies_config.get(self.platform_key)

        self.platform = self._get_info("platform")
        self.live_url = self._get_info("live_url")
        self.output_dir = self._get_info("output_dir")
        self.segment_record = self._get_info("segment_record", default=False)
        self.segment_time = self._get_info("segment_time", default=self.DEFAULT_SEGMENT_TIME)
        self.quality = self._get_info("quality", default=self.DEFAULT_QUALITY)
        self.save_format = self._get_info("save_format", default=self.DEFAULT_SAVE_FORMAT).lower()
        self.proxy = self.is_use_proxy()
        os.makedirs(self.output_dir, exist_ok=True)
        self.app.language_manager.add_observer(self)
        self._ = {}
        self.load()

    def load(self):
        language = self.app.language_manager.language
        for key in ("recording_manager", "stream_manager"):
            self._.update(language.get(key, {}))

    def _get_info(self, key: str, default: Any = None):
        return self.recording_info.get(key, default) or default

    def is_use_proxy(self):
        default_proxy_platform = self.default_config.get("default_platform_with_proxy", "")
        proxy_list = default_proxy_platform.replace("，", ",").replace(" ", "").split(",")
        if self.default_config.get("enable_proxy") and self.platform_key in proxy_list:
            self.proxy = self.default_config.get("proxy_address")
            return self.proxy

    def _get_filename(self, stream_info: StreamData) -> str:
        live_title = None
        stream_info.title = utils.clean_name(stream_info.title, None)
        if self.default_config.get("filename_includes_title") and stream_info.title:
            stream_info.title = self._clean_and_truncate_title(stream_info.title)
            live_title = stream_info.title

        if self.recording.streamer_name and self.recording.streamer_name != self._["live_room"]:
            stream_info.anchor_name = self.recording.streamer_name
        else:
            stream_info.anchor_name = utils.clean_name(stream_info.anchor_name, self._["live_room"])

        now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        full_filename = "_".join([i for i in (stream_info.anchor_name, live_title, now) if i])
        return full_filename

    def _get_output_dir(self, stream_info: StreamData) -> str:
        if self.recording.recording_dir and self.default_config.get("folder_name_time"):
            current_date = datetime.today().strftime("%Y-%m-%d")
            if current_date not in self.recording.recording_dir:
                self.recording.recording_dir = None
                
        if self.recording.recording_dir:
            return self.recording.recording_dir

        now = datetime.today().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = self.output_dir.rstrip("/").rstrip("\\")
        if self.default_config.get("folder_name_platform"):
            output_dir = os.path.join(output_dir, stream_info.platform)
        if self.default_config.get("folder_name_author"):
            output_dir = os.path.join(output_dir, stream_info.anchor_name)
        if self.default_config.get("folder_name_time"):
            output_dir = os.path.join(output_dir, now[:10])
        if self.default_config.get("folder_name_title") and stream_info.title:
            live_title = self._clean_and_truncate_title(stream_info.title)
            if self.default_config.get("folder_name_time"):
                output_dir = os.path.join(output_dir, f"{live_title}_{stream_info.anchor_name}")
            else:
                output_dir = os.path.join(output_dir, f"{now[:10]}_{live_title}")
        os.makedirs(output_dir, exist_ok=True)
        self.recording.recording_dir = output_dir
        self.app.page.run_task(self.app.record_manager.persist_recordings)
        return output_dir

    def _get_save_path(self, filename: str) -> str:
        suffix = self.save_format
        suffix = "_%03d." + suffix if self.segment_record and self.save_format != "flv" else "." + suffix
        save_file_path = os.path.join(self.output_dir, filename + suffix).replace(" ", "_")
        return save_file_path.replace("\\", "/")

    @staticmethod
    def _clean_and_truncate_title(title: str) -> str | None:
        if not title:
            return None
        cleaned_title = title[:30].replace("，", ",").replace(" ", "")
        return cleaned_title

    def _get_record_url(self, url: str):
        http_record_list = ["shopee"]
        if self.platform_key in http_record_list:
            url = url.replace("https://", "http://")
        if self.default_config.get("force_https_recording") and url.startswith("http://"):
            url = url.replace("http://", "https://")
        return url

    async def fetch_stream(self) -> StreamData:
        logger.info(f"Live URL: {self.live_url}")
        logger.info(f"Use Proxy: {self.proxy or None}")
        self.recording.use_proxy = bool(self.proxy)
        handler = platform_handlers.get_platform_handler(
            live_url=self.live_url,
            proxy=self.proxy,
            cookies=self.cookies,
            record_quality=self.quality,
            platform=self.platform,
            username=self.account_config.get(self.platform_key, {}).get("username"),
            password=self.account_config.get(self.platform_key, {}).get("password"),
            account_type=self.account_config.get(self.platform_key, {}).get("account_type")
        )
        stream_info = await handler.get_stream_info(self.live_url)
        self.recording.is_checking = False
        return stream_info

    async def start_recording(self, stream_info: StreamData):
        """
        Construct ffmpeg recording parameters and start recording
        """

        filename = self._get_filename(stream_info)
        self.output_dir = self._get_output_dir(stream_info)
        save_path = self._get_save_path(filename)
        logger.info(f"Save Path: {save_path}")
        self.recording.recording_dir = os.path.dirname(save_path)
        os.makedirs(self.recording.recording_dir, exist_ok=True)
        record_url = self._get_record_url(stream_info.record_url)

        ffmpeg_builder = ffmpeg_builders.create_builder(
            self.save_format,
            record_url=record_url,
            proxy=self.proxy,
            segment_record=self.segment_record,
            segment_time=self.segment_time,
            full_path=save_path,
            headers=self.get_headers_params(record_url, self.platform_key)
        )
        ffmpeg_command = ffmpeg_builder.build_command()
        self.app.page.run_task(
            self.start_ffmpeg,
            stream_info.anchor_name,
            self.live_url,
            stream_info.record_url,
            ffmpeg_command,
            self.save_format,
            self.default_config.get("custom_script_command")
        )

    async def start_ffmpeg(
        self,
        record_name: str,
        live_url: str,
        record_url: str,
        ffmpeg_command: list,
        save_type: str,
        script_command: str | None = None
    ) -> bool:
        """
        The child process executes ffmpeg for recording
        """

        try:
            save_file_path = ffmpeg_command[-1]

            process = await asyncio.create_subprocess_exec(
                *ffmpeg_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                startupinfo=self.subprocess_start_info
            )

            self.app.add_ffmpeg_process(process)
            self.recording.status_info = RecordingStatus.RECORDING
            self.recording.record_url = record_url
            logger.info(f"Recording in Progress: {live_url}")
            logger.log("STREAM", f"Recording Stream URL: {record_url}")
            while True:
                if not self.recording.recording or not self.app.recording_enabled:
                    logger.info(f"Preparing to End Recording: {live_url}")

                    if os.name == "nt":
                        if process.stdin:
                            process.stdin.write(b"q")
                            await process.stdin.drain()
                    else:
                        # import signal
                        # process.send_signal(signal.SIGINT)
                        process.terminate()

                    if process.stdin:
                        process.stdin.close()

                    try:
                        await asyncio.wait_for(process.wait(), timeout=10.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()

                if process.returncode is not None:
                    logger.info(f"Exit loop recording (normal 0 | abnormal 1): code={process.returncode}, {live_url}")
                    break

                await asyncio.sleep(1)

            return_code = process.returncode
            safe_return_code = [0, 255]
            stdout, stderr = await process.communicate()
            if return_code not in safe_return_code and stderr:
                logger.error(f"FFmpeg Stderr Output: {str(stderr.decode()).splitlines()[0]}")
                self.recording.status_info = RecordingStatus.RECORDING_ERROR

                try:
                    self.app.record_manager.stop_recording(self.recording)
                    await self.app.record_card_manager.update_card(self.recording)
                    self.app.page.pubsub.send_others_on_topic("update", self.recording)
                    await self.app.snack_bar.show_snack_bar(
                        record_name + " " + self._["record_stream_error"], duration=2000
                    )
                except Exception as e:
                    logger.debug(f"Failed to update UI: {e}")

            if return_code in safe_return_code:
                if self.recording.monitor_status:
                    self.recording.status_info = RecordingStatus.MONITORING
                    display_title = self.recording.title
                else:
                    self.recording.status_info = RecordingStatus.STOPPED_MONITORING
                    display_title = self.recording.display_title

                self.recording.live_title = None
                if not self.recording.recording:
                    logger.success(f"Live recording has stopped: {record_name}")
                else:
                    self.recording.recording = False
                    logger.success(f"Live recording completed: {record_name}")

                try:
                    self.recording.update({"display_title": display_title})
                    await self.app.record_card_manager.update_card(self.recording)
                    self.app.page.pubsub.send_others_on_topic("update", self.recording)
                    if self.app.recording_enabled and process in self.app.process_manager.ffmpeg_processes:
                        self.app.page.run_task(self.app.record_manager.check_if_live, self.recording)
                    else:
                        self.recording.status_info = RecordingStatus.NOT_RECORDING_SPACE
                except Exception as e:
                    logger.debug(f"Failed to update UI: {e}")

                if self.default_config.get("convert_to_mp4") and self.save_format == "ts":
                    if self.segment_record:
                        file_paths = utils.get_file_paths(os.path.dirname(save_file_path))
                        prefix = os.path.basename(save_file_path).rsplit("_", maxsplit=1)[0]
                        for path in file_paths:
                            if prefix in path:
                                try:
                                    self.app.page.run_task(
                                        self.converts_mp4, path, self.default_config["delete_original"]
                                    )
                                except Exception as e:
                                    logger.error(f"Failed to convert video: {e}")
                                    await self.converts_mp4(path, self.default_config["delete_original"])
                    else:
                        try:
                            self.app.page.run_task(
                                self.converts_mp4, save_file_path, self.default_config["delete_original"]
                            )
                        except Exception as e:
                            logger.error(f"Failed to convert video: {e}")
                            await self.converts_mp4(save_file_path, self.default_config["delete_original"])

                if self.default_config.get("execute_custom_script") and script_command:
                    logger.info("Prepare a direct script in the background")
                    try:
                        self.app.page.run_task(
                            self.custom_script_execute,
                            script_command,
                            record_name,
                            save_file_path,
                            save_type,
                            self.segment_record,
                            self.default_config.get("convert_to_mp4")
                        )
                        logger.success("Successfully added script execution")
                    except Exception as e:
                        logger.error(f"Failed to execute custom script: {e}")
                        await self.custom_script_execute(
                            script_command,
                            record_name,
                            save_file_path,
                            save_type,
                            self.segment_record,
                            self.default_config.get("convert_to_mp4")
                        )

                # 语音识别处理
                if self.default_config.get("speech_recognition_enabled") and self.default_config.get("speech_recognition_auto_process"):
                    try:
                        # 延迟执行，等待转码和文件操作完成
                        delay_time = 10 if self.default_config.get("convert_to_mp4") else 3
                        
                        # 如果是分段录制，处理所有分段文件
                        if self.segment_record:
                            # 延迟后再查找文件，确保转码完成
                            self.app.page.run_task(self.process_speech_recognition_delayed, save_file_path, delay_time, True)
                        else:
                            # 处理单个文件
                            self.app.page.run_task(self.process_speech_recognition_delayed, save_file_path, delay_time, False)
                        
                        logger.info("语音识别任务已启动")
                    except Exception as e:
                        logger.error(f"启动语音识别失败: {e}")

        except Exception as e:
            logger.error(f"An error occurred during the subprocess execution: {e}")
            return False
        finally:
            self.recording.record_url = None

        return True

    async def converts_mp4(self, converts_file_path: str, is_original_delete: bool = True) -> None:
        """Asynchronous transcoding method, can be added to the background service to continue execution"""
        if not self.app.recording_enabled:
            logger.info(f"Application is closing, adding transcoding task to background service: {converts_file_path}")
            BackgroundService.get_instance().add_task(
                self.converts_mp4_sync, converts_file_path, is_original_delete
            )
            return
            
        # Otherwise, execute transcoding normally
        await self._do_converts_mp4(converts_file_path, is_original_delete)
    
    def converts_mp4_sync(self, converts_file_path: str, is_original_delete: bool = True) -> None:
        """Synchronous version of the transcoding method, used for background service"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._do_converts_mp4(converts_file_path, is_original_delete))
        finally:
            loop.close()
    
    async def _do_converts_mp4(self, converts_file_path: str, is_original_delete: bool = True) -> None:
        """Actual execution method for transcoding"""
        converts_success = False
        save_path = None
        try:
            converts_file_path = converts_file_path.replace("\\", "/")
            if os.path.exists(converts_file_path) and os.path.getsize(converts_file_path) > 0:
                save_path = converts_file_path.rsplit(".", maxsplit=1)[0] + ".mp4"
                _output = subprocess.check_output(
                    [
                        "ffmpeg",
                        "-i", converts_file_path,
                        "-c:v", "copy",
                        "-c:a", "copy",
                        "-f", "mp4",
                        save_path
                    ],
                    stderr=subprocess.STDOUT,
                    startupinfo=self.subprocess_start_info,
                )

                converts_success = True
                logger.info(f"Video transcoding completed: {save_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Video transcoding failed! Error message: {e.output.decode()}")

        try:
            if converts_success:
                if is_original_delete:
                    time.sleep(1)
                    if os.path.exists(converts_file_path):
                        os.remove(converts_file_path)
                    logger.info(f"Delete Original File: {converts_file_path}")
                else:
                    converts_dir = f"{os.path.dirname(save_path)}/original"
                    os.makedirs(converts_dir, exist_ok=True)
                    shutil.move(converts_file_path, converts_dir)
                    logger.info(f"Move Transcoding Files: {converts_file_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Error occurred during conversion: {e}")
        except Exception as e:
            logger.error(f"An unknown error occurred: {e}")

    async def custom_script_execute(
        self,
        script_command: str,
        record_name: str,
        save_file_path: str,
        save_type: str,
        split_video_by_time: bool,
        converts_to_mp4: bool
    ):
        from ..process_manager import BackgroundService
        
        if "python" in script_command:
            params = [
                f'--record_name "{record_name}"',
                f'--save_file_path "{save_file_path}"',
                f"--save_type {save_type}--split_video_by_time {split_video_by_time}",
                f"--converts_to_mp4 {converts_to_mp4}"
            ]
        else:
            params = [
                f'"{record_name.split(" ", maxsplit=1)[-1]}"',
                f'"{save_file_path}"',
                save_type,
                f"split_video_by_time: {split_video_by_time}",
                f"converts_to_mp4: {converts_to_mp4}"
            ]
        script_command = script_command.strip() + " " + " ".join(params)
        
        if not self.app.recording_enabled:
            logger.info("Application is closing, adding script execution task to background service")
            BackgroundService.get_instance().add_task(self.run_script_sync, script_command)
        else:
            self.app.page.run_task(self.run_script_async, script_command)
            
        logger.success("Script command execution initiated!")
        
    def run_script_sync(self, command: str) -> None:
        """Synchronous version of the script execution method, used for background service"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_script_async(command))
        finally:
            loop.close()

    async def run_script_async(self, command: str) -> None:
        try:
            process = await asyncio.create_subprocess_exec(
                *command.split(),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                startupinfo=self.subprocess_start_info,
                text=True
            )

            stdout, stderr = await process.communicate()

            if stdout:
                logger.info(stdout.splitlines()[0])
            if stderr:
                logger.error(stderr.splitlines()[0])

            if process.returncode != 0:
                logger.info(f"Custom Script process exited with return code {process.returncode}")

        except PermissionError:
            logger.error(
                "Script has no execution permission!, If it is a Linux environment, "
                "please first execute: chmod+x your_script.sh to grant script executable permission"
            )
        except OSError:
            logger.error("Please add `#!/bin/bash` at the beginning of your bash script file.")
        except Exception as e:
            logger.error(f"An error occurred: {e}")

    async def process_speech_recognition_delayed(self, save_file_path: str, delay_time: int, is_segment: bool) -> None:
        """
        延迟处理语音识别，等待转码完成
        
        Args:
            save_file_path: 原始保存路径
            delay_time: 延迟时间（秒）
            is_segment: 是否为分段录制
        """
        try:
            # 等待文件操作完成
            await asyncio.sleep(delay_time)
            
            if is_segment:
                # 分段录制：查找所有相关文件
                save_dir = os.path.normpath(os.path.dirname(save_file_path))
                file_paths = utils.get_file_paths(save_dir)
                prefix = os.path.basename(save_file_path).rsplit("_", maxsplit=1)[0]
                
                for path in file_paths:
                    normalized_path = os.path.normpath(path)
                    if prefix in os.path.basename(normalized_path) and os.path.exists(normalized_path):
                        # 优先使用mp4文件
                        if self.default_config.get("convert_to_mp4") and normalized_path.endswith('.ts'):
                            mp4_path = os.path.splitext(normalized_path)[0] + ".mp4"
                            if os.path.exists(mp4_path):
                                normalized_path = mp4_path
                        
                        if os.path.exists(normalized_path):
                            await self.process_speech_recognition(normalized_path)
            else:
                # 单个文件
                final_file_path = os.path.normpath(save_file_path)
                
                # 如果启用了转码，优先使用转码后的mp4文件
                if self.default_config.get("convert_to_mp4") and self.save_format == "ts":
                    mp4_path = os.path.splitext(final_file_path)[0] + ".mp4"
                    if os.path.exists(mp4_path):
                        final_file_path = mp4_path
                
                if os.path.exists(final_file_path):
                    await self.process_speech_recognition(final_file_path)
                else:
                    logger.warning(f"语音识别：文件不存在 {final_file_path}")
                    
        except Exception as e:
            logger.error(f"延迟语音识别处理失败: {e}")

    async def process_speech_recognition(self, video_file_path: str) -> None:
        """
        处理视频文件的语音识别
        
        Args:
            video_file_path: 视频文件路径
        """
        try:
            # 检查语音识别管理器是否已初始化
            if not hasattr(self.app, 'speech_recognition_manager'):
                from .speech_recognition import SpeechRecognitionManager
                self.app.speech_recognition_manager = SpeechRecognitionManager(self.app)
            
            # 延迟执行，等待文件写入完成
            await asyncio.sleep(2)
            
            if not self.app.recording_enabled:
                logger.info(f"Application is closing, adding speech recognition task to background service: {video_file_path}")
                BackgroundService.get_instance().add_task(
                    self.process_speech_recognition_sync, video_file_path
                )
                return
            
            # 正常执行语音识别
            success = await self.app.speech_recognition_manager.recognize_and_save_subtitle(video_file_path)
            if success:
                logger.success(f"语音识别完成: {video_file_path}")
            else:
                logger.warning(f"语音识别失败或跳过: {video_file_path}")
                
        except Exception as e:
            logger.error(f"语音识别处理异常: {e}")

    def process_speech_recognition_sync(self, video_file_path: str) -> None:
        """同步版本的语音识别处理方法，用于后台服务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.process_speech_recognition(video_file_path))
        finally:
            loop.close()

    @staticmethod
    def get_headers_params(live_url, platform_key):
        live_domain = "/".join(live_url.split("/")[0:3])
        record_headers = {
            "pandalive": "origin:https://www.pandalive.co.kr",
            "winktv": "origin:https://www.winktv.co.kr",
            "popkontv": "origin:https://www.popkontv.com",
            "flextv": "origin:https://www.flextv.co.kr",
            "qiandurebo": "referer:https://qiandurebo.com",
            "17live": "referer:https://17.live/en/live/6302408",
            "lang": "referer:https://www.lang.live",
            "shopee": "origin:" + live_domain
        }
        return record_headers.get(platform_key)
