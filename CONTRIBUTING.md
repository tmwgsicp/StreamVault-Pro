# 🤝 贡献指南 | Contributing Guide

感谢您对 StreamVault Pro 项目的关注！我们欢迎社区的贡献和反馈。

Thank you for your interest in the StreamVault Pro project! We welcome contributions and feedback from the community.

## 📋 如何贡献 | How to Contribute

### 🐛 报告问题 | Reporting Issues

如果您发现了bug或有功能建议：
If you find bugs or have feature suggestions:

1. 在提交新issue前，请先搜索现有的[Issues](https://github.com/tmwgsicp/StreamVault-Pro/issues)
2. 使用相应的issue模板
3. 提供详细的重现步骤和环境信息
4. 附上相关的日志和截图

### 💡 功能建议 | Feature Requests

对于新功能建议，请：
For new feature suggestions, please:

1. 查看[Discussions](https://github.com/tmwgsicp/StreamVault-Pro/discussions)
2. 详细描述功能需求和使用场景
3. 说明功能的预期效果
4. 考虑功能的实现复杂度

### 🔧 代码贡献 | Code Contributions

#### 开发环境设置 | Development Environment Setup

```bash
# 1. Fork并克隆仓库 | Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/StreamVault-Pro.git
cd StreamVault-Pro

# 2. 创建虚拟环境 | Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装开发依赖 | Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. 安装预提交钩子 | Install pre-commit hooks
pre-commit install
```

#### 代码规范 | Code Standards

我们使用以下工具确保代码质量：
We use the following tools to ensure code quality:

- **Ruff**: 代码格式化和linting
- **MyPy**: 类型检查
- **Black**: 代码格式化
- **Pytest**: 单元测试

```bash
# 运行代码检查 | Run code checks
python -m ruff check .
python -m ruff format .
python -m mypy app/
python -m pytest
```

#### 提交规范 | Commit Convention

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

类型 | Types:
- `feat`: 新功能 | new feature
- `fix`: 修复bug | bug fix
- `docs`: 文档更新 | documentation update
- `style`: 代码格式 | code style
- `refactor`: 重构 | refactoring
- `test`: 测试 | tests
- `chore`: 构建/工具 | build/tools

示例 | Examples:
```
feat(transcript): add batch export functionality
fix(ui): resolve recording card display issue
docs(readme): update installation instructions
```

#### Pull Request流程 | Pull Request Process

1. **创建分支** | Create Branch
   ```bash
   git checkout -b feature/your-feature-name
   # 或 | or
   git checkout -b fix/issue-description
   ```

2. **开发和测试** | Develop and Test
   - 编写代码并添加测试
   - 确保所有测试通过
   - 遵循代码规范

3. **提交更改** | Commit Changes
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   git push origin feature/your-feature-name
   ```

4. **创建Pull Request** | Create Pull Request
   - 使用清晰的标题和描述
   - 引用相关的issue
   - 添加必要的测试和文档

5. **代码审查** | Code Review
   - 等待维护者审查
   - 根据反馈修改代码
   - 合并到主分支

## 📝 开发指南 | Development Guidelines

### 项目结构 | Project Structure

```
StreamVault-Pro/
├── app/                    # 应用核心代码 | Core application code
│   ├── core/              # 核心功能 | Core functionality
│   ├── ui/                # 用户界面 | User interface
│   ├── utils/             # 工具函数 | Utility functions
│   └── models/            # 数据模型 | Data models
├── config/                # 配置文件 | Configuration files
├── assets/                # 静态资源 | Static assets
├── tests/                 # 测试文件 | Test files
└── docs/                  # 文档 | Documentation
```

### 添加新平台支持 | Adding New Platform Support

1. 在 `app/core/platform_handlers/handlers.py` 中添加新的处理器
2. 实现 `PlatformHandler` 基类的抽象方法
3. 在 `__init__.py` 中注册新的处理器
4. 添加相应的测试

### UI组件开发 | UI Component Development

1. 所有UI组件应继承适当的基类
2. 使用 Flet 框架的最佳实践
3. 确保组件支持深浅主题
4. 添加国际化支持

### 测试要求 | Testing Requirements

- 为新功能添加单元测试
- 确保测试覆盖率不低于80%
- 测试应该快速且可靠
- 使用mock对象模拟外部依赖

## 🌐 国际化 | Internationalization

项目支持多语言，当前支持：
The project supports multiple languages, currently supporting:

- 简体中文 (zh_CN)
- English (en)

添加新的翻译：
To add new translations:

1. 在 `locales/` 目录中添加语言文件
2. 更新 `app/utils/language_manager.py`
3. 测试新语言的显示效果

## 📄 许可证 | License

通过贡献代码，您同意您的贡献将在 [Apache License 2.0](./LICENSE) 下发布。
By contributing, you agree that your contributions will be licensed under [Apache License 2.0](./LICENSE).

## 🙏 致谢 | Acknowledgments

感谢所有为项目做出贡献的开发者！
Thanks to all developers who contribute to the project!

## 📞 联系方式 | Contact

如果您有任何问题，可以通过以下方式联系我们：
If you have any questions, you can contact us through:

- **GitHub Issues**: [提交问题](https://github.com/tmwgsicp/StreamVault-Pro/issues)
- **GitHub Discussions**: [参与讨论](https://github.com/tmwgsicp/StreamVault-Pro/discussions)
- **Email**: tmwgsicp@outlook.com

---

再次感谢您的贡献！🚀
Thank you again for your contribution! 🚀 