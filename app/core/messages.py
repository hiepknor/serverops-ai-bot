from __future__ import annotations

from app.config import Settings

MessageKey = str

MESSAGES: dict[str, dict[MessageKey, str]] = {
    "en": {
        "access_denied": "Access denied.",
        "action_failed": "Action failed: {error}",
        "action_container_restarted": "Container restarted: {target}",
        "action_service_restarted": "Service restarted: {target}",
        "action_unsupported": "Unsupported action: {action}",
        "audit_empty": "Recent audit: none",
        "audit_header": "Recent audit",
        "confirmation_no_match": "No pending confirmation matched.",
        "confirmation_required": (
            "Confirmation required.\n"
            "Action: {action}\n"
            "Target: {target}\n"
            "Reply exactly:\n"
            "{confirmation_text}"
        ),
        "docker_access_denied": "Docker access denied: {error}",
        "docker_containers_empty": "Docker containers: none",
        "docker_containers_header": "Docker containers",
        "docker_disabled": "Docker tools are disabled. Set ENABLE_DOCKER_TOOLS=true to enable.",
        "docker_logs_header": "Docker logs: {name}",
        "docker_unavailable": "Docker unavailable: {error}",
        "health_ok": "Health: OK",
        "health_warning_cpu": "high CPU",
        "health_warning_disk": "high disk",
        "health_warning_memory": "high RAM",
        "health_warn": "Health: WARN: {warnings}",
        "log_access_denied": "Log access denied: {error}",
        "log_empty": "(empty)",
        "log_header": "Log: {name}",
        "restart_usage": "Usage: /restart <allowed-service> or /docker_restart <allowed-container>",
        "server_status_header": "Server status",
        "usage_audit": "Usage: /audit [1-{max_limit}]",
        "usage_docker_logs": "Usage: /docker_logs <allowed-container>",
        "usage_ask": "Usage: /ask <question>",
        "usage_incident": "Usage: /incident <allowed-log-name>",
        "usage_log": "Usage: /log <allowed-log-name>",
        "usage_summarize_log": "Usage: /summarize_log <allowed-log-name>",
    },
    "vi": {
        "access_denied": "Từ chối truy cập.",
        "action_failed": "Thao tác thất bại: {error}",
        "action_container_restarted": "Đã khởi động lại container: {target}",
        "action_service_restarted": "Đã khởi động lại service: {target}",
        "action_unsupported": "Hành động chưa được hỗ trợ: {action}",
        "audit_empty": "Audit gần đây: không có",
        "audit_header": "Audit gần đây",
        "confirmation_no_match": "Không tìm thấy xác nhận đang chờ phù hợp.",
        "confirmation_required": (
            "Cần xác nhận trước khi thực thi.\n"
            "Hành động: {action}\n"
            "Mục tiêu: {target}\n"
            "Vui lòng trả lời chính xác:\n"
            "{confirmation_text}"
        ),
        "docker_access_denied": "Từ chối truy cập Docker: {error}",
        "docker_containers_empty": "Container Docker: không có",
        "docker_containers_header": "Container Docker",
        "docker_disabled": "Docker tools đang tắt. Đặt ENABLE_DOCKER_TOOLS=true để bật.",
        "docker_logs_header": "Log Docker: {name}",
        "docker_unavailable": "Docker không khả dụng: {error}",
        "health_ok": "Sức khỏe hệ thống: OK",
        "health_warning_cpu": "CPU cao",
        "health_warning_disk": "Disk cao",
        "health_warning_memory": "RAM cao",
        "health_warn": "Sức khỏe hệ thống: CẢNH BÁO: {warnings}",
        "log_access_denied": "Từ chối truy cập log: {error}",
        "log_empty": "(trống)",
        "log_header": "Log: {name}",
        "restart_usage": (
            "Cách dùng: /restart <service-được-phép> hoặc "
            "/docker_restart <container-được-phép>"
        ),
        "server_status_header": "Trạng thái server",
        "usage_audit": "Cách dùng: /audit [1-{max_limit}]",
        "usage_docker_logs": "Cách dùng: /docker_logs <container-được-phép>",
        "usage_ask": "Cách dùng: /ask <câu-hỏi>",
        "usage_incident": "Cách dùng: /incident <tên-log-được-phép>",
        "usage_log": "Cách dùng: /log <tên-log-được-phép>",
        "usage_summarize_log": "Cách dùng: /summarize_log <tên-log-được-phép>",
    },
}


def message(settings: Settings, key: MessageKey, **values: object) -> str:
    language = settings.bot_language if settings.bot_language in MESSAGES else "vi"
    template = MESSAGES[language][key]
    return template.format(**values)
