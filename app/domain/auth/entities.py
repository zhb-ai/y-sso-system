"""Auth 域 - 实体模型重导出

User 和 LoginRecord 的实际定义在 model/ 子目录下，
此处统一重导出，使得按 entities.py 约定扫描时也能发现它们。
"""

from app.domain.auth.model.user import User                    # noqa: F401
from app.domain.auth.model.login_record import LoginRecord      # noqa: F401
