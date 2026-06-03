import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


FEISHU_WEBHOOK_ENV_NAMES = ("FEISHU_WEBHOOK_URL", "FEISHU_BOT_WEBHOOK")


def read_report(report_path: Path) -> str:
    """Read the generated Markdown study report."""
    if not report_path.exists():
        raise FileNotFoundError(f"学习报告文件不存在：{report_path}")

    return report_path.read_text(encoding="utf-8")


def extract_markdown_section(markdown: str, heading: str) -> str:
    """Extract a second-level Markdown section by heading text."""
    pattern = rf"^##\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, markdown, flags=re.MULTILINE)
    if not match:
        return "未提取到相关内容。"

    content = match.group(1).strip()
    return content or "未提取到相关内容。"


def build_feishu_message(report: str) -> str:
    """Build a concise Feishu text message from the study report."""
    question = extract_markdown_section(report, "用户问题")
    question_type = extract_markdown_section(report, "问题类型")
    summary = extract_markdown_section(report, "针对本问题的资料摘要")
    key_points = extract_markdown_section(report, "针对本问题的核心知识点")
    adaptation_plan = extract_markdown_section(report, "智能体适应方案")
    review_plan = extract_markdown_section(report, "复习计划")

    return f"""【课程学习总结通知】

问题：
{question}

问题类型：
{question_type}

资料摘要：
{summary}

核心知识点：
{key_points}

智能体适应方案：
{adaptation_plan}

复习建议：
{review_plan}
"""


def get_webhook_from_env() -> str:
    """Read Feishu webhook URL from environment variables."""
    for env_name in FEISHU_WEBHOOK_ENV_NAMES:
        webhook = os.getenv(env_name, "").strip()
        if webhook:
            return webhook
    return ""


def send_feishu_text(webhook_url: str, message: str) -> dict:
    """Send a text message to a Feishu custom bot webhook."""
    payload = {
        "msg_type": "text",
        "content": {
            "text": message,
        },
    }
    request = urllib.request.Request(
        url=webhook_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"飞书 Webhook HTTP 错误：{error.code} {error_body}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"飞书 Webhook 网络连接失败：{error.reason}") from error

    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        return {"raw": response_text}

    status_code = result.get("StatusCode", result.get("code", 0))
    if status_code not in (0, None):
        raise RuntimeError(f"飞书 Webhook 返回异常：{result}")

    return result


def notify_from_report(
    report_path: Path,
    webhook_url: str = "",
    mode: str = "auto",
) -> tuple[str, str]:
    """Notify Feishu from a generated report.

    mode:
    - none: skip notification
    - mock: print message only
    - webhook: require webhook and send
    - auto: send when webhook exists, otherwise mock
    """
    if mode == "none":
        return "none", "已跳过飞书通知。"

    report = read_report(report_path)
    message = build_feishu_message(report)
    webhook = webhook_url.strip() or get_webhook_from_env()

    if mode == "mock" or (mode == "auto" and not webhook):
        print("\n--- 飞书通知 mock 预览 ---")
        print(message)
        return "mock", message

    if not webhook:
        raise RuntimeError("未配置飞书 Webhook，请设置 FEISHU_WEBHOOK_URL 或使用 mock 模式。")

    send_feishu_text(webhook, message)
    return "webhook", "飞书通知发送成功。"
