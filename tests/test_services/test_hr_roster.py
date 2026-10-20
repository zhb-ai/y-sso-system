"""花名册快照的合成与失败隔离。通讯录同步不拉花名册。"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from yweb.organization import SyncResult
from yweb.organization.services.sync_service import BaseSyncService

from app.domain.wechat_work.hr_roster import apply_staff_rosters, build_hr_roster
from app.domain.wechat_work.sync_service import WechatWorkSyncService


def _catalog():
    return [
        {
            "group_id": 1001,
            "group_name": "个人信息",
            "field_list": [
                {
                    "fieldid": 11007,
                    "field_name": "籍贯",
                    "field_type": 2,
                    "option_list": [{"id": 11, "value": "河北省"}],
                },
                {
                    "fieldid": 11015,
                    "field_name": "身份证号码",
                    "field_type": 1,
                    "option_list": [],
                },
                {
                    "fieldid": 11005,
                    "field_name": "出生日期",
                    "field_type": 3,
                    "option_list": [],
                },
            ],
        },
        {
            "group_id": 1004,
            "group_name": "教育经历",
            "field_list": [
                {"fieldid": 14001, "field_name": "学历", "field_type": 1, "option_list": []},
                {"fieldid": 14002, "field_name": "毕业院校", "field_type": 1, "option_list": []},
            ],
        },
        {
            "group_id": 1009,
            "group_name": "材料附件",
            "field_list": [
                {"fieldid": 19001, "field_name": "员工照片", "field_type": 4, "option_list": []},
            ],
        },
    ]


class _RosterEmployee:
    """测试用员工，记录是否保存。"""

    def __init__(self, userid, roster=None):
        self.enterprise_wechat_user_id = userid
        self.hr_roster = roster
        self.saved = False

    def save(self, commit=True):
        self.saved = True


class TestBuildHrRoster:
    """花名册 JSON 要覆盖已配置字段，并保留可重复组的已有记录。"""

    def test_includes_empty_fields_and_formats_option_date_and_file(self):
        """未返回的字段为 null；选项、日期、附件按可直接使用的值保存。"""
        document = build_hr_roster(
            _catalog(),
            [
                {"fieldid": 11007, "sub_idx": 0, "result": 1, "value_type": 3, "value_uint32": 11},
                {"fieldid": 11005, "sub_idx": 0, "result": 1, "value_type": 4, "value_int64": 723744000},
                {
                    "fieldid": 19001,
                    "sub_idx": 0,
                    "result": 1,
                    "value_type": 6,
                    "value_file": {"media_id": ["photo-1"]},
                },
                {"fieldid": 14002, "sub_idx": 1, "result": 1, "value_type": 1, "value_string": "郑州大学"},
            ],
            userid="luxiaopeng",
            synced_at="2026-10-20T11:00:00+08:00",
        )

        personal = document["groups"][0]["records"][0]["fields"]
        by_name = {field["name"]: field for field in personal}
        assert by_name["籍贯"]["value"] == "河北省"
        assert by_name["籍贯"]["option_id"] == 11
        assert by_name["身份证号码"]["value"] is None
        assert by_name["出生日期"]["value"] == "1992-12-08"
        assert document["groups"][2]["records"][0]["fields"][0]["value"] == ["photo-1"]

        education = document["groups"][1]
        assert education["repeatable"] is True
        assert [record["sub_idx"] for record in education["records"]] == [1]
        education_fields = {field["name"]: field["value"] for field in education["records"][0]["fields"]}
        assert education_fields["毕业院校"] == "郑州大学"
        assert education_fields["学历"] is None

    def test_read_failure_is_marked_and_does_not_look_like_an_empty_value(self):
        """接口明确读取失败时，字段标为不可用，而不是当成未填写。"""
        document = build_hr_roster(
            _catalog(),
            [{"fieldid": 19001, "sub_idx": 0, "result": 2, "value_type": 6, "value_file": {}}],
            userid="luxiaopeng",
            synced_at="2026-10-20T11:00:00+08:00",
        )
        photo = document["groups"][2]["records"][0]["fields"][0]
        assert photo["value"] is None
        assert photo["unavailable"] is True


class TestApplyStaffRosters:
    """单人拉取失败时保留原快照，成功的人仍然写入。"""

    def test_failure_does_not_overwrite_existing_roster(self):
        ok_employee = _RosterEmployee("ok")
        failed_employee = _RosterEmployee("bad", roster={"userid": "bad", "groups": []})

        errors = apply_staff_rosters(
            [(ok_employee, "ok"), (failed_employee, "bad")],
            _catalog(),
            {
                "ok": [{"fieldid": 11015, "sub_idx": 0, "result": 1, "value_type": 1, "value_string": "110"}],
                "bad": ValueError("userid not found"),
            },
            synced_at="2026-10-20T11:00:00+08:00",
        )

        assert ok_employee.saved is True
        assert ok_employee.hr_roster["userid"] == "ok"
        assert failed_employee.saved is False
        assert failed_employee.hr_roster == {"userid": "bad", "groups": []}
        assert errors == ["花名册同步失败: userid=bad: userid not found"]


def _sync_service():
    models = SimpleNamespace(
        Organization=object,
        Department=object,
        Employee=object,
        EmployeeOrgRel=object,
        EmployeeDeptRel=object,
    )
    return WechatWorkSyncService(client=MagicMock(), org_models=models)


class TestSyncFromExternalDoesNotFetchRoster:
    """通讯录同步不拉花名册。"""

    def test_contact_sync_does_not_call_hr_roster(self, monkeypatch):
        service = _sync_service()
        contact = SyncResult()
        contact.created_count = 3
        contact.finish("通讯录完成")
        monkeypatch.setattr(
            BaseSyncService,
            "sync_from_external",
            lambda self, org_id: contact,
        )
        called = []
        monkeypatch.setattr(
            service,
            "sync_hr_roster",
            lambda org_id: called.append(org_id) or [],
        )

        result = service.sync_from_external(1)

        assert called == []
        assert result.created_count == 3
        assert result.success is True
        assert result.errors == []
