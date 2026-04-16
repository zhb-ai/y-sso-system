"""开发服务器启动脚本测试"""

import dev_server


class TestDevServer:
    """开发服务器默认参数测试"""

    def test_build_parser_uses_port_8000_by_default(self):
        """默认端口应统一为 8000"""
        parser = dev_server.build_parser()

        args = parser.parse_args([])

        assert args.port == 8000
