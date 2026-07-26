from mcp_gateway.application.services import ExecuteCommand
from mcp_gateway.domain.profiles import Profile
from mcp_gateway.infrastructure.settings import Settings
from mcp_gateway.infrastructure.subprocess_runner import ProcessPolicy, SubprocessCommandRunner
from mcp_gateway.presentation.mcp_server import create_server


class FakeHostInfo:
    def identity(self):
        return {"host_id": "test-host", "uid": 1000}

    def status(self):
        return {"host_id": "test-host", "cpu_percent": 0}


def tool_names(server):
    return {tool.name for tool in server._tool_manager.list_tools()}


def create_test_server(profile: Profile):
    settings = Settings(profile=profile)
    runner = SubprocessCommandRunner(ProcessPolicy(allowed_cwds=settings.allowed_cwds))
    return create_server(settings, FakeHostInfo(), ExecuteCommand(profile, runner))


def test_observer_exposes_only_read_only_host_tools():
    names = tool_names(create_test_server(Profile.OBSERVER))
    assert names == {"host_get_identity", "host_get_status"}


def test_operator_exposes_command_tool_in_addition_to_host_tools():
    names = tool_names(create_test_server(Profile.OPERATOR))
    assert names == {"host_get_identity", "host_get_status", "execute_command"}
