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

## ✨ Core Features

### 🎯 Professional Recording
- **40+ Platform Support**: Covers major live streaming platforms including Douyin, Kuaishou, Bilibili, Huya, Douyu, TikTok, YouTube, and more
- **Smart Monitoring**: Continuous live status monitoring, auto-record when streaming starts, supports scheduled tasks and automatic detection
- **Multi-format Output**: Supports ts, flv, mkv, mov, mp4, mp3, m4a, and other output formats
- **Auto Transcoding**: Automatically transcode to mp4 format after recording completion
- **High-quality Recording**: Multiple quality options to ensure recording quality

### 📝 Intelligent Transcript Management
- **Multi-format Support**: Automatic recognition and management of transcript files in recording directories (txt, srt, vtt, lrc formats)
- **Smart Search**: Keyword search and date filtering with search result highlighting
- **Batch Operations**: Support for batch export and management operations
- **Content Statistics**: Display word count, line count, file size and other detailed information
- **Enhanced Preview**: Optimized transcript viewing interface for better reading experience

### 🎨 Modern Interface Design
- **Enhanced Recording Cards**: Platform icon recognition, status color indicators, smart time information display
- **Data Visualization**: User-friendly data formatting display (duration, speed, file size)
- **Responsive Layout**: Support for grid view and list view, adapting to different usage habits
- **Dark/Light Themes**: Support for dark and light theme mode switching
- **Modern Design**: Material Design style, professional and beautiful

### 🌐 Cross-platform Support
- **Desktop Applications**: Native support for Windows, macOS, Linux
- **Web Version**: Direct browser access, no installation required

## 📸 Interface Preview

![StreamVault Pro Interface](./assets/images/example01.png)

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
