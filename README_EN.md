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
  <a href="./README.md">简体中文</a> / English
</div><br>

# 🚀 StreamVault Pro - Professional Live Stream Recording Platform

**StreamVault Pro** is a powerful professional-grade live stream recording and management platform, built upon the open-source [StreamCap](https://github.com/ihmily/StreamCap) project with extensive optimizations and feature enhancements. We are committed to providing users with more professional and efficient live content management solutions.

## 📋 Project Information

This project is a secondary development based on the open-source [StreamCap](https://github.com/ihmily/StreamCap) project, following the Apache-2.0 license.

**Original Author:** [ihmily](https://github.com/ihmily)  
**Project Maintainer:** [tmwgsicp](https://github.com/tmwgsicp)  
**Project Repository:** https://github.com/tmwgsicp/StreamVault-Pro

## 🎯 Core Features

### 🎥 Professional Recording
- **Multi-platform Support**: Supports 40+ major live streaming platforms including Douyin, Kuaishou, Bilibili, Huya, Douyu, TikTok, YouTube Live, etc.
- **Smart Monitoring**: Automatic detection of live stream status, records when streams go live, auto-reconnect on stream interruption
- **High-quality Recording**: Based on FFmpeg technology, ensuring recording quality and stability
- **Multiple Output Formats**: Supports ts, flv, mkv, mov, mp4, and other output formats
- **Auto Transcoding**: Automatically transcode to standard mp4 format after recording completion

### 🧠 Intelligent Transcript Management
- **Auto Recognition**: Intelligently scans and recognizes transcript files in recording directories
- **Multi-format Support**: Supports txt, srt, vtt, lrc and other subtitle and transcript formats
- **Batch Operations**: Supports batch export, search and management of transcripts
- **Search Functionality**: Powerful keyword search and date filtering capabilities

### 🎨 Modern Interface Design
- **Intuitive Operation**: Clean and modern user interface with intuitive operation
- **Real-time Status**: Real-time display of recording status, progress and statistics
- **Responsive Design**: Adapts to different screen sizes and resolutions
- **Theme Support**: Supports light and dark theme switching

### 🌐 Cross-platform Support
- **Desktop Versions**: Full support for Windows, macOS, Linux systems
- **Web Version**: Modern browser-based web application
- **Lightweight Deployment**: No complex configuration required, works out of the box

## 📋 Supported Platforms

StreamVault Pro supports recording from the following live streaming platforms:

### 🇨🇳 Domestic Platforms
- Douyin (抖音)
- Kuaishou (快手)
- Bilibili (哔哩哔哩)
- Huya (虎牙)
- Douyu (斗鱼)
- YY Live
- Huajiao Live
- Inke Live

### 🌍 International Platforms
- TikTok
- YouTube Live
- Twitch
- Facebook Live
- Instagram Live
- Twitter Spaces
- 30+ other platforms...

## 🚀 Quick Start

### Run from Source

```bash
# Clone repository
git clone https://github.com/tmwgsicp/StreamVault-Pro.git
cd StreamVault-Pro

# Install dependencies
pip install -r requirements.txt

# Run desktop version
python main.py

# Run web version
python main.py --web --host 0.0.0.0 --port 8080
```

Then visit `http://localhost:8080` in your browser (for web version)

### System Requirements

- **Python**: 3.10 or higher
- **FFmpeg**: For video recording and transcoding
- **Operating System**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)

## 📚 User Guide

### Basic Recording
1. Add live stream URL
2. Select recording quality and format
3. Set save path
4. Start monitoring and recording

### Advanced Features
- **Transcript Management**: Automatically scan and manage transcript content from recordings
- **Batch Operations**: Monitor multiple live streams simultaneously
- **Scheduled Tasks**: Set specific time periods for recording
- **Message Notifications**: Receive live status notifications

## 🔧 Configuration

Main configuration files are located in the `config/` directory:
- `settings.json` - Main settings
- `accounts.json` - Account configuration
- `cookies.json` - Cookie configuration
- `version.json` - Version information

## 🤝 Contributing

We welcome community contributions! Please check the [Contributing Guide](./CONTRIBUTING.md) to learn how to participate in project development.

### Development Environment Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Code formatting
python -m ruff format .

# Type checking
python -m mypy app/
```

## 📄 License

This project is licensed under the [Apache License 2.0](./LICENSE).

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Patent use
- ✅ Private use

**Note**: When using this software to record live content, please comply with the relevant platform terms of service and local laws and regulations.

## 📞 Support & Feedback

- **Documentation**: [Wiki](https://github.com/tmwgsicp/StreamVault-Pro/wiki)
- **Bug Reports**: [Issues](https://github.com/tmwgsicp/StreamVault-Pro/issues)
- **Feature Requests**: [Discussions](https://github.com/tmwgsicp/StreamVault-Pro/discussions)
- **Email Contact**: tmwgsicp@outlook.com

## 🙏 Acknowledgments

- Thanks to [ihmily](https://github.com/ihmily) for providing the excellent open-source project [StreamCap](https://github.com/ihmily/StreamCap)
- Thanks to all contributors and users for their support and feedback
- Thanks to the open-source community for providing excellent tools and libraries

---

<div align="center">
  <strong>Making live content management more professional and efficient 🚀</strong>
</div>
