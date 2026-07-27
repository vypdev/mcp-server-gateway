from gateway_node.application.services import ExecuteCommand
from gateway_node.application.authentication import AuthenticationService
from gateway_node.infrastructure.host_info import PsutilHostInfoProvider
from gateway_node.infrastructure.settings import Settings
from gateway_node.infrastructure.subprocess_runner import ProcessPolicy, SubprocessCommandRunner
from gateway_node.infrastructure.token_store import JsonTokenStore
from gateway_node.infrastructure.token_verifier import LocalTokenVerifier
from gateway_node.presentation.mcp_server import create_server


def build_server():
    settings = Settings.from_env()
    runner = SubprocessCommandRunner(
        ProcessPolicy(
            allowed_cwds=settings.allowed_cwds,
            max_timeout_seconds=settings.command_timeout_seconds,
            max_output_bytes=settings.max_output_bytes,
            max_arguments=settings.max_command_args,
        )
    )
    host_info = PsutilHostInfoProvider(settings.host_id, settings.profile.value)
    execute_command = ExecuteCommand(settings.profile, runner)
    authentication = AuthenticationService(JsonTokenStore(settings.auth_file, settings.auth_lock_file))
    return create_server(
        settings,
        host_info,
        execute_command,
        token_verifier=LocalTokenVerifier(authentication),
    )


def main() -> None:
    build_server().run(transport="streamable-http")
