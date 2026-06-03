import argparse
import re
from datetime import datetime
from pathlib import Path


DEFAULT_NOTES_FILE = Path("data/sample_course_notes.md")
DEFAULT_OUTPUT_FILE = Path("outputs/summary_report.md")


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
    """Simulate an AI answer based on the course material and user question."""
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
        "当前课程资料中没有找到与该问题直接对应的内容。"
        "建议补充更完整的课程笔记或教材片段后再次提问。"
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


def build_report(
    question: str,
    summary: str,
    key_points: list[str],
    answer: str,
    review_plan: list[str],
) -> str:
    """Build the final Markdown study report."""
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# 课程学习总结报告

## 生成时间

{generated_at}

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


def run_assistant(notes_file: Path, question: str, output_file: Path) -> str:
    """Run the course QA assistant workflow."""
    raw_text = read_course_notes(notes_file)
    course_text = clean_text(raw_text)

    if not course_text:
        raise ValueError("课程资料为空，请先补充 data/sample_course_notes.md。")
    if not question.strip():
        raise ValueError("用户问题为空，请输入一个明确的学习问题。")

    summary = mock_generate_summary(course_text)
    key_points = mock_extract_key_points(course_text)
    answer = mock_answer_question(course_text, question)
    review_plan = mock_generate_review_plan(key_points, question)
    report = build_report(question, summary, key_points, answer, review_plan)
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
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    question = args.question.strip() or input("请输入你的学习问题：").strip()

    try:
        report = run_assistant(args.file, question, args.output)
    except (FileNotFoundError, ValueError) as error:
        print(f"运行失败：{error}")
        return

    print("智能体运行完成。")
    print(f"学习报告已保存到：{args.output}")
    print("\n--- 报告预览 ---")
    print(report)


if __name__ == "__main__":
    main()
