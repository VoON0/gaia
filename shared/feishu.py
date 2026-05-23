"""飞书 API 工具模块。

用法：
    from shared.feishu import push_feishu, get_feishu_token
    
必须设置环境变量（或用 .env 文件）：
    FEISHU_APP_ID
    FEISHU_APP_SECRET
    FEISHU_CHAT_ID
"""

import os, json, urllib.request, urllib.parse, logging

logger = logging.getLogger(__name__)

FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")


def get_feishu_token() -> str | None:
    """获取飞书 tenant_access_token"""
    if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
        logger.error("FEISHU_APP_ID 或 FEISHU_APP_SECRET 未设置")
        return None
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        return result.get("tenant_access_token")
    except Exception as e:
        logger.error(f"获取飞书 token 失败: {e}")
        return None


def push_feishu(content: str, title: str = "GAIA 报告", msg_type: str = "interactive") -> bool:
    """推送消息到飞书群聊"""
    token = get_feishu_token()
    if not token:
        return False
    if not FEISHU_CHAT_ID:
        logger.error("FEISHU_CHAT_ID 未设置")
        return False

    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    body = {
        "receive_id": FEISHU_CHAT_ID,
        "msg_type": msg_type,
        "content": json.dumps({
            "config": {"wide_screen_mode": True},
            "header": {"title": {"tag": "plain_text", "content": title}, "template": "blue"},
            "elements": [{"tag": "markdown", "content": content}]
        }) if msg_type == "interactive" else content
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read().decode())
        if result.get("code") != 0:
            logger.error(f"飞书推送失败: {result.get('msg')}")
            return False
        return True
    except Exception as e:
        logger.error(f"飞书推送异常: {e}")
        return False
