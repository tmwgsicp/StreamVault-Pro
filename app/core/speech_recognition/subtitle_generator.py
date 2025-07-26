import re
from datetime import datetime, timedelta
from typing import List, Tuple


class SubtitleGenerator:
    """字幕生成器"""
    
    def __init__(self):
        # 句子分割符（中英文标点符号）
        self.sentence_separators = r'[。！？；.!?;]'
        # 默认字幕显示时长（秒）
        self.default_duration = 3.0
        # 每行最大字符数
        self.max_chars_per_line = 30
    
    def split_text_into_sentences(self, text: str) -> List[str]:
        """将文本按句子分割"""
        # 按标点符号分割
        sentences = re.split(self.sentence_separators, text)
        
        # 清理空白和空句子
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 如果没有标点符号，按长度分割
        if len(sentences) <= 1:
            sentences = self.split_by_length(text)
        
        return sentences
    
    def split_by_length(self, text: str) -> List[str]:
        """按长度分割文本"""
        sentences = []
        words = text.split()
        current_sentence = ""
        
        for word in words:
            if len(current_sentence + word) <= self.max_chars_per_line:
                current_sentence += word + " "
            else:
                if current_sentence:
                    sentences.append(current_sentence.strip())
                current_sentence = word + " "
        
        if current_sentence:
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def calculate_timestamps(self, sentences: List[str]) -> List[Tuple[str, str, str]]:
        """计算字幕时间戳"""
        result = []
        current_time = 0.0
        
        for sentence in sentences:
            start_time = current_time
            
            # 根据句子长度计算显示时长
            char_count = len(sentence)
            duration = max(self.default_duration, char_count * 0.1)  # 每个字符0.1秒，最少3秒
            
            end_time = start_time + duration
            
            start_timestamp = self.seconds_to_timestamp(start_time)
            end_timestamp = self.seconds_to_timestamp(end_time)
            
            result.append((start_timestamp, end_timestamp, sentence))
            
            current_time = end_time + 0.5  # 间隔0.5秒
        
        return result
    
    def seconds_to_timestamp(self, seconds: float) -> str:
        """将秒数转换为时间戳格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def seconds_to_vtt_timestamp(self, seconds: float) -> str:
        """将秒数转换为WebVTT时间戳格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    def generate_srt(self, text: str) -> str:
        """生成SRT格式字幕"""
        sentences = self.split_text_into_sentences(text)
        timestamps = self.calculate_timestamps(sentences)
        
        srt_content = []
        for i, (start, end, sentence) in enumerate(timestamps, 1):
            srt_content.append(f"{i}")
            srt_content.append(f"{start} --> {end}")
            srt_content.append(sentence)
            srt_content.append("")  # 空行分隔
        
        return "\n".join(srt_content)
    
    def generate_vtt(self, text: str) -> str:
        """生成WebVTT格式字幕"""
        sentences = self.split_text_into_sentences(text)
        
        vtt_content = ["WEBVTT", ""]
        current_time = 0.0
        
        for sentence in sentences:
            start_time = current_time
            char_count = len(sentence)
            duration = max(self.default_duration, char_count * 0.1)
            end_time = start_time + duration
            
            start_timestamp = self.seconds_to_vtt_timestamp(start_time)
            end_timestamp = self.seconds_to_vtt_timestamp(end_time)
            
            vtt_content.append(f"{start_timestamp} --> {end_timestamp}")
            vtt_content.append(sentence)
            vtt_content.append("")
            
            current_time = end_time + 0.5
        
        return "\n".join(vtt_content) 