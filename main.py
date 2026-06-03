import argparse
import http.client
import json
import os
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


def call_doubao_agent(course_text: str, question: str, model: str) -> dict:
    """Call Doubao through Volcengine Ark's chat completions API."""
    api_key = os.getenv("ARK_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 ARK_API_KEY 环境变量，无法调用豆包 API。")

    prompt = f"""你是一个“课程资料智能问答与学习总结助手”，也是一个会根据学生问题动态调整讲解策略的课程助教。

请严格围绕“本次学生问题”生成学习报告。注意：不同问题必须给出不同的资料摘要、核心知识点、回答重点、适应方案和复习计划，不能机械复用同一套模板。

处理规则：
1. 先判断学生问题类型，例如：概念解释、流程梳理、对比分析、应用举例、问题排查、资料外延伸、模糊问题。
2. 如果问题与课程资料相关，优先结合资料回答，并根据问题类型选择讲解角度。
3. 如果课程资料没有覆盖该问题，可以使用通用知识补充，但必须在 answer 开头说明：“课程资料未覆盖该问题，以下为通用解答：”。
4. 如果问题模糊，不要直接复用资料摘要，要先指出问题不明确，再给出可理解的方向和追问建议。
5. summary 必须是“针对本次问题的资料摘要”，只总结和本次问题最相关的资料内容。
6. key_points 必须是“针对本次问题的核心知识点”，不要每次输出同一批知识点。
7. adaptation_plan 必须说明本智能体为什么采用这种回答策略，以及用户下一步应该如何补充输入或学习。
8. review_plan 必须根据本次问题定制，不能泛泛地写“复习知识点”。
9. 输出必须是 JSON，不要输出 Markdown 代码块，不要在 JSON 外添加任何解释。

JSON 格式如下：
{{
  "question_type": "本次问题类型，例如：概念解释 / 对比分析 / 流程梳理 / 应用举例 / 模糊问题 / 资料外延伸",
  "summary": "针对本次问题的资料摘要，120-260字。必须围绕问题筛选资料内容，而不是重复完整课程摘要。",
  "key_points": [
    "与本次问题强相关的知识点1：说明含义和为什么相关",
    "与本次问题强相关的知识点2：说明含义和为什么相关",
    "与本次问题强相关的知识点3：说明含义和为什么相关"
  ],
  "answer": "针对学生问题的深度回答，建议500-900字。根据问题类型组织内容，可包含定义、依据、步骤、对比、例子、误区、结论。不要空泛。",
  "adaptation_plan": [
    "适应方案1：说明本次回答如何根据问题类型调整",
    "适应方案2：说明如果用户想获得更准确结果，需要补充什么资料或问题条件",
    "适应方案3：说明后续学习或追问方向"
  ],
  "review_plan": [
    "复习建议1：针对本问题先复习什么",
    "复习建议2：如何自测本问题是否掌握",
    "复习建议3：用什么案例或练习巩固",
    "复习建议4：指出本问题最容易混淆的地方"
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
                    "你是严谨、耐心、讲解深入的大学课程助教。"
                    "你必须根据每次学生问题动态调整摘要、知识点、回答和复习计划。"
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.45,
        "max_tokens": 1800,
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
    except http.client.RemoteDisconnected as error:
        raise RuntimeError("豆包 API 连接被远端断开，请稍后重试。") from error

    try:
        content = response_data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError(f"豆包 API 返回结构异常：{response_data}") from error

    try:
        result = json.loads(content)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"豆包 API 返回内容不是有效 JSON：{content}") from error

    return normalize_agent_result(result, question)


def ensure_list(value: object) -> list[str]:
    """Convert model output into a clean string list."""
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [line.strip("- ").strip() for line in value.splitlines() if line.strip()]
    return []


def normalize_agent_result(result: dict, question: str) -> dict:
    """Fill missing model fields so the workflow remains stable."""
    question_type = str(result.get("question_type") or "未明确分类").strip()
    summary = str(
        result.get("summary")
        or "豆包 API 未返回单独的资料摘要，建议检查提示词或重新运行。"
    ).strip()
    answer = str(
        result.get("answer")
        or "豆包 API 未返回完整回答，请重新运行或补充更明确的问题。"
    ).strip()

    key_points = ensure_list(result.get("key_points"))
    if not key_points:
        key_points = [
            "本次问题相关知识点未被模型单独列出，建议结合问题回答部分进行整理。"
        ]

    adaptation_plan = ensure_list(result.get("adaptation_plan"))
    if not adaptation_plan:
        adaptation_plan = [
            f"本次问题“{question}”需要结合课程资料进行针对性理解。",
            "如果希望获得更精确的回答，可以补充具体章节、概念或使用场景。",
            "后续可继续追问定义、流程、案例或对比分析等方向。",
        ]

    review_plan = ensure_list(result.get("review_plan"))
    if not review_plan:
        review_plan = [
            "先阅读本次回答中的核心概念和关键步骤。",
            "尝试用自己的话复述问题答案。",
            "结合课程资料补充遗漏的例子和细节。",
        ]

    return {
        "question_type": question_type,
        "summary": summary,
        "key_points": key_points,
        "answer": answer,
        "adaptation_plan": adaptation_plan,
        "review_plan": review_plan,
    }


def build_report(
    question: str,
    question_type: str,
    summary: str,
    key_points: list[str],
    answer: str,
    adaptation_plan: list[str],
    review_plan: list[str],
) -> str:
    """Build the final Markdown study report."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 课程学习总结报告

## 生成时间

{generated_at}

## 生成模式

豆包 API

## 用户问题

{question}

## 问题类型

{question_type}

## 针对本问题的资料摘要

{summary}

## 针对本问题的核心知识点

{chr(10).join(f"{index}. {point}" for index, point in enumerate(key_points, start=1))}

## 问题回答

{answer}

## 智能体适应方案

{chr(10).join(f"- {item}" for item in adaptation_plan)}

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
    model: str,
) -> str:
    """Run the course QA assistant workflow."""
    raw_text = read_course_notes(notes_file)
    course_text = clean_text(raw_text)

    if not course_text:
        raise ValueError(f"课程资料为空，请补充资料文件：{notes_file}")
    if not question.strip():
        raise ValueError("用户问题为空，请输入一个明确的学习问题。")

    result = call_doubao_agent(course_text, question, model)
    report = build_report(
        question=question,
        question_type=result["question_type"],
        summary=result["summary"],
        key_points=result["key_points"],
        answer=result["answer"],
        adaptation_plan=result["adaptation_plan"],
        review_plan=result["review_plan"],
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
        report = run_assistant(args.file, question, args.output, args.model)
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
