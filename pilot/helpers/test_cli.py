from unittest.mock import patch, MagicMock
from helpers.cli import execute_command, terminate_process, run_command_until_success
from helpers.test_Project import create_project


def test_terminate_process_not_running():
    terminate_process(999999999, 'not running')
    assert True


@patch('helpers.cli.get_saved_command_run')
@patch('helpers.cli.run_command')
def test_execute_command_timeout_exit_code(mock_run, mock_get_saved_command):
    # Given
    project = create_project()
    command = 'ping www.google.com'
    timeout = 1
    mock_process = MagicMock()
    mock_run.return_value = mock_process
    mock_process.poll.return_value = None
    mock_process.pid = 1234

    # When
    cli_response, llm_response, exit_code = execute_command(project, command, timeout, force=True)

    # Then
    assert cli_response is not None
    assert llm_response == 'timed out'
    assert exit_code is not None


@patch('helpers.cli.get_saved_command_run')
@patch('helpers.cli.ask_user', return_value='')
def test_execute_command_enter(mock_ask, mock_get_saved_command):
    # Given
    project = create_project()
    command = 'echo hello'
    timeout = 1000

    # When
    cli_response, llm_response, exit_code = execute_command(project, command, timeout)

    # Then
    assert 'hello' in cli_response
    assert llm_response is None
    assert exit_code == 0


@patch('helpers.cli.get_saved_command_run')
@patch('helpers.cli.ask_user', return_value='yes')
def test_execute_command_yes(mock_ask, mock_get_saved_command):
    # Given
    project = create_project()
    command = 'echo hello'
    timeout = 1000

    # When
    cli_response, llm_response, exit_code = execute_command(project, command, timeout)

    # Then
    assert 'hello' in cli_response
    assert llm_response is None
    assert exit_code == 0


@patch('helpers.cli.get_saved_command_run')
@patch('helpers.cli.ask_user', return_value='no')
def test_execute_command_rejected_with_no(mock_ask, mock_get_saved_command):
    # Given
    project = create_project()
    command = 'ping www.google.com'
    timeout = 1

    # When
    cli_response, llm_response, exit_code = execute_command(project, command, timeout)

    # Then
    assert cli_response is None
    assert llm_response == 'DONE'
    assert exit_code is None


@patch('helpers.cli.get_saved_command_run')
@patch('helpers.cli.ask_user', return_value='no, my DNS is not working, ping 8.8.8.8 instead')
def test_execute_command_rejected_with_message(mock_ask, mock_get_saved_command):
    # Given
    project = create_project()
    command = 'ping www.google.com'
    timeout = 1

    # When
    cli_response, llm_response, exit_code = execute_command(project, command, timeout)

    # Then
    assert cli_response is None
    assert llm_response == 'no, my DNS is not working, ping 8.8.8.8 instead'
    assert exit_code is None


@patch('helpers.cli.execute_command', return_value=('hello', None, 0))
def test_run_command_until_success(mock_execute):
    # Given
    convo = MagicMock()
    command = 'ping www.google.com'
    timeout = 1

    # When
    result = run_command_until_success(convo, command, timeout)

    # Then
    assert result['success']
    assert result['cli_response'] == 'hello'
    assert convo.send_message.call_count == 1


@patch('helpers.cli.execute_command', return_value=('running...', 'DONE', None))
def test_run_command_until_success_app(mock_execute):
    # Given
    convo = MagicMock()
    command = 'npm run start'
    command_id = 'app'
    timeout = 1000

    # When
    result = run_command_until_success(convo, command, timeout, command_id=command_id)

    # Then
    assert result['success']
    assert result['cli_response'] == 'running...'
    assert convo.send_message.call_count == 0


@patch('helpers.cli.execute_command', return_value=('error', None, 2))
def test_run_command_until_success_error(mock_execute):
    # Given
    convo = MagicMock()
    convo.send_message.return_value = 'NEEDS DEBUGGING'
    convo.agent.debugger.debug.return_value = False
    command = 'ping www.google.com'
    timeout = 1

    # When
    result = run_command_until_success(convo, command, timeout)

    # Then
    assert convo.send_message.call_count == 1
    assert not result['success']
    assert result['cli_response'] == 'error'


@patch('helpers.cli.execute_command', return_value=('hell', 'timed out', 0))
def test_run_command_until_success_timed_out(mock_execute):
    # Given
    convo = MagicMock()
    convo.send_message.return_value = 'NEEDS DEBUGGING'
    convo.agent.debugger.debug.return_value = False
    command = 'ping www.google.com'
    timeout = 1

    # When
    result = run_command_until_success(convo, command, timeout)

    # Then
    assert convo.send_message.call_count == 1
    assert not result['success']
    assert result['cli_response'] == 'hell'


@patch('helpers.cli.execute_command', return_value=(None, 'DONE', None))
def test_run_command_until_success_no(mock_execute):
    # Given
    convo = MagicMock()
    command = 'ping www.google.com'
    timeout = 1

    # When
    result = run_command_until_success(convo, command, timeout)

    # Then
    assert result['success']
    assert result['cli_response'] is None
    assert 'user_input' not in result or result['user_input'] is None
    assert convo.send_message.call_count == 0


@patch('helpers.cli.execute_command', return_value=(None, 'no, my DNS is not working, ping 8.8.8.8 instead', None))
def test_run_command_until_success_rejected(mock_execute):
    # Given
    convo = MagicMock()
    command = 'ping www.google.com'
    timeout = 1

    # When
    result = run_command_until_success(convo, command, timeout)

    # Then
    assert not result['success']
    assert 'cli_response' not in result or result['cli_response'] is None
    assert result['user_input'] == 'no, my DNS is not working, ping 8.8.8.8 instead'
    assert convo.send_message.call_count == 0
