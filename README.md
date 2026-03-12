# Claude Marketplace

通用性质的 Claude Code 插件市场。

## 插件列表

### checkpoint-architect

审查点构建助手 - 帮助产品经理通过引导式对话创建符合系统规范的审查点内容。

**功能特性：**
- 引导式对话，无需技术背景
- 两种模式：快速模式 + 引导模式
- 5种审查模式：文书完整性、时限合规性、信息一致性、程序合规性、自定义逻辑
- 自动验证内容格式
- 生成可视化流程图（Mermaid + ASCII）
- **新增**：自动推断推荐信息点清单，帮助用户了解需要从各文书中抽取的关键字段
- **新增**：输出文件包含免责声明，提醒人工核实

## 安装方法

```bash
# 添加市场
/plugin marketplace add breezewang19-lang/claude-marketplace

# 安装插件
/plugin install checkpoint-architect@checkpoint-marketplace
```

## 版本历史

- v1.0.0: 初始版本
