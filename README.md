<div align="center">
  <img src="./assets/images/logo.svg" alt="StreamVault Pro" />
</div>
<p align="center">
  <img alt="Python version" src="https://img.shields.io/badge/python-3.10%2B-blue.svg">
  <a href="https://github.com/tmwgsicp/StreamVault-Pro">
      <img alt="Supported Platforms" src="https://img.shields.io/badge/Platforms-Win%20%7C%20Mac%20%7C%20Linux-6B5BFF.svg"></a>
  <a href="https://github.com/tmwgsicp/StreamVault-Pro/releases/latest">
      <img alt="Latest Release" src="https://img.shields.io/github/v/release/tmwgsicp/StreamVault-Pro"></a>
  <a href="https://github.com/tmwgsicp/StreamVault-Pro/releases/latest">
      <img alt="Downloads" src="https://img.shields.io/github/downloads/tmwgsicp/StreamVault-Pro/total"></a>
  <a href="https://github.com/tmwgsicp/StreamVault-Pro/blob/main/LICENSE">
      <img alt="License" src="https://img.shields.io/badge/license-Apache%202.0-blue.svg"></a>
</p>
<div align="center">
  简体中文 / <a href="./README_EN.md">English</a>
</div><br>

# 🚀 StreamVault Pro - 专业级直播录制管理平台

**StreamVault Pro** 是一款功能强大的专业级直播流录制和管理平台，基于开源项目 [StreamCap](https://github.com/ihmily/StreamCap) 进行深度优化和功能扩展。我们致力于为用户提供更加专业、高效的直播内容管理解决方案。

## 📋 项目说明

本项目基于 [StreamCap](https://github.com/ihmily/StreamCap) 开源项目进行二次开发，遵循 Apache-2.0 开源协议。

**原项目作者：** [ihmily](https://github.com/ihmily)  
**项目维护者：** [tmwgsicp](https://github.com/tmwgsicp)  
**项目地址：** https://github.com/tmwgsicp/StreamVault-Pro

## 🎯 核心特性 | Core Features

### 🎥 专业录制功能
- **多平台支持**: 支持抖音、快手、B站、虎牙、斗鱼等40+主流直播平台
- **智能监控**: 自动检测开播状态，开播即录，断流自动重连
- **高质量录制**: 基于FFmpeg技术，保证录制质量和稳定性
- **多格式输出**: 支持ts、flv、mkv、mov、mp4等多种输出格式
- **自动转码**: 录制完成后可自动转码为标准mp4格式

### 🧠 智能文案管理
- **自动识别**: 智能扫描并识别录制目录中的文案文件
- **多格式支持**: 支持txt、srt、vtt、lrc等字幕和文案格式
- **批量操作**: 支持文案的批量导出、搜索和管理
- **搜索功能**: 强大的关键词搜索和日期筛选功能

### 🎨 现代化界面设计
- **直观操作**: 简洁现代的用户界面，操作直观易懂
- **实时状态**: 实时显示录制状态、进度和统计信息
- **响应式设计**: 适配不同屏幕尺寸和分辨率
- **主题支持**: 支持明暗主题切换

### 🌐 跨平台支持
- **桌面版本**: 完整支持Windows、macOS、Linux系统
- **Web版本**: 基于现代浏览器的Web应用
- **轻量部署**: 无需复杂配置，开箱即用

## 📋 支持平台 | Supported Platforms

StreamVault Pro 支持以下直播平台的录制：

### 🇨🇳 国内平台
- 抖音 (Douyin)
- 快手 (Kuaishou) 
- 哔哩哔哩 (Bilibili)
- 虎牙 (Huya)
- 斗鱼 (Douyu)
- YY直播
- 花椒直播
- 映客直播

### 🌍 国际平台  
- TikTok
- YouTube Live
- Twitch
- Facebook Live
- Instagram Live
- Twitter Spaces
- 其他30+平台...

## 🚀 快速开始

### 源码运行

```bash
# 克隆仓库
git clone https://github.com/tmwgsicp/StreamVault-Pro.git
cd StreamVault-Pro

# 安装依赖
pip install -r requirements.txt

# 运行桌面版
python main.py

# 运行Web版
python main.py --web --host 0.0.0.0 --port 8080
```

然后在浏览器中访问 `http://localhost:8080`（Web版）

### 系统要求

- **Python**: 3.10 或更高版本
- **FFmpeg**: 用于视频录制和转码
- **操作系统**: Windows 10+、macOS 10.14+、Linux (Ubuntu 18.04+)

## 📚 使用指南

### 基础录制
1. 添加直播间URL
2. 选择录制质量和格式
3. 设置保存路径
4. 开始监控和录制

### 高级功能
- **文案管理**：自动扫描和管理录制产生的文案内容
- **批量操作**：同时监控多个直播间
- **定时任务**：设置特定时间段进行录制
- **消息推送**：接收直播状态通知

## 🔧 配置说明

主要配置文件位于 `config/` 目录：
- `settings.json` - 主要设置
- `accounts.json` - 账户配置
- `cookies.json` - Cookie配置
- `version.json` - 版本信息

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [贡献指南](./CONTRIBUTING.md) 了解如何参与项目开发。

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest

# 代码格式化
python -m ruff format .

# 类型检查
python -m mypy app/
```

## 📄 许可证

本项目基于 [Apache License 2.0](./LICENSE) 开源协议。

- ✅ 商业使用
- ✅ 修改
- ✅ 分发
- ✅ 专利使用
- ✅ 私人使用

**注意**：使用本软件录制直播内容时，请遵守相关平台的服务条款和当地法律法规。

## 📞 支持与反馈

- **文档**：[Wiki](https://github.com/tmwgsicp/StreamVault-Pro/wiki)
- **问题反馈**：[Issues](https://github.com/tmwgsicp/StreamVault-Pro/issues)
- **功能建议**：[Discussions](https://github.com/tmwgsicp/StreamVault-Pro/discussions)
- **邮件联系**：tmwgsicp@outlook.com

## 🙏 致谢

- 感谢 [ihmily](https://github.com/ihmily) 提供的优秀开源项目 [StreamCap](https://github.com/ihmily/StreamCap)
- 感谢所有贡献者和用户的支持与反馈
- 感谢开源社区提供的优秀工具和库

---

<div align="center">
  <strong>让直播内容管理更加专业高效 🚀</strong>
</div>
