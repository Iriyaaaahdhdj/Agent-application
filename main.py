import argparse
import json
import os
import re
import socket
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from feishu_notify import notify_from_report


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_NOTES_FILE = BASE_DIR / "data" / "sample_course_notes.md"
DEFAULT_OUTPUT_FILE = BASE_DIR / "outputs" / "summary_report.md"
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
DEFAULT_ARK_MODEL = "doubao-seed-2-0-lite-260215"


def read_course_notes(file_path: Path) -> str:
    """Read course notes from a Markdown file."""
    if not file_path.exists():
        raise FileNotFoundError(f"课程资料文件不存在：{file_path}")

    return file_path.read_text(encoding="utf-8")


def clean_text(text: str) -> str:
    """Clean blank lines and repeated spaces while keeping Markdown structure."""
    lines = [line.strip() for line in text.splitlines()]
    useful_lines = [line for line in lines if line]
    return "\n".join(useful_lines)


def split_sentences(text: str) -> list[str]:
    """Split Chinese and English text into simple sentence units."""
    sentences = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            continue
        line = re.sub(r"^\d+[.、]\s*", "", line)
        if not line:
            continue

        parts = re.split(r"(?<=[。！？!?；;])\s*", line)
        sentences.extend(part.strip() for part in parts if part.strip())

    return [sentence for sentence in sentences if len(sentence) >= 8]


def mock_generate_summary(course_text: str) -> str:
    """Simulate an AI summary by selecting representative sentences."""
    sentences = split_sentences(course_text)
    if not sentences:
        return "当前课程资料为空，无法生成摘要。"

    selected = sentences[:3]
    summary = " ".join(selected)
    if len(summary) > 220:
        summary = summary[:220].rstrip() + "……"

    return f"本次课程资料主要围绕以下内容展开：{summary}"


def mock_extract_key_points(course_text: str) -> list[str]:
    """Simulate AI key point extraction with common course keywords."""
    keyword_patterns = [
        "智能体",
        "大模型",
        "工作流",
        "输入校验",
        "文本清洗",
        "内容摘要",
        "知识点提取",
        "问题理解",
        "答案生成",
        "复习计划",
        "飞书",
        "CLI",
        "异常处理",
        "工具调用",
    ]

    points = []
    for keyword in keyword_patterns:
        if keyword in course_text and keyword not in points:
            points.append(keyword)

    if not points:
        sentences = split_sentences(course_text)
        points = [sentence[:30] for sentence in sentences[:5]]

    return points[:8]


def mock_answer_question(course_text: str, question: str) -> str:
    """Simulate an AI answer based on notes, with a simple general fallback."""
    question = question.strip()
    if not question:
        return "未检测到有效问题，请重新输入学习问题。"

    matched_sentences = []
    keywords = extract_question_keywords(question)
    for sentence in split_sentences(course_text):
        if any(keyword in sentence for keyword in keywords):
            matched_sentences.append(sentence)

    if matched_sentences:
        matched_sentences.sort(
            key=lambda sentence: sum(keyword in sentence for keyword in keywords),
            reverse=True,
        )
        evidence = " ".join(matched_sentences[:3])
        return (
            "根据课程资料，可以这样理解："
            f"{evidence} "
            "因此，回答该问题时应优先结合资料中的概念、流程和应用场景进行说明。"
        )

    return (
        "课程资料中没有找到与该问题直接对应的内容。"
        "如果使用豆包 API 模式，系统会基于通用知识继续提供解答；"
        "当前 mock 模式仅能给出有限的演示回答。"
    )


def extract_question_keywords(question: str) -> list[str]:
    """Extract simple Chinese keywords from a question."""
    known_terms = [
        "智能体",
        "聊天机器人",
        "普通聊天机器人",
        "大模型",
        "工作流",
        "工具调用",
        "输入校验",
        "文本清洗",
        "内容摘要",
        "知识点提取",
        "问题理解",
        "答案生成",
        "复习计划",
        "飞书",
        "异常处理",
    ]

    keywords = [term for term in known_terms if term in question]
    if keywords:
        return keywords

    stop_words = {
        "什么",
        "为什么",
        "怎么",
        "如何",
        "哪些",
        "区别",
        "联系",
        "是",
        "的",
        "和",
        "与",
        "请",
        "说明",
        "解释",
    }
    tokens = re.findall(r"[\u4e00-\u9fa5A-Za-z0-9]+", question)
    for token in tokens:
        if token not in stop_words and len(token) >= 2:
            keywords.append(token)
    return keywords or [question]


def mock_generate_review_plan(key_points: list[str], question: str) -> list[str]:
    """Generate a simple review plan from key points and the user question."""
    first_points = "、".join(key_points[:3]) if key_points else "课程核心概念"

    return [
        f"第一步：先复习 {first_points}，理解本节课程的基础概念。",
        f"第二步：围绕问题“{question}”整理自己的回答，并尝试用 3 句话复述。",
        "第三步：根据知识点列表制作自测题，检查是否能独立解释概念和流程。",
        "第四步：复习结束后查看生成的学习报告，补充遗漏的课堂笔记。",
    ]


def call_doubao_agent(course_text: str, question: str, model: str) -> dict:
    """Call Doubao through Volcengine Ark's chat completions API."""
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 ARK_API_KEY 环境变量，无法调用豆包 API。")

    prompt = f"""你是一个“深度课程助教型”AI 智能体，目标不是简单复述资料，而是帮助学生真正理解课程内容。

请根据以下规则回答学生问题：
1. 如果学生问题与课程资料相关，必须优先结合课程资料回答，再使用通用知识进行补充解释。
2. 如果课程资料没有覆盖该问题，允许使用你的通用知识进行解答，但必须在 answer 开头说明：“课程资料未覆盖该问题，以下为通用解答：”。
3. 不要因为资料中没有完全相同的原句就拒绝回答；只要概念相关，就应该结合资料进行推理和讲解。
4. 回答要适合大学课程学习场景，不能只给一句话结论，要帮助学生理解“是什么、为什么、怎么用、容易和什么混淆”。
5. 输出必须是 JSON，不要输出 Markdown 代码块，不要在 JSON 外添加任何解释。

JSON 格式如下：
{{
  "summary": "课程资料摘要，150-260字。要说明本资料主要讲了什么、各部分之间有什么关系。",
  "key_points": [
    "知识点1：用一句话解释含义和学习价值",
    "知识点2：用一句话解释含义和学习价值",
    "知识点3：用一句话解释含义和学习价值"
  ],
  "answer": "针对学生问题的深度回答，建议 500-900 字。必须包含：1. 直接结论；2. 课程资料依据；3. 分点解释；4. 一个具体例子；5. 易混点或常见误区；6. 最后用一句话总结。可以在字符串中使用换行和编号。",
  "review_plan": [
    "复习建议1：说明先复习什么以及为什么",
    "复习建议2：说明如何自测",
    "复习建议3：说明如何用案例巩固",
    "复习建议4：指出容易混淆的地方"
  ]
}}

课程资料：
{course_text}

学生问题：
{question}
"""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是严谨、耐心、讲解深入的大学课程助教。回答要有教学价值，"
                    "优先基于课程资料，同时可以用通用知识补充背景、例子和辨析。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        url=f"{ARK_BASE_URL}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"豆包 API HTTP 错误：{error.code} {error_body}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"豆包 API 网络连接失败：{error.reason}") from error
    except TimeoutError as error:
        raise RuntimeError("豆包 API 响应超时，请稍后重试或减少问题复杂度。") from error
    except socket.timeout as error:
        raise RuntimeError("豆包 API 响应超时，请稍后重试或减少问题复杂度。") from error

    try:
        content = response_data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"豆包 API 返回结构异常：{response_data}") from error

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"豆包 API 返回内容不是有效 JSON：{content}") from error

    required_fields = {"summary", "key_points", "answer", "review_plan"}
    if not required_fields.issubset(result):
        raise RuntimeError("豆包 API 返回字段不完整。")

    return result


def generate_with_mock(course_text: str, question: str) -> dict:
    """Generate assistant result with local mock functions."""
    key_points = mock_extract_key_points(course_text)
    return {
        "summary": mock_generate_summary(course_text),
        "key_points": key_points,
        "answer": mock_answer_question(course_text, question),
        "review_plan": mock_generate_review_plan(key_points, question),
    }


def generate_agent_result(
    course_text: str,
    question: str,
    provider: str,
    model: str,
) -> tuple[dict, str]:
    """Generate result with Doubao API or local mock fallback."""
    if provider == "mock":
        return generate_with_mock(course_text, question), "mock"

    if provider == "ark" or os.getenv("ARK_API_KEY"):
        try:
            return call_doubao_agent(course_text, question, model), "ark"
        except RuntimeError as error:
            if provider == "ark":
                raise
            print(f"豆包 API 调用失败，已切换为 mock 模式：{error}")

    return generate_with_mock(course_text, question), "mock"


def build_report(
    question: str,
    summary: str,
    key_points: list[str],
    answer: str,
    review_plan: list[str],
    provider: str,
) -> str:
    """Build the final Markdown study report."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 课程学习总结报告

## 生成时间

{generated_at}

## 生成模式

{provider}

## 用户问题

{question}

## 资料摘要

{summary}

## 核心知识点

{chr(10).join(f"{index}. {point}" for index, point in enumerate(key_points, start=1))}

## 问题回答

{answer}

## 复习计划

{chr(10).join(f"- {item}" for item in review_plan)}
"""


def save_report(report: str, output_path: Path) -> None:
    """Save report to a Markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")


def run_assistant(
    notes_file: Path,
    question: str,
    output_file: Path,
    provider: str,
    model: str,
) -> str:
    """Run the course QA assistant workflow."""
    raw_text = read_course_notes(notes_file)
    course_text = clean_text(raw_text)

    if not course_text:
        raise ValueError("课程资料为空，请先补充 data/sample_course_notes.md。")
    if not question.strip():
        raise ValueError("用户问题为空，请输入一个明确的学习问题。")

    result, used_provider = generate_agent_result(course_text, question, provider, model)
    report = build_report(
        question=question,
        summary=result["summary"],
        key_points=result["key_points"],
        answer=result["answer"],
        review_plan=result["review_plan"],
        provider=used_provider,
    )
    save_report(report, output_file)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="课程资料智能问答与学习总结助手")
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_NOTES_FILE,
        help="课程资料 Markdown 文件路径，默认 data/sample_course_notes.md",
    )
    parser.add_argument(
        "--question",
        type=str,
        default="",
        help="学生问题。如果不填写，程序会在命令行中提示输入。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="学习报告输出路径，默认 outputs/summary_report.md",
    )
    parser.add_argument(
        "--provider",
        choices=["auto", "mock", "ark"],
        default="auto",
        help="模型提供方：auto 自动选择，mock 本地模拟，ark 调用豆包 API。",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.getenv("ARK_MODEL", DEFAULT_ARK_MODEL),
        help="火山方舟模型 ID，默认 doubao-seed-2-0-lite-260215。",
    )
    parser.add_argument(
        "--notify",
        choices=["auto", "mock", "webhook", "none"],
        default="auto",
        help="飞书通知模式：auto 自动选择，mock 打印预览，webhook 发送飞书，none 跳过。",
    )
    parser.add_argument(
        "--feishu-webhook",
        type=str,
        default="",
        help="飞书机器人 Webhook 地址。也可通过 FEISHU_WEBHOOK_URL 环境变量配置。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    question = args.question.strip() or input("请输入你的学习问题：").strip()

    try:
        report = run_assistant(args.file, question, args.output, args.provider, args.model)
    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"运行失败：{error}")
        return

    print("智能体运行完成。")
    print(f"学习报告已保存到：{args.output}")
    print("\n--- 报告预览 ---")
    print(report)

    try:
        notify_mode, notify_result = notify_from_report(
            report_path=args.output,
            webhook_url=args.feishu_webhook,
            mode=args.notify,
        )
    except RuntimeError as error:
        print(f"飞书通知失败：{error}")
        return

    if notify_mode == "webhook":
        print(notify_result)
    elif notify_mode == "none":
        print(notify_result)


if __name__ == "__main__":
    main()
