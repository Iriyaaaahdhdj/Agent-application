from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_PATH = ROOT / "data" / "eval_cases.csv"
OUT_PATH = ROOT / "docs" / "大模型评测结果汇总.md"


BOOLEAN_FIELDS = ("format_pass", "refusal_pass")
SCORE_FIELDS = ("human_score", "answer_groundedness")


def as_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def pct(value: float) -> str:
    return f"{value:.1%}"


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_rows() -> list[dict[str, str]]:
    with CASE_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def summarize_group(rows: list[dict[str, str]]) -> dict[str, float]:
    total = len(rows)
    scores = [float(row["human_score"]) for row in rows]
    groundedness = [float(row["answer_groundedness"]) for row in rows]
    return {
        "cases": total,
        "avg_score": avg(scores),
        "good_rate": sum(score >= 4 for score in scores) / total,
        "groundedness": avg(groundedness),
        "format_pass_rate": sum(as_bool(row["format_pass"]) for row in rows) / total,
        "refusal_pass_rate": sum(as_bool(row["refusal_pass"]) for row in rows) / total,
        "avg_latency_ms": avg([float(row["latency_ms"]) for row in rows]),
    }


def group_by(rows: list[dict[str, str]], field: str) -> dict[str, list[dict[str, str]]]:
    result: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        result[row[field]].append(row)
    return dict(result)


def render_summary_table(title: str, grouped: dict[str, list[dict[str, str]]]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| 分组 | 样例数 | 平均人工分 | 4分及以上 | 依据充分性 | 格式通过率 | 拒答通过率 | 平均耗时 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, items in sorted(grouped.items()):
        s = summarize_group(items)
        lines.append(
            "| {name} | {cases:.0f} | {avg_score:.2f} | {good_rate} | {groundedness:.2f} | {format_pass_rate} | {refusal_pass_rate} | {latency:.0f}ms |".format(
                name=name,
                cases=s["cases"],
                avg_score=s["avg_score"],
                good_rate=pct(s["good_rate"]),
                groundedness=s["groundedness"],
                format_pass_rate=pct(s["format_pass_rate"]),
                refusal_pass_rate=pct(s["refusal_pass_rate"]),
                latency=s["avg_latency_ms"],
            )
        )
    lines.append("")
    return lines


def main() -> None:
    rows = load_rows()
    badcases = Counter(row["badcase_type"] for row in rows if row["badcase_type"])
    by_version = group_by(rows, "prompt_version")
    by_task = group_by(rows, "task_group")
    by_scope = group_by(rows, "source_scope")
    total = summarize_group(rows)

    lines = [
        "# 大模型评测结果汇总",
        "",
        "数据来源：`data/eval_cases.csv`。该评测集用于复盘课程资料问答 Agent 的回答质量，不代表真实线上用户数据。",
        "",
        "## 评测口径",
        "",
        "- `human_score`：人工可用性评分，1-5 分。",
        "- `answer_groundedness`：回答是否基于项目资料和代码事实，1-5 分。",
        "- `format_pass`：是否符合指定输出格式。",
        "- `refusal_pass`：资料缺失、隐私、安全边界问题是否正确拒答。",
        "- `latency_ms`：单轮生成耗时记录，用于观察体验风险。",
        "",
        "## 总体表现",
        "",
        f"- 样例数：{total['cases']:.0f}",
        f"- 平均人工分：{total['avg_score']:.2f}",
        f"- 4 分及以上占比：{pct(total['good_rate'])}",
        f"- 平均依据充分性：{total['groundedness']:.2f}",
        f"- 格式通过率：{pct(total['format_pass_rate'])}",
        f"- 拒答通过率：{pct(total['refusal_pass_rate'])}",
        f"- 平均耗时：{total['avg_latency_ms']:.0f}ms",
        "",
    ]

    lines.extend(render_summary_table("按 Prompt 版本", by_version))
    lines.extend(render_summary_table("按任务类型", by_task))
    lines.extend(render_summary_table("按资料覆盖范围", by_scope))

    lines.extend(
        [
            "## Badcase Top",
            "",
            "| 类型 | 数量 | 典型原因 | 下一步动作 |",
            "|---|---:|---|---|",
        ]
    )

    root_causes = {
        "回答泛化": ("Prompt 没有强制绑定项目资料和用户任务", "按任务类型拆模板，要求先判断用户意图再回答"),
        "引用不明确": ("当前资料未做片段编号，回答缺少来源字段", "增加资料切分、片段 id 和引用输出"),
        "资料缺失仍回答": ("模型倾向用通识补全，拒答边界不够硬", "增加资料覆盖判断和拒答测试集"),
        "结构不稳定": ("JSON/表格等格式约束缺少后置校验", "增加 schema 校验和失败重试"),
    }
    for name, count in badcases.most_common():
        cause, action = root_causes.get(name, ("需要继续复盘", "补充测试样例"))
        lines.append(f"| {name} | {count} | {cause} | {action} |")

    lines.extend(
        [
            "",
            "## 迭代结论",
            "",
            "1. V1 能完成基础问答，但在资料缺失和格式约束场景下不稳定。",
            "2. V2 引入任务类型拆分后，回答结构和项目展示类任务明显改善。",
            "3. V3 增加资料约束和拒答规则后，边界问题表现更稳，但仍需要接入分段引用和 schema 校验。",
            "",
            "## 后续开发 Backlog",
            "",
            "| 优先级 | 需求 | 验收标准 |",
            "|---|---|---|",
            "| P0 | 资料分段和片段编号 | 回答中能返回引用片段 id |",
            "| P0 | 结构化输出校验 | JSON 任务格式通过率达到 95% 以上 |",
            "| P1 | 用户反馈表 | 支持记录有用/无用和失败原因 |",
            "| P1 | RAG 检索 | 能按问题召回相关资料片段 |",
            "| P2 | 简单 Web 页面 | 支持资料上传、提问和报告预览 |",
        ]
    )

    OUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
