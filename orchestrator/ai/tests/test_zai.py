import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from orchestrator.ai.zai import ZaiGLMClient, ZaiClientError


@pytest.fixture
def zai_client():
    """Returns a new, unconfigured ZaiClient instance for each test."""
    # Reset the singleton instance before each test
    ZaiClient._instance = None
    return ZaiClient()


def test_zai_client_lazy_initialization(zai_client):
    """Tests that the ZaiClient is not configured on import."""
    assert not zai_client._configured
    assert zai_client._client is None


@patch("orchestrator.ai.zai.zai_sdk")
def test_zai_client_configure_success(mock_zai_sdk, zai_client):
    """Tests the configure() method with a valid API key."""
    mock_sdk_instance = MagicMock()
    mock_zai_sdk.ZaiClient.return_value = mock_sdk_instance

    zai_client.configure(api_key="valid_key")

    assert zai_client._configured
    assert zai_client._client is not None
    mock_zai_sdk.ZaiClient.assert_called_once_with(api_key="valid_key")


@patch("orchestrator.ai.zai.zai_sdk")
def test_zai_client_configure_invalid_key(mock_zai_sdk, zai_client):
    """Tests the configure() method with an invalid API key."""
    mock_zai_sdk.ZaiClient.side_effect = Exception("Invalid API Key")

    with pytest.raises(ZaiClientError, match="Failed to configure ZAI client"):
        zai_client.configure(api_key="invalid_key")

    assert not zai_client._configured
    assert zai_client._client is None


def test_error_handling_missing_api_key(zai_client):
    """Tests that an error is raised if the API key is missing."""
    with pytest.raises(ZaiClientError, match="ZAI client is not configured"):
        zai_client.generate_response("test prompt")


@pytest.mark.asyncio
async def test_generate_response_wraps_sdk_call_in_executor(zai_client):
    """Tests that generate_response() wraps the SDK call in an executor."""
    # Configure the client
    with patch("orchestrator.ai.zai.zai_sdk") as mock_zai_sdk:
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.generate.return_value = "mocked response"
        mock_zai_sdk.ZaiClient.return_value = mock_sdk_instance
        zai_client.configure(api_key="valid_key")

    # Mock run_in_executor
    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value="mocked response")
        mock_get_loop.return_value = mock_loop

        response = await zai_client.generate_response("test prompt")

        assert response == "mocked response"
        mock_loop.run_in_executor.assert_called_once()
        # Check that the SDK method was passed to the executor
        call_args = mock_loop.run_in_executor.call_args
        assert call_args[0][1] == zai_client._client.generate
        assert call_args[0][2] == "test prompt"


@pytest.mark.asyncio
async def test_plan_mission_returns_agent_list(zai_client):
    """Tests that plan_mission() returns a list of agents."""
    with patch("orchestrator.ai.zai.zai_sdk") as mock_zai_sdk:
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.plan.return_value = ["agent1", "agent2"]
        mock_zai_sdk.ZaiClient.return_value = mock_sdk_instance
        zai_client.configure(api_key="valid_key")

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value=["agent1", "agent2"])
        mock_get_loop.return_value = mock_loop

        agents = await zai_client.plan_mission("test mission")

        assert agents == ["agent1", "agent2"]
        mock_loop.run_in_executor.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_results_returns_answer(zai_client):
    """Tests that synthesize_results() returns a synthesized answer."""
    with patch("orchestrator.ai.zai.zai_sdk") as mock_zai_sdk:
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.synthesize.return_value = "synthesized answer"
        mock_zai_sdk.ZaiClient.return_value = mock_sdk_instance
        zai_client.configure(api_key="valid_key")

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        mock_loop.run_in_executor = AsyncMock(return_value="synthesized answer")
        mock_get_loop.return_value = mock_loop

        answer = await zai_client.synthesize_results("test results")

        assert answer == "synthesized answer"
        mock_loop.run_in_executor.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling_sdk_error(zai_client):
    """Tests error handling for SDK errors."""
    with patch("orchestrator.ai.zai.zai_sdk") as mock_zai_sdk:
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.generate.side_effect = Exception("SDK Error")
        mock_zai_sdk.ZaiClient.return_value = mock_sdk_instance
        zai_client.configure(api_key="valid_key")

    with patch("asyncio.get_running_loop") as mock_get_loop:
        mock_loop = MagicMock()
        # Simulate the executor raising the exception
        mock_loop.run_in_executor = AsyncMock(side_effect=Exception("SDK Error"))
        mock_get_loop.return_value = mock_loop

        with pytest.raises(ZaiClientError, match="ZAI SDK error"):
            await zai_client.generate_response("test prompt")
