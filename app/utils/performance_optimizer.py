"""
性能优化工具模块
提供UI渲染优化、内存管理、异步任务管理等功能
"""
import asyncio
import gc
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
import weakref

import flet as ft

from .logger import logger


class PerformanceOptimizer:
    """性能优化器"""
    
    def __init__(self):
        self.render_cache = {}
        self.task_pool = set()
        self.weak_refs = weakref.WeakSet()
        self.last_gc_time = time.time()
        self.gc_interval = 300  # 5分钟垃圾回收间隔
        
    def debounce(self, wait_time: float = 0.3):
        """防抖装饰器"""
        def decorator(func: Callable):
            last_called = [0]
            pending_call = [None]
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # 取消之前的调用
                if pending_call[0]:
                    pending_call[0].cancel()
                
                # 如果距离上次调用时间足够长，直接执行
                if current_time - last_called[0] >= wait_time:
                    last_called[0] = current_time
                    return await func(*args, **kwargs)
                
                # 否则延迟执行
                async def delayed_call():
                    await asyncio.sleep(wait_time)
                    last_called[0] = time.time()
                    return await func(*args, **kwargs)
                
                pending_call[0] = asyncio.create_task(delayed_call())
                return await pending_call[0]
            
            return wrapper
        return decorator
    
    def throttle(self, interval: float = 1.0):
        """节流装饰器"""
        def decorator(func: Callable):
            last_called = [0]
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_time = time.time()
                if current_time - last_called[0] >= interval:
                    last_called[0] = current_time
                    return await func(*args, **kwargs)
                
            return wrapper
        return decorator
    
    def cache_render(self, cache_key: str, ttl: float = 300):
        """渲染结果缓存装饰器"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                current_time = time.time()
                
                # 检查缓存
                if cache_key in self.render_cache:
                    cached_data, timestamp = self.render_cache[cache_key]
                    if current_time - timestamp < ttl:
                        return cached_data
                
                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.render_cache[cache_key] = (result, current_time)
                return result
            
            return wrapper
        return decorator
    
    def clear_cache(self, pattern: Optional[str] = None):
        """清空缓存"""
        if pattern:
            keys_to_remove = [k for k in self.render_cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.render_cache[key]
        else:
            self.render_cache.clear()
    
    async def batch_update_controls(self, controls: List[ft.Control], delay: float = 0.01):
        """批量更新控件，减少重绘次数"""
        for control in controls:
            control.update()
            if delay > 0:
                await asyncio.sleep(delay)
    
    def manage_task(self, task: asyncio.Task):
        """管理异步任务，防止内存泄漏"""
        self.task_pool.add(task)
        task.add_done_callback(lambda t: self.task_pool.discard(t))
        return task
    
    def add_weak_ref(self, obj: Any):
        """添加弱引用，便于内存管理"""
        self.weak_refs.add(obj)
    
    async def periodic_cleanup(self):
        """定期清理内存"""
        current_time = time.time()
        if current_time - self.last_gc_time > self.gc_interval:
            # 清理过期缓存
            expired_keys = []
            for key, (_, timestamp) in self.render_cache.items():
                if current_time - timestamp > 600:  # 10分钟过期
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.render_cache[key]
            
            # 强制垃圾回收
            gc.collect()
            self.last_gc_time = current_time
            
            logger.debug(f"性能清理完成: 清理缓存 {len(expired_keys)} 项，活动任务 {len(self.task_pool)} 个")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "cache_size": len(self.render_cache),
            "active_tasks": len(self.task_pool),
            "weak_refs": len(self.weak_refs),
            "last_gc": self.last_gc_time,
        }


class UIOptimizer:
    """UI优化器"""
    
    @staticmethod
    def create_efficient_grid(items: List[Any], create_item_func: Callable, 
                            runs_count: int = 3, chunk_size: int = 20) -> ft.GridView:
        """创建高效的网格视图，支持大量数据的分块渲染"""
        grid = ft.GridView(
            expand=True,
            runs_count=runs_count,
            spacing=10,
            run_spacing=10,
            child_aspect_ratio=1.2,
            controls=[]
        )
        
        # 分块渲染
        for i in range(0, min(len(items), chunk_size)):
            item_control = create_item_func(items[i])
            grid.controls.append(item_control)
        
        return grid
    
    @staticmethod
    def create_virtual_list(items: List[Any], create_item_func: Callable,
                          visible_count: int = 20) -> ft.ListView:
        """创建虚拟列表，只渲染可见项目"""
        list_view = ft.ListView(
            expand=True,
            spacing=8,
            padding=ft.Padding(10, 5, 10, 5),
            controls=[]
        )
        
        # 只渲染前面的可见项目
        for i in range(min(len(items), visible_count)):
            item_control = create_item_func(items[i])
            list_view.controls.append(item_control)
        
        return list_view
    
    @staticmethod
    def optimize_button_style(button: ft.ElevatedButton, size: str = "medium") -> ft.ElevatedButton:
        """优化按钮样式和性能"""
        size_configs = {
            "small": {"height": 28, "icon_size": 14, "text_size": 11, "padding": 6},
            "medium": {"height": 35, "icon_size": 16, "text_size": 12, "padding": 8},
            "large": {"height": 42, "icon_size": 18, "text_size": 14, "padding": 10},
        }
        
        config = size_configs.get(size, size_configs["medium"])
        
        button.height = config["height"]
        if hasattr(button, 'content') and isinstance(button.content, ft.Row):
            for control in button.content.controls:
                if isinstance(control, ft.Icon):
                    control.size = config["icon_size"]
                elif isinstance(control, ft.Text):
                    control.size = config["text_size"]
        
        if button.style:
            button.style.padding = ft.Padding(config["padding"], config["padding"], 
                                           config["padding"], config["padding"])
        
        return button


# 全局性能优化器实例
performance_optimizer = PerformanceOptimizer()
ui_optimizer = UIOptimizer() 