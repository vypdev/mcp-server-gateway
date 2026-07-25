from mcp_gateway.config import Settings
from mcp_gateway.server import create_server


def tool_names(server):
    return {tool.name for tool in server._tool_manager.list_tools()}


def test_observer_does_not_register_operator_command_tool():
    server = create_server(Settings(profile="observer"))
    assert "host_get_status" in tool_names(server)
    assert "docker_list_containers" in tool_names(server)
    assert "execute_command" not in tool_names(server)


def test_operator_registers_observer_and_command_tools():
    server = create_server(Settings(profile="operator"))
    names = tool_names(server)
    assert {"host_get_status", "docker_list_containers", "execute_command"} <= names
