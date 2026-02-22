"""应用启动事件

集中管理应用启动时需要执行的初始化逻辑，由 main.py 的 lifespan 调用。
"""

from yweb.log import get_logger

logger = get_logger()


def auto_sync_permissions(app):
    """启动时自动扫描路由并同步权限到数据库

    利用 PermissionService 扫描 FastAPI 已注册路由，
    将新增的模块级权限条目写入 permission 表。

    Args:
        app: FastAPI 应用实例（需已调用 register_all_routes 完成路由注册，
             且 app.state.perm_service 已设置）
    """
    perm_service = getattr(app.state, 'perm_service', None)
    if not perm_service:
        logger.warning("权限服务未初始化，跳过自动扫描")
        return

    result = perm_service.scan_and_sync()
    created = result.get("created", [])
    if created:
        logger.info(f"权限自动扫描：新增 {len(created)} 个权限条目")
    else:
        logger.info("权限自动扫描：无新增权限（已同步）")
