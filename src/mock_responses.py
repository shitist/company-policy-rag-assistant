from __future__ import annotations

from typing import Dict, List, Sequence

from src.prompts import get_refusal_text, normalize_response_language


TOPIC_KEYWORDS = {
    "ai_tool_policy": [
        "ai",
        "llm",
        "gemini",
        "tool",
        "prompt",
        "draft",
        "人工知能",
        "aiツール",
        "下書き",
        "生成",
        "AI工具",
        "草稿",
    ],
    "sns_guideline": [
        "sns",
        "social",
        "post",
        "posting",
        "reply",
        "dm",
        "投稿",
        "返信",
        "ソーシャル",
        "发布",
        "社媒",
    ],
    "information_security": [
        "security",
        "password",
        "credential",
        "device",
        "access",
        "セキュリティ",
        "パスワード",
        "認証",
        "安全",
        "密码",
    ],
    "copyright_material": [
        "copyright",
        "license",
        "image",
        "music",
        "asset",
        "rights",
        "著作権",
        "素材",
        "ライセンス",
        "版权",
    ],
    "talent_privacy": [
        "talent",
        "privacy",
        "private",
        "rumor",
        "personal",
        "タレント",
        "プライバシー",
        "噂",
        "隐私",
        "艺人",
    ],
    "fan_content": [
        "fan",
        "submission",
        "artwork",
        "ugc",
        "repost",
        "ファン",
        "投稿作品",
        "二次利用",
        "粉丝",
        "投稿",
    ],
    "expense_policy": [
        "expense",
        "reimburse",
        "receipt",
        "tier",
        "経費",
        "精算",
        "領収書",
        "报销",
        "费用",
    ],
    "incident_response": [
        "incident",
        "controversy",
        "criticism",
        "holding",
        "crisis",
        "炎上",
        "事故",
        "初動",
        "危機",
        "舆情",
    ],
}


MOCK_ANSWERS = {
    "en": {
        "ai_tool_policy": (
            "AI tools may be used for drafting, rewriting, summarizing approved sample materials, "
            "and brainstorming, but the output must remain a draft until reviewed by a human. "
            "Do not enter confidential, private, unpublished, or credential-related information into external AI tools."
        ),
        "sns_guideline": (
            "For sensitive SNS content, pause publishing, classify the topic, collect source context, "
            "and avoid one-person judgment. Public replies should not confirm private facts or add unsupported details."
        ),
        "information_security": (
            "Do not place confidential information, credentials, private schedules, unreleased materials, "
            "or personal data into public tools or unmanaged storage. Suspected security events should be preserved and escalated."
        ),
        "copyright_material": (
            "Do not assume public material is reusable. Use only approved assets, original work, "
            "or material with a clear permission record that matches platform, format, and intended use."
        ),
        "talent_privacy": (
            "Do not confirm, deny, quote, or hint at private talent information. If rumors involve private details, "
            "avoid repeating them and escalate through the incident response workflow when the issue is spreading."
        ),
        "fan_content": (
            "Viewing fan content is not permission to reuse it. Campaign reuse requires a permission record "
            "covering the specific creator, use, platform, and attribution requirement."
        ),
        "expense_policy": (
            "A reimbursement request should include a receipt or equivalent record, date, category, "
            "business purpose, and requester note. Missing receipts should be flagged for review."
        ),
        "incident_response": (
            "During a public incident, pause non-essential posting, preserve context, avoid speculation, "
            "separate confirmed facts from assumptions, and decide whether a short neutral holding message is needed."
        ),
    },
    "zh": {
        "ai_tool_policy": "可以使用 AI 工具做草稿、改写、摘要和头脑风暴，但输出内容必须经过人工确认后才能用于对外沟通。不要把机密、隐私、未公开信息或凭证相关内容输入外部 AI 工具。",
        "sns_guideline": "涉及敏感 SNS 内容时，应先暂停发布、判断议题性质、收集来源上下文，并避免由单人直接决定。公开回复不应确认私人事实，也不应加入没有依据的新细节。",
        "information_security": "不要把机密信息、凭证、私人日程、未公开素材或个人数据放入公开工具或非受管存储。疑似安全事件应保留证据并升级处理。",
        "copyright_material": "不能因为素材公开可见就默认可以复用。应使用已批准素材、原创内容，或具备清晰许可记录且用途、平台、格式相匹配的材料。",
        "talent_privacy": "不要确认、否认、引用或暗示 talent 的私人信息。涉及私人细节的传闻不应被重复扩散，若传播加速，应进入事故应对流程。",
        "fan_content": "看到粉丝内容不等于获得复用许可。若用于活动，需要有覆盖创作者、用途、平台和署名要求的 permission record。",
        "expense_policy": "报销申请应包含收据或等效记录、日期、类别、业务目的和申请人备注。缺少收据的申请应标记为待审核。",
        "incident_response": "发生公开事故时，应暂停非必要发布、保留上下文、避免猜测，区分已确认事实和假设，并判断是否需要简短中性的 holding message。",
    },
    "ja": {
        "ai_tool_policy": "AI ツールは下書き、リライト、要約、ブレインストーミングに利用できます。ただし、外部向けに使う前に必ず人が確認する必要があります。機密情報、個人情報、未公開情報、認証情報に関わる内容を外部 AI ツールへ入力してはいけません。",
        "sns_guideline": "センシティブな SNS 投稿では、まず投稿を止め、トピックを分類し、根拠となる文脈を集め、単独判断を避けます。公開返信では非公開の事実を確認したり、根拠のない詳細を追加したりしないでください。",
        "information_security": "機密情報、認証情報、非公開スケジュール、未公開素材、個人データを公開ツールや管理外ストレージに置いてはいけません。セキュリティ事象が疑われる場合は、証跡を保全してエスカレーションします。",
        "copyright_material": "公開されている素材でも、そのまま再利用できるとは限りません。承認済み素材、オリジナル制作物、または用途・媒体・形式に合う明確な許諾記録がある素材を使います。",
        "talent_privacy": "タレントの非公開情報について、確認、否定、引用、示唆をしてはいけません。私的情報を含む噂は繰り返さず、拡散が速い場合は incident response workflow にエスカレーションします。",
        "fan_content": "ファンコンテンツを閲覧できることは再利用許可を意味しません。キャンペーンで使う場合は、制作者、用途、プラットフォーム、クレジット条件を含む permission record が必要です。",
        "expense_policy": "経費申請には、領収書または同等の記録、日付、カテゴリ、業務目的、申請者メモを含めます。領収書がない場合は自動承認せず、レビュー対象として扱います。",
        "incident_response": "公開上の incident が発生した場合は、不要不急の投稿を止め、文脈を保全し、推測を避け、確認済み事実と仮説を分けます。そのうえで短く中立的な holding message が必要か判断します。",
    },
}

SOURCE_LABELS = {
    "en": "Sources",
    "zh": "引用来源",
    "ja": "参照元",
}


def detect_topic(question: str) -> str | None:
    lowered = question.lower()
    scores = {}
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword.lower() in lowered)
        if score:
            scores[topic] = score

    if not scores:
        return None
    return max(scores, key=scores.get)


def select_citation_chunks(topic: str, chunks: Sequence[Dict[str, object]], limit: int = 3) -> List[Dict[str, object]]:
    selected: List[Dict[str, object]] = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("category") == topic:
            selected.append(chunk)
        if len(selected) >= limit:
            break
    return selected


def format_chunk_ids(chunks: Sequence[Dict[str, object]]) -> str:
    ids = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        chunk_id = metadata.get("chunk_id") if isinstance(metadata, dict) else None
        ids.append(str(chunk_id or chunk.get("id")))
    return ", ".join(f"[{chunk_id}]" for chunk_id in ids)


def generate_mock_answer(
    question: str,
    chunks: Sequence[Dict[str, object]],
    response_language: str | None = "auto",
) -> Dict[str, object]:
    language = normalize_response_language(response_language, question)
    refusal_text = get_refusal_text(language)
    topic = detect_topic(question)
    if topic is None:
        return {
            "answer": refusal_text,
            "provider": "mock",
            "language": language,
            "used_chunk_ids": [],
            "is_refusal": True,
        }

    citation_chunks = select_citation_chunks(topic, chunks)
    if not citation_chunks:
        return {
            "answer": refusal_text,
            "provider": "mock",
            "language": language,
            "used_chunk_ids": [],
            "is_refusal": True,
        }

    citation_ids = format_chunk_ids(citation_chunks)
    answer = f"{MOCK_ANSWERS[language][topic]}\n\n{SOURCE_LABELS[language]}: {citation_ids}"
    used_ids = [
        str(chunk.get("metadata", {}).get("chunk_id") or chunk.get("id"))
        for chunk in citation_chunks
        if isinstance(chunk.get("metadata", {}), dict)
    ]

    return {
        "answer": answer,
        "provider": "mock",
        "language": language,
        "used_chunk_ids": used_ids,
        "is_refusal": False,
    }

