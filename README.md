# 课程资料智能问答与学习总结助手

本项目是《AI智能体设计开发及应用》课程大作业，面向大学生日常课程学习场景，开发一个基于豆包 API 的课程资料智能问答与学习总结助手。

项目仓库地址：https://github.com/Iriyaaaahdhdj/Agent-application

## 1. 项目背景

学生在复习课程时，经常需要从课堂笔记、教材片段和课程资料中查找重点内容。如果每次都人工整理摘要、理解概念、归纳知识点和制定复习计划，会消耗大量时间。

本项目通过 AI 智能体帮助学生围绕具体学习问题完成资料理解、问题回答、报告生成和飞书通知。系统不再使用固定 mock 模板，而是直接调用豆包 API，根据不同问题动态生成不同的资料摘要、核心知识点、回答内容和适应方案。

## 2. 项目目标

- 读取本地课程资料文件。
- 接收用户在命令行输入的学习问题。
- 调用豆包 API 进行真实大模型分析。
- 根据不同问题识别问题类型。
- 针对本次问题生成差异化资料摘要、知识点、回答和复习计划。
- 生成 Markdown 学习总结报告。
- 支持飞书机器人通知或通知 mock 预览。
- 记录测试用例和异常处理情况。

## 3. 功能介绍

### 课程资料读取

默认读取：

```text
data/sample_course_notes.md
```

也可以通过 `--file` 指定其他课程资料文件。

### 豆包 API 智能问答

系统只保留豆包 API 模式。用户提出不同问题时，智能体会先判断问题类型，例如：

- 概念解释
- 对比分析
- 流程梳理
- 应用举例
- 模糊问题
- 资料外延伸

然后根据问题类型生成不同的回答策略。

### 学习总结报告

报告保存到：

```text
outputs/summary_report.md
```

报告内容包括：

- 生成时间
- 生成模式
- 用户问题
- 问题类型
- 针对本问题的资料摘要
- 针对本问题的核心知识点
- 问题回答
- 智能体适应方案
- 复习计划

### 飞书通知

系统可以读取学习报告，并将问题、问题类型、摘要、知识点、适应方案和复习建议整理为飞书通知文本。

## 4. 智能体工作流

```text
用户输入课程资料和学习问题
        ↓
输入校验
        ↓
文本清洗
        ↓
调用豆包 API
        ↓
判断问题类型
        ↓
生成针对本问题的资料摘要
        ↓
提取针对本问题的核心知识点
        ↓
生成深度问题回答
        ↓
生成智能体适应方案
        ↓
生成定制复习计划
        ↓
保存 Markdown 学习报告
        ↓
飞书通知或通知预览
```

## 5. 技术栈

| 技术 | 用途 |
|---|---|
| Python | 项目主要开发语言 |
| argparse | CLI 参数解析 |
| pathlib | 文件路径处理 |
| urllib | 调用豆包 API 和飞书 Webhook |
| Markdown | 课程资料和报告格式 |
| 火山方舟豆包 API | 真实大模型分析、问答和总结 |
| 飞书机器人 Webhook | 学习总结通知 |
| GitHub | 项目代码与文档管理 |

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

## 7. 安装依赖

当前版本使用 Python 标准库调用豆包 API 和飞书 Webhook，无需第三方依赖。

```bash
pip install -r requirements.txt
```

建议使用 Python 3.10 或以上版本。

## 8. CLI 运行方式

进入项目目录：

```powershell
cd C:\Users\Iriya\Desktop\智能体应用大作业\Agent-application
```

配置豆包 API Key：

```powershell
$env:ARK_API_KEY="你的豆包或火山方舟 API Key"
```

运行智能体：

```bash
python main.py --notify none --question "什么是智能体？它和普通聊天机器人有什么区别？"
```

换一个问题运行：

```bash
python main.py --notify none --question "智能体工作流包括哪些步骤？"
```

指定课程资料：

```bash
python main.py --file data/sample_course_notes.md --notify none --question "工具调用在智能体中有什么作用？"
```

交互式运行：

```bash
python main.py
```

## 9. 飞书协同说明

飞书通知 mock 预览：

```bash
python main.py --notify mock --question "什么是智能体？"
```

配置真实飞书 Webhook：

```powershell
$env:FEISHU_WEBHOOK_URL="你的飞书机器人 Webhook 地址"
```

发送到飞书群：

```bash
python main.py --notify webhook --question "什么是智能体？"
```

如果飞书机器人开启关键词安全设置，建议关键词设置为：

```text
课程
```

当前版本暂未实现飞书签名校验。如果开启签名校验，需要继续扩展签名计算逻辑。

## 10. 测试说明

测试记录位于：

```text
docs/测试记录.md
```

已覆盖场景：

- 正常输入课程资料
- 用户提问明确
- 用户提问模糊
- 课程资料为空
- 问题超出资料范围
- 飞书 Webhook 未配置
- 输出报告是否成功生成

注意：当前主程序已改为只调用豆包 API，因此正式运行测试前需要配置 `ARK_API_KEY`。

## 11. 项目展示截图说明

建议补充以下截图用于课堂展示：

1. CLI 运行截图：展示不同问题生成不同报告。
2. 学习报告截图：展示问题类型、资料摘要、核心知识点、回答和适应方案。
3. 飞书通知截图：展示飞书群里的课程学习总结通知。
4. GitHub 仓库截图：展示 README、代码、测试记录和输出报告。

截图可放在：

```text
assets/
├── cli_run.png
├── summary_report.png
└── feishu_notify.png
```

## 12. 反思总结

本项目体现了 AI 智能体在学习场景中的应用价值。相比普通问答程序，本项目强调围绕用户问题进行动态处理：先识别问题类型，再根据问题生成对应摘要、知识点、回答、适应方案和复习计划。

通过本项目，我学习了如何将大模型 API、CLI、文件处理、Markdown 报告和飞书机器人通知组合成一个完整的智能体工作流。项目后续仍可继续扩展，例如增加网页界面、支持 PDF 上传、接入飞书文档归档、完善自动化测试和飞书签名校验。
