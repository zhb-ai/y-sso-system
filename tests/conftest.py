"""
Pytest 公共配置和 Fixtures
"""

import pytest
import os


def pytest_configure(config):
    """全局初始化钩子"""
    os.environ.setdefault("TESTING", "1")
