# 课程资料智能问答与学习总结助手

本项目是《AI智能体设计开发及应用》课程大作业，项目围绕大学生日常课程学习场景，设计并开发一个能够读取课程资料、回答学习问题、生成学习总结报告，并支持飞书机器人通知的 AI 智能体应用。

项目仓库地址：https://github.com/Iriyaaaahdhdj/Agent-application

## 1. 项目背景

在课程学习过程中，学生经常需要整理课堂笔记、教材片段、PPT 内容和实验说明等资料。随着课程资料增多，人工查找重点、归纳知识点和制定复习计划会变得低效。

本项目希望通过 AI 智能体辅助学生完成课程资料理解、重点提取、问题回答和学习总结，降低资料整理成本，提高复习效率。同时，项目结合飞书机器人通知功能，将学习总结推送到飞书群中，方便后续查看、提醒和协作。

## 2. 项目目标

本项目的目标是设计并实现一个简单可运行的课程学习智能体系统，具体包括：

- 支持读取本地课程资料文件。
- 支持用户通过 CLI 输入学习问题。
- 支持使用 mock 模式进行离线演示。
- 支持接入火山方舟豆包 API，生成更深入的课程回答。
- 自动生成课程资料摘要、核心知识点、问题回答和复习计划。
- 将结果保存为 Markdown 学习总结报告。
- 支持飞书机器人通知，将学习总结发送到飞书群。
- 提供测试记录，验证核心功能和异常情况处理。

## 3. 功能介绍

### 资料读取

程序默认读取：

```text
data/sample_course_notes.md
```

该文件作为课程资料输入，用于后续摘要、知识点提取和问答。

### 智能问答

用户可以在命令行中输入问题，系统会结合课程资料生成回答。

系统支持两种回答模式：

- `mock`：本地模拟 AI 函数，适合无网络或课堂演示。
- `ark`：调用火山方舟豆包 API，生成更深入的课程解释、例子、易混点分析和复习建议。

### 学习报告生成

程序会自动生成 Markdown 格式学习报告，保存到：

```text
outputs/summary_report.md
```

报告内容包括：

- 生成时间
- 生成模式
- 用户问题
- 资料摘要
- 核心知识点
- 问题回答
- 复习计划

### 飞书通知

系统可以读取学习总结报告，提取摘要、知识点和复习建议，并通过飞书机器人 Webhook 发送到飞书群。

如果没有配置真实 Webhook，系统会进入 mock 模式，在命令行打印飞书通知预览。

## 4. 智能体工作流

本项目的智能体工作流如下：

```text
用户输入课程资料和学习问题
        ↓
输入校验
        ↓
文本清洗
        ↓
调用 mock 函数或豆包 API
        ↓
生成课程摘要
        ↓
提取核心知识点
        ↓
生成问题回答
        ↓
生成复习计划
        ↓
保存 Markdown 学习报告
        ↓
飞书通知或 mock 通知预览
```

各步骤说明：

1. 输入校验：检查课程资料和用户问题是否为空。
2. 文本清洗：去除空行，整理课程资料文本。
3. 模型调用：根据 `--provider` 参数选择 mock 模式或豆包 API 模式。
4. 内容生成：生成摘要、知识点、回答和复习计划。
5. 报告保存：将结果写入 `outputs/summary_report.md`。
6. 飞书协同：根据 `--notify` 参数决定是否发送飞书通知。
7. 异常处理：处理文件不存在、资料为空、API 超时、Webhook 未配置等情况。

## 5. 技术栈

| 技术 | 用途 |
|---|---|
| Python | 项目主要开发语言 |
| argparse | CLI 参数解析 |
| pathlib | 文件路径处理 |
| urllib | 调用豆包 API 和飞书 Webhook |
| Markdown | 课程资料和报告格式 |
| 火山方舟豆包 API | 真实大模型问答与总结 |
| 飞书机器人 Webhook | 学习总结通知推送 |
| GitHub | 项目代码和文档管理 |

## 6. 项目结构

```text
Agent-application/
├── README.md
├── main.py
├── feishu_notify.py
├── requirements.txt
├── .gitignore
├── data/
│   ├── sample_course_notes.md
│   └── empty_notes.md
├── outputs/
│   └── summary_report.md
└── docs/
    └── 测试记录.md
```

主要文件说明：

- `main.py`：智能体主程序，负责资料读取、问答生成、报告保存和通知调度。
- `feishu_notify.py`：飞书机器人通知模块。
- `data/sample_course_notes.md`：示例课程资料。
- `data/empty_notes.md`：空资料测试样例。
- `outputs/summary_report.md`：智能体生成的学习总结报告。
- `docs/测试记录.md`：项目测试用例和测试记录。
- `requirements.txt`：项目依赖说明。

## 7. 安装依赖

当前版本主要使用 Python 标准库，无需安装第三方依赖。仍可执行以下命令完成依赖检查：

```bash
pip install -r requirements.txt
```

建议使用 Python 3.10 或以上版本运行。

## 8. CLI 运行方式

进入项目目录：

```powershell
cd C:\Users\Iriya\Desktop\智能体应用大作业\Agent-application
```

使用 mock 模式运行：

```bash
python main.py --provider mock --notify none --question "什么是智能体？"
```

使用豆包 API 模式运行。先配置 API Key：

```powershell
$env:ARK_API_KEY="你的豆包或火山方舟 API Key"
```

然后运行：

```bash
python main.py --provider ark --notify none --question "什么是智能体？它和普通聊天机器人有什么区别？"
```

使用自动模式：

```bash
python main.py --provider auto --question "智能体的核心组成是什么？"
```

如果检测到 `ARK_API_KEY`，程序会调用豆包 API；否则会自动使用 mock 模式。

指定课程资料文件：

```bash
python main.py --file data/sample_course_notes.md --question "智能体工作流包括哪些步骤？"
```

交互式输入问题：

```bash
python main.py
```

## 9. 飞书协同说明

本项目通过飞书自定义机器人 Webhook 实现学习总结通知。

### 飞书 mock 通知

不配置真实 Webhook，只打印通知预览：

```bash
python main.py --provider mock --notify mock --question "什么是智能体？"
```

### 真实飞书通知

在飞书群中添加自定义机器人，复制 Webhook 地址，然后在 PowerShell 中配置：

```powershell
$env:FEISHU_WEBHOOK_URL="你的飞书机器人 Webhook 地址"
```

运行：

```bash
python main.py --provider auto --notify webhook --question "什么是智能体？"
```

飞书群中会收到类似内容：

```text
【课程学习总结通知】

问题：
什么是智能体？

资料摘要：
...

核心知识点：
...

复习建议：
...
```

如果飞书机器人开启了关键词安全设置，建议关键词设置为：

```text
课程
```

当前版本暂未实现飞书签名校验，如果开启签名校验，需要继续扩展签名计算逻辑。

## 10. 测试说明

项目测试记录位于：

```text
docs/测试记录.md
```

已覆盖测试场景：

- 正常输入课程资料
- 用户提问明确
- 用户提问模糊
- 课程资料为空
- 问题超出资料范围
- 飞书 Webhook 未配置
- 输出报告是否成功生成

示例测试命令：

```bash
python main.py --provider mock --notify none --question "什么是智能体？"
```

```bash
python main.py --provider mock --notify none --file data/empty_notes.md --question "什么是智能体？"
```

```bash
python main.py --provider mock --notify auto --question "什么是智能体？"
```

测试结果表明，当前系统可以稳定完成课程资料读取、摘要生成、知识点提取、问题回答、复习计划生成、报告保存和飞书 mock 通知。

## 11. 项目展示截图说明

建议在提交或课堂展示时补充以下截图：

1. CLI 运行截图  
   展示执行 `python main.py --provider ark --notify none --question "什么是智能体？"` 后的终端输出。

2. 学习报告截图  
   展示 `outputs/summary_report.md` 中生成的摘要、知识点、回答和复习计划。

3. 飞书通知截图  
   展示飞书群中机器人发送的“课程学习总结通知”。

4. GitHub 仓库截图  
   展示项目目录结构、README、测试记录和代码文件。

截图可放在 `docs/` 或新建 `assets/` 目录中，例如：

```text
assets/
├── cli_run.png
├── summary_report.png
└── feishu_notify.png
```

## 12. 反思总结

通过本项目，我对 AI 智能体应用的设计和开发流程有了更完整的理解。

本项目从真实学习场景出发，将课程资料整理、智能问答、学习报告生成和飞书通知结合起来，形成了一个较完整的智能体工作流。开发过程中，系统不仅使用了大模型完成摘要、知识点提取和回答生成，也使用 Python 代码完成了文件读取、参数解析、报告保存、异常处理和飞书 Webhook 调用。

项目的主要收获包括：

- 理解了智能体不是单纯聊天，而是围绕目标完成多步骤任务。
- 学会了将大模型能力与代码工具结合起来。
- 学会了使用 CLI 管理程序输入、运行方式和测试流程。
- 学会了通过飞书机器人实现简单协同通知。
- 学会了为项目补充测试记录和异常处理说明。

当前项目仍有改进空间：

- 可以增加网页界面，让用户更方便地上传资料和输入问题。
- 可以支持更多课程资料格式，例如 PDF、Word 和表格。
- 可以增加飞书文档自动归档功能，而不仅是群通知。
- 可以增加自动化测试脚本，进一步提高项目稳定性。
- 可以完善飞书机器人签名校验，提高安全性。

总体来看，本项目较好地体现了 AI 智能体在学习场景中的应用价值，也完成了从场景分析、工作流设计、代码实现、工具协同、测试记录到项目文档整理的完整过程。
