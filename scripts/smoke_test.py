from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from main import build_report, clean_text, normalize_agent_result, read_course_notes


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def assert_contains(text: str, expected: str, message: str) -> None:
    if expected not in text:
        raise AssertionError(f"{message}: {expected!r} not found")


def test_clean_text() -> None:
    raw = "  # Title  \n\n  line one  \n   \nline two\n"
    assert_equal(clean_text(raw), "# Title\nline one\nline two", "clean_text should trim blank lines")


def test_read_course_notes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "notes.md"
        path.write_text("# Notes\ncontent", encoding="utf-8")
        assert_contains(read_course_notes(path), "content", "read_course_notes should read UTF-8 files")


def test_normalize_agent_result() -> None:
    result = normalize_agent_result(
        {
            "question_type": "概念解释",
            "summary": "summary",
            "key_points": ["point"],
            "answer": "answer",
            "adaptation_plan": "- plan a\n- plan b",
            "review_plan": ["review"],
        },
        "什么是智能体？",
    )
    assert_equal(result["question_type"], "概念解释", "question_type should be preserved")
    assert_equal(result["adaptation_plan"], ["plan a", "plan b"], "string lists should be normalized")


def test_build_report() -> None:
    report = build_report(
        question="什么是智能体？",
        question_type="概念解释",
        summary="资料摘要",
        key_points=["知识点一", "知识点二"],
        answer="回答正文",
        adaptation_plan=["适应方案"],
        review_plan=["复习建议"],
    )
    for section in ["用户问题", "问题类型", "资料摘要", "核心知识点", "问题回答", "复习计划"]:
        assert_contains(report, section, f"report should contain section {section}")


def main() -> None:
    tests = [
        test_clean_text,
        test_read_course_notes,
        test_normalize_agent_result,
        test_build_report,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(json.dumps({"ok": True, "tests": len(tests)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
