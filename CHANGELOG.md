# 📋 更新日志 | Changelog

StreamVault Pro 项目的所有重要更改都记录在此文件中。
All notable changes to the StreamVault Pro project will be documented in this file.

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-01

### 🚀 重大更新 | Major Updates

#### 添加 | Added
- **项目重新品牌化**: 更名为 StreamVault Pro
- **现代化Logo设计**: 全新的品牌标识和视觉设计
- **代码库清理**: 移除敏感信息，为开源发布做准备
- **完整文档体系**: 全面的README、贡献指南、发布指南
- **开源社区支持**: 专注于开源社区驱动的发展

#### 改进 | Improved
- **文档体系重构**: 全面重写README和项目文档
- **项目结构优化**: 更清晰的代码组织和模块划分
- **国际化支持**: 完善的中英文双语支持
- **用户体验优化**: 更专业的界面设计和交互体验

#### 修复 | Fixed
- **兼容性问题**: 修复与最新Flet版本的兼容性问题
- **稳定性改进**: 提升应用整体稳定性和性能表现
- **安全性增强**: 清理敏感信息，提高代码安全性

## [1.1.0] - 2024-12-15

### ✨ 功能增强 | Feature Enhancements

#### 添加 | Added
- **📝 智能文案管理系统**
  - 自动扫描录制目录中的文案文件（txt、srt、vtt、lrc格式）
  - 支持关键词搜索、日期筛选、批量操作
  - 一键导出功能，支持单个或批量导出文案内容
  - 增强的文案查看界面，支持搜索高亮和内容统计

- **🎨 界面优化升级**
  - 录制卡片增强显示，新增平台识别图标和颜色标识
  - 智能时间信息显示（添加时间、最后录制时间）
  - 友好的数据格式化（时长、速度、文件大小）
  - 现代化卡片设计（阴影效果、圆角边框、芯片标签）

#### 改进 | Improved
- **主界面管理优化**
  - 实时搜索和智能筛选功能
  - 多维度排序（名称、状态、平台、时间）
  - 统计信息展示和批量操作优化
  - 网格视图和列表视图兼容性改进

- **文件格式支持扩展**
  - 新增 `.lrc` 歌词文件格式支持
  - 智能文本提取，从字幕文件中提取纯文本内容
  - 改进的文件格式识别和处理

#### 修复 | Fixed
- 修复文案对话框需要点击两次才显示的问题
- 修复网格视图下功能按钮不可见的问题
- 优化页面切换和加载性能
- 改进错误处理和用户反馈机制
- 修复深浅主题模式切换问题

## [1.0.1] - 2024-11-30

### 🔧 维护更新 | Maintenance Update

#### 修复 | Fixed
- 修复录制状态显示不准确的问题
- 改进FFmpeg进程管理
- 优化内存使用和性能表现
- 修复部分平台录制失败的问题

#### 改进 | Improved
- 更新依赖库到最新版本
- 改进错误日志记录
- 优化启动速度

## [1.0.0] - 2024-11-15

### 🎉 初始发布 | Initial Release

#### 功能特性 | Features
- **多平台录制支持**: 支持40+主流直播平台
- **智能监控**: 循环监控直播状态，开播即录
- **多格式输出**: 支持ts、flv、mkv、mov、mp4等格式
- **自动转码**: 录制完成后自动转码为mp4格式
- **跨平台支持**: Windows、macOS、Linux和Web版本
- **消息推送**: 支持直播状态推送通知

#### 技术实现 | Technical Implementation
- 基于Flet框架构建现代化UI
- 集成FFmpeg进行高质量录制
- 使用StreamGet库处理多平台流媒体

---

## 版本说明 | Version Notes

### 版本编号规则 | Version Numbering Rules

我们遵循语义化版本规范：
We follow semantic versioning:

- **主版本号** (Major): 不兼容的API更改
- **次版本号** (Minor): 向后兼容的功能性新增
- **修订号** (Patch): 向后兼容的问题修正

### 发布周期 | Release Cycle

- **主版本**: 每年1-2次重大更新
- **次版本**: 每月1-2次功能更新
- **修订版**: 根据需要随时发布bug修复

### 支持策略 | Support Policy

- 当前版本和前一个主版本提供完整支持
- 安全补丁会向后兼容至少两个主版本
- 社区用户享受开源社区支持

---

## 🔗 相关链接 | Related Links

- [项目主页](https://github.com/tmwgsicp/StreamVault-Pro)
- [问题反馈](https://github.com/tmwgsicp/StreamVault-Pro/issues)
- [功能建议](https://github.com/tmwgsicp/StreamVault-Pro/discussions)

感谢所有贡献者的支持！🙏
Thanks to all contributors for their support! 🙏 