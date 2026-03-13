"""企业微信组织架构同步服务

继承 YWeb 框架的 BaseSyncService，实现企业微信特有的数据获取和转换逻辑。

功能：
- 全量同步：从企微拉取完整组织架构（部门 + 成员 + 关系）
- 增量事件：处理通讯录变更回调的单条事件
- 同步锁：使用 threading.Lock 防止并发同步冲突

使用示例::

    from app.domain.wechat_work import WechatWorkClient, WechatWorkSyncService

    client = WechatWorkClient.from_organization(org)
    sync_service = WechatWorkSyncService(client)
    result = sync_service.sync_from_external(org.id)
"""

import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

from yweb.organization import BaseSyncService, ExternalSource, EmployeeStatus, SyncResult
from yweb.log import get_logger

from .client import WechatWorkClient

logger = get_logger()

# 企业微信根部门 ID（固定值，等价于 Organization 本身）
WECHAT_WORK_ROOT_DEPT_ID = "1"


class WechatWorkSyncService(BaseSyncService):
    """企业微信组织架构同步服务

    继承 BaseSyncService，实现三个抽象方法：
    - fetch_departments: 从企微获取部门列表
    - fetch_employees: 从企微获取员工列表
    - fetch_organization_info: 获取企业信息

    同步锁机制：
    - 使用 threading.Lock 按 org_id 隔离
    - 全量同步和增量回调不会并发冲突
    - 非阻塞：已有同步在进行时，新请求直接返回错误
    """

    external_source = ExternalSource.WECHAT_WORK

    # 模型类（在 __init__ 中从 OrgModels 获取）
    org_model = None
    dept_model = None
    employee_model = None
    emp_org_rel_model = None
    emp_dept_rel_model = None

    # ==================== 同步锁 ====================

    _sync_locks: Dict[int, threading.Lock] = {}
    _locks_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, org_id: int) -> threading.Lock:
        """获取指定组织的同步锁"""
        with cls._locks_lock:
            if org_id not in cls._sync_locks:
                cls._sync_locks[org_id] = threading.Lock()
            return cls._sync_locks[org_id]

    # ==================== 初始化 ====================

    def __init__(self, client: WechatWorkClient, org_models=None):
        """初始化同步服务

        Args:
            client: 企业微信 API 客户端
            org_models: OrgModels 实例（包含所有组织架构模型类）
        """
        # 设置模型类（从 OrgModels 获取）
        if org_models:
            self.org_model = org_models.Organization
            self.dept_model = org_models.Department
            self.employee_model = org_models.Employee
            self.emp_org_rel_model = org_models.EmployeeOrgRel
            self.emp_dept_rel_model = org_models.EmployeeDeptRel

        self.client = client
        super().__init__()

    # ==================== 全量同步（带锁） ====================

    def sync_from_external(self, org_id: int):
        """全量同步（带锁保护 + 缓存管理）

        Args:
            org_id: 组织 ID

        Returns:
            SyncResult 同步结果
        """
        lock = self._get_lock(org_id)
        if not lock.acquire(blocking=False):
            result = SyncResult()
            result.add_error("同步正在进行中，请稍后再试")
            return result

        try:
            # 清理缓存（确保每次全量同步使用新鲜数据）
            self._cached_departments = None
            self._cached_employees = None

            logger.info(f"开始全量同步: org_id={org_id}")
            result = super().sync_from_external(org_id)
            if result.success:
                logger.info(
                    f"全量同步完成: org_id={org_id}, "
                    f"新建={result.created_count}, "
                    f"更新={result.updated_count}, "
                    f"删除={result.deleted_count}, "
                    f"耗时={result.duration_seconds:.1f}s"
                )
            else:
                logger.warning(
                    f"全量同步完成（有错误）: org_id={org_id}, "
                    f"errors={result.errors}"
                )
            return result
        finally:
            # 确保缓存被清理
            self._cached_departments = None
            self._cached_employees = None
            lock.release()

    # ==================== 抽象方法实现 ====================

    def fetch_departments(self, org) -> List[Dict[str, Any]]:
        """从企微获取部门列表（支持缓存）

        过滤掉企微根部门（ID=1），它等价于 Organization 本身。
        企微 parentid=1 的部门映射为 YWeb 的根部门（parent_id=None）。

        缓存机制：全量同步时由 BaseSyncService 预拉取并缓存，
        避免 fetch_employees 内部重复调用。
        """
        # 如果已有缓存，直接返回（全量同步预拉取场景）
        if self._cached_departments is not None:
            return self._cached_departments

        raw_depts = self.client.get_departments()
        result = []

        for d in raw_depts:
            dept_id = str(d.get("id", ""))
            parent_id = str(d.get("parentid", ""))

            # 跳过根部门（等价于 Organization）
            if dept_id == WECHAT_WORK_ROOT_DEPT_ID:
                continue

            result.append({
                "external_dept_id": dept_id,
                "external_parent_id": (
                    None if parent_id == WECHAT_WORK_ROOT_DEPT_ID
                    else parent_id
                ),
                "name": d.get("name", ""),
                "sort_order": d.get("order", 0),
            })

        logger.debug(f"获取企微部门: 共 {len(result)} 个（已过滤根部门）")
        return result

    def fetch_employees(self, org) -> List[Dict[str, Any]]:
        """从企微获取所有员工（支持缓存）

        遍历所有部门获取成员详情，去重合并多部门归属信息。

        缓存机制：全量同步时由 BaseSyncService 预拉取并缓存，
        sync_employee_dept_relations 直接复用缓存数据，避免重复 API 调用。
        """
        # 如果已有缓存，直接返回
        if self._cached_employees is not None:
            return self._cached_employees

        all_users: Dict[str, Dict[str, Any]] = {}

        # 收集所有需要遍历的部门 ID（包含根部门下的直属成员）
        # 使用缓存的部门数据避免重复调用 fetch_departments
        dept_ids = [WECHAT_WORK_ROOT_DEPT_ID]
        external_depts = self._cached_departments or self.fetch_departments(org)
        dept_ids.extend(d["external_dept_id"] for d in external_depts)

        for dept_id in dept_ids:
            try:
                users = self.client.get_department_users(int(dept_id))
            except ValueError:
                logger.warning(f"获取部门成员失败，跳过: dept_id={dept_id}")
                continue

            for u in users:
                uid = str(u.get("userid", ""))
                if not uid:
                    continue

                # 过滤该成员所属部门中的根部门
                user_dept_ids = [
                    str(d) for d in u.get("department", [])
                    if str(d) != WECHAT_WORK_ROOT_DEPT_ID
                ]

                if uid not in all_users:
                    all_users[uid] = {
                        "external_user_id": uid,
                        "name": u.get("name", ""),
                        "mobile": u.get("mobile"),
                        "email": u.get("email"),
                        "avatar": u.get("avatar"),
                        "gender": u.get("gender", 0),
                        "emp_no": u.get("alias"),
                        "position": u.get("position"),
                        "status": self._map_status(u.get("status", 1)),
                        "department_ids": user_dept_ids,
                        "main_department": u.get("main_department"),
                        "enterprise_wechat_user_id": u.get("userid"),
                    }
                else:
                    # 合并多部门归属
                    existing = set(all_users[uid]["department_ids"])
                    existing.update(user_dept_ids)
                    all_users[uid]["department_ids"] = list(existing)

        logger.debug(f"获取企微员工: 共 {len(all_users)} 人（已去重）")
        return list(all_users.values())

    def fetch_organization_info(self, org) -> Optional[Dict[str, Any]]:
        """获取企业信息

        企微没有直接的企业信息查询接口，返回 None 跳过此步骤。
        """
        return None

    # ==================== 增量事件处理 ====================

    def handle_create_department(self, org, event_data: Dict[str, Any]):
        """处理部门创建事件

        Args:
            org: Organization 实例
            event_data: 事件数据（已解析的 XML 字典）
        """
        dept_id = str(event_data.get("Id", ""))
        parent_id = str(event_data.get("ParentId", ""))
        name = event_data.get("Name", "")
        order = int(event_data.get("Order", 0))

        logger.info(f"回调事件: 创建部门 [{name}] id={dept_id}")

        data = {
            "external_dept_id": dept_id,
            "external_parent_id": (
                None if parent_id == WECHAT_WORK_ROOT_DEPT_ID
                else parent_id
            ),
            "name": name,
            "sort_order": order,
        }
        self._create_dept_from_external(org, data)

        # 建立父子关系
        self._update_single_dept_parent(org, data)

    def handle_update_department(self, org, event_data: Dict[str, Any]):
        """处理部门更新事件"""
        dept_id = str(event_data.get("Id", ""))
        logger.info(f"回调事件: 更新部门 id={dept_id}")

        dept = self.dept_model.query.filter(
            self.dept_model.org_id == org.id,
            self.dept_model.external_dept_id == dept_id,
        ).first()

        if not dept:
            logger.warning(f"部门不存在，忽略更新事件: external_dept_id={dept_id}")
            return

        # 更新字段（只更新事件中存在的字段）
        if "Name" in event_data:
            dept.name = event_data["Name"]
        if "Order" in event_data:
            dept.sort_order = int(event_data["Order"])

        # 处理父部门变更
        if "ParentId" in event_data:
            new_parent_id = str(event_data["ParentId"])
            if new_parent_id == WECHAT_WORK_ROOT_DEPT_ID:
                if dept.parent_id is not None:
                    dept.parent_id = None
                    dept.update_path_and_level()
            else:
                parent = self.dept_model.query.filter(
                    self.dept_model.org_id == org.id,
                    self.dept_model.external_dept_id == new_parent_id,
                ).first()
                if parent and dept.parent_id != parent.id:
                    dept.parent_id = parent.id
                    dept.update_path_and_level()

        dept.save(commit=True)

    def handle_delete_department(self, org, event_data: Dict[str, Any]):
        """处理部门删除事件

        安全删除策略：
        1. 子部门上移到父部门（避免孤儿部门）
        2. 清理员工-部门关联（避免指向不存在的部门）
        3. 软删除部门（设置 deleted_at，不物理删除）
        """
        dept_id = str(event_data.get("Id", ""))
        logger.info(f"回调事件: 删除部门 id={dept_id}")

        dept = self.dept_model.query.filter(
            self.dept_model.org_id == org.id,
            self.dept_model.external_dept_id == dept_id,
        ).first()

        if not dept:
            logger.warning(f"部门不存在，忽略删除事件: external_dept_id={dept_id}")
            return

        # 1. 子部门上移到父部门（而非变成孤儿）
        children = self.dept_model.query.filter(
            self.dept_model.parent_id == dept.id,
        ).all()
        for child in children:
            child.parent_id = dept.parent_id
            child.update_path_and_level()
            child.save(commit=True)

        # 2. 清理员工-部门关联
        self.emp_dept_rel_model.query.filter(
            self.emp_dept_rel_model.dept_id == dept.id,
        ).delete()

        # 3. 软删除部门
        dept.deleted_at = datetime.now()
        dept.save(commit=True)
        logger.info(f"部门已软删除: external_dept_id={dept_id}, id={dept.id}")

    def handle_create_user(self, org, event_data: Dict[str, Any]):
        """处理成员创建事件"""
        user_id = str(event_data.get("UserID", ""))
        name = event_data.get("Name", "")
        logger.info(f"回调事件: 创建成员 [{name}] userid={user_id}")

        # 从企微 API 获取完整成员信息（事件只包含部分字段）
        try:
            user_detail = self.client.get_user(user_id)
        except ValueError:
            logger.error(f"获取新成员详情失败: userid={user_id}")
            return

        dept_ids = [
            str(d) for d in user_detail.get("department", [])
            if str(d) != WECHAT_WORK_ROOT_DEPT_ID
        ]

        data = {
            "external_user_id": user_id,
            "name": user_detail.get("name", name),
            "mobile": user_detail.get("mobile"),
            "email": user_detail.get("email"),
            "avatar": user_detail.get("avatar"),
            "gender": user_detail.get("gender", 0),
            "emp_no": user_detail.get("alias"),
            "position": user_detail.get("position"),
            "status": self._map_status(user_detail.get("status", 1)),
            "department_ids": dept_ids,
            "main_department": user_detail.get("main_department"),
            "enterprise_wechat_user_id": user_detail.get("userid", None),
        }

        # 创建员工 + 组织关联
        employee = self._create_employee_from_external(org, data)

        # 创建部门关联
        self._sync_single_employee_dept_rels(org, employee, data)

    def handle_update_user(self, org, event_data: Dict[str, Any]):
        """处理成员更新事件"""
        user_id = str(event_data.get("UserID", ""))
        logger.info(f"回调事件: 更新成员 userid={user_id}")

        # 查找已有员工
        rel = self.emp_org_rel_model.query.filter(
            self.emp_org_rel_model.org_id == org.id,
            self.emp_org_rel_model.external_user_id == user_id,
        ).first()

        if not rel:
            logger.warning(f"成员不存在，尝试作为新成员创建: userid={user_id}")
            self.handle_create_user(org, event_data)
            return

        employee = self.employee_model.get(rel.employee_id)
        if not employee:
            logger.error(f"员工记录丢失: employee_id={rel.employee_id}")
            return

        # 从企微 API 获取完整信息
        try:
            user_detail = self.client.get_user(user_id)
        except ValueError:
            logger.error(f"获取成员详情失败: userid={user_id}")
            return

        dept_ids = [
            str(d) for d in user_detail.get("department", [])
            if str(d) != WECHAT_WORK_ROOT_DEPT_ID
        ]

        data = {
            "external_user_id": user_id,
            "name": user_detail.get("name", ""),
            "mobile": user_detail.get("mobile"),
            "email": user_detail.get("email"),
            "avatar": user_detail.get("avatar"),
            "gender": user_detail.get("gender", 0),
            "emp_no": user_detail.get("alias"),
            "position": user_detail.get("position"),
            "status": self._map_status(user_detail.get("status", 1)),
            "department_ids": dept_ids,
            "main_department": user_detail.get("main_department"),
            "enterprise_wechat_user_id": user_detail.get("userid", None),
        }

        # 更新员工 + 组织关联
        self._update_employee_from_external(employee, rel, data)

        # 更新部门关联
        self._sync_single_employee_dept_rels(org, employee, data)

    def handle_delete_user(self, org, event_data: Dict[str, Any]):
        """处理成员删除事件

        标记为离职（RESIGNED）、清理部门关联、禁用关联的 User 账号。
        """
        user_id = str(event_data.get("UserID", ""))
        logger.info(f"回调事件: 删除成员 userid={user_id}")

        rel = self.emp_org_rel_model.query.filter(
            self.emp_org_rel_model.org_id == org.id,
            self.emp_org_rel_model.external_user_id == user_id,
        ).first()

        if not rel:
            logger.warning(f"成员不存在，忽略删除事件: userid={user_id}")
            return

        # 标记离职
        rel.status = EmployeeStatus.RESIGNED.value
        rel.save(commit=True)

        # 清理部门关联
        self.emp_dept_rel_model.query.filter(
            self.emp_dept_rel_model.employee_id == rel.employee_id,
        ).delete()

        # 禁用关联的 User 账号
        employee = self.employee_model.get(rel.employee_id)
        if employee:
            self._on_employee_mark_resigned(employee, rel)

        logger.info(f"成员已标记离职: userid={user_id}, employee_id={rel.employee_id}")

    # ==================== 辅助方法 ====================

    @staticmethod
    def _map_status(wechat_status: int) -> int:
        """企微状态码 → YWeb EmployeeStatus

        企微状态: 1=已激活, 2=已禁用, 4=未激活, 5=已离职
        """
        mapping = {
            1: EmployeeStatus.ACTIVE.value,       # 已激活 → 在职
            2: EmployeeStatus.SUSPENDED.value,     # 已禁用 → 停职
            4: EmployeeStatus.PENDING.value,       # 未激活 → 待入职
            5: EmployeeStatus.RESIGNED.value,      # 已离职 → 离职
        }
        return mapping.get(wechat_status, EmployeeStatus.ACTIVE.value)

    def _update_single_dept_parent(self, org, data: Dict[str, Any]):
        """建立单个部门的父子关系"""
        ext_id = data.get("external_dept_id")
        ext_parent_id = data.get("external_parent_id")

        dept = self.dept_model.query.filter(
            self.dept_model.org_id == org.id,
            self.dept_model.external_dept_id == ext_id,
        ).first()

        if not dept:
            return

        if ext_parent_id:
            parent = self.dept_model.query.filter(
                self.dept_model.org_id == org.id,
                self.dept_model.external_dept_id == ext_parent_id,
            ).first()
            if parent and dept.parent_id != parent.id:
                dept.parent_id = parent.id
                dept.update_path_and_level()
                dept.save(commit=True)
        elif dept.parent_id is not None:
            dept.parent_id = None
            dept.update_path_and_level()
            dept.save(commit=True)

    def _create_employee_from_external(self, org, data: Dict[str, Any]) -> Any:
        # 创建员工
        employee = self.employee_model(
            name=data.get('name', ''),
            mobile=data.get('mobile'),
            email=data.get('email'),
            avatar=data.get('avatar'),
            gender=data.get('gender', 0),
            enterprise_wechat_user_id=data.get('enterprise_wechat_user_id'),
        )
        employee.save(commit=True)
        
        # 尝试转换 userid 为 openid
        enterprise_wechat_user_id = data.get('enterprise_wechat_user_id')
        if enterprise_wechat_user_id:
            try:
                openid = self.client.convert_userid_to_openid(enterprise_wechat_user_id)
                employee.enterprise_wechat_openid = openid
                employee.save(commit=True)
            except Exception as e:
                logger.warning(f"转换 userid 为 openid 失败，将在后续同步时重试: userid={enterprise_wechat_user_id}, {e}")
        
        # 创建员工-组织关联
        rel = self.emp_org_rel_model(
            employee_id=employee.id,
            org_id=org.id,
            emp_no=data.get('emp_no'),
            position=data.get('position'),
            external_user_id=str(data.get('enterprise_wechat_user_id', '')),
            enterprise_wechat_openid=employee.enterprise_wechat_openid,
        )
        rel.save(commit=True)
        
        return employee
    
    def _update_employee_from_external(self, employee, rel, data: Dict[str, Any]):
        """根据外部数据更新员工，添加 wechat_user_id 和 wechat_openid 字段处理"""
        employee.name = data.get('name', employee.name)
        employee.mobile = data.get('mobile', employee.mobile)
        employee.email = data.get('email', employee.email)
        employee.avatar = data.get('avatar', employee.avatar)
        employee.gender = data.get('gender', employee.gender)
        
        # 更新 enterprise_wechat_user_id
        new_wechat_user_id = data.get('enterprise_wechat_user_id')
        if new_wechat_user_id != employee.enterprise_wechat_user_id:
            employee.enterprise_wechat_user_id = new_wechat_user_id
            # 如果 userid 变化，重新转换 openid
            if new_wechat_user_id:
                try:
                    openid = self.client.convert_userid_to_openid(new_wechat_user_id)
                    employee.enterprise_wechat_openid = openid
                except Exception as e:
                    logger.warning(f"转换 userid 为 openid 失败，将在后续同步时重试: userid={new_wechat_user_id}, {e}")
        
        employee.save(commit=True)
        
        rel.emp_no = data.get('emp_no', rel.emp_no)
        rel.position = data.get('position', rel.position)
        rel.enterprise_wechat_openid = employee.enterprise_wechat_openid
        rel.save(commit=True)
    
    def _sync_single_employee_dept_rels(
        self, org, employee, data: Dict[str, Any]
    ):
        """同步单个员工的部门关联关系"""
        ext_dept_ids = data.get("department_ids", [])
        main_dept_id = data.get("main_department")

        # 建立外部部门ID → 内部部门ID 的映射
        depts = self.dept_model.query.filter(
            self.dept_model.org_id == org.id,
        ).all()
        ext_to_dept_id = {
            d.external_dept_id: d.id for d in depts if d.external_dept_id
        }

        target_dept_ids = {
            ext_to_dept_id[eid] for eid in ext_dept_ids
            if eid in ext_to_dept_id
        }

        # 获取现有关联
        existing_rels = self.emp_dept_rel_model.query.filter(
            self.emp_dept_rel_model.employee_id == employee.id,
        ).all()
        current_dept_ids = {r.dept_id for r in existing_rels}

        # 添加新关联
        for dept_id in target_dept_ids - current_dept_ids:
            ext_dept_id = next(
                (k for k, v in ext_to_dept_id.items() if v == dept_id), None
            )
            rel = self.emp_dept_rel_model(
                employee_id=employee.id,
                dept_id=dept_id,
                external_dept_id=ext_dept_id,
            )
            rel.save(commit=True)

        # 删除多余关联
        for dept_id in current_dept_ids - target_dept_ids:
            self.emp_dept_rel_model.query.filter(
                self.emp_dept_rel_model.employee_id == employee.id,
                self.emp_dept_rel_model.dept_id == dept_id,
            ).delete()

        # 设置主部门（优先使用企业微信返回的 main_department）
        if target_dept_ids:
            # 尝试使用企业微信返回的主部门
            primary_dept_id = None
            if main_dept_id:
                main_dept_id_str = str(main_dept_id)
                if main_dept_id_str in ext_to_dept_id:
                    primary_dept_id = ext_to_dept_id[main_dept_id_str]
            
            # 如果没有主部门或主部门不存在，使用第一个部门
            if primary_dept_id is None and target_dept_ids:
                primary_dept_id = min(target_dept_ids)
            
            if primary_dept_id and employee.primary_dept_id != primary_dept_id:
                employee.primary_dept_id = primary_dept_id
                employee.save(commit=True)

    # ==================== 生命周期钩子 ====================

    def _on_employee_mark_resigned(self, employee, rel):
        """员工标记离职时：同时禁用关联的 User 账号

        恢复（员工重新出现在企微通讯录）时，仅恢复员工状态，
        User 账号需要管理员手工启用。
        """
        user_id = getattr(employee, 'user_id', None)
        if not user_id:
            return

        from app.models_registry import User
        user = User.get(user_id)
        if user and user.is_active:
            user.is_active = False
            user.save(commit=True)
            logger.info(
                f"员工离职，已禁用关联用户账号: "
                f"employee_id={employee.id}, user_id={user_id}, "
                f"username={user.username}"
            )
