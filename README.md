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

## ✨ 核心特性

### 🎯 专业录制功能
- **40+ 平台支持**：覆盖抖音、快手、B站、虎牙、斗鱼、TikTok、YouTube等主流直播平台
- **智能监控**：循环监控直播状态，开播即录，支持定时任务和自动检测
- **多格式输出**：支持 ts、flv、mkv、mov、mp4、mp3、m4a 等多种输出格式
- **自动转码**：录制完成后可自动转码为 mp4 格式
- **高质量录制**：支持多种画质选择，确保录制质量

### 📝 智能文案管理
- **多格式支持**：自动识别和管理录制目录中的文案文件（txt、srt、vtt、lrc格式）
- **智能搜索**：支持关键词搜索、日期筛选，搜索结果高亮显示
- **批量操作**：支持批量导出和管理操作
- **内容统计**：显示字数、行数、文件大小等详细信息
- **增强预览**：优化的文案查看界面，提供更好的阅读体验

### 🎨 现代化界面设计
- **录制卡片增强**：平台图标识别、状态颜色标识、智能时间信息显示
- **数据可视化**：友好的数据格式化显示（时长、速度、文件大小）
- **响应式布局**：支持网格视图和列表视图，适配不同使用习惯
- **深浅主题**：支持深浅主题模式切换
- **现代化设计**：Material Design风格，专业美观

### 🌐 跨平台支持
- **桌面应用**：Windows、macOS、Linux 原生支持
- **Web版本**：浏览器直接访问，无需安装

## 📸 界面预览

![StreamVault Pro Interface](./assets/images/example01.png)

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
