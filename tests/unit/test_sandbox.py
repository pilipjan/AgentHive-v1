"""Unit tests for ToolSandbox execution and isolation."""

import pytest
from agent_runtime.tools.sandbox import ToolSandbox


@pytest.mark.asyncio
async def test_calculator_tool_success():
    res = await ToolSandbox.execute_tool("calculator", {"expression": "(12 * 4) + 10"})
    assert res.success is True
    assert res.output == 58.0
    assert res.error is None


@pytest.mark.asyncio
async def test_calculator_tool_injection_protection():
    # Expression containing letters or unsafe characters must fail
    res = await ToolSandbox.execute_tool("calculator", {"expression": "__import__('os').system('ls')"})
    assert res.success is False
    assert "invalid non-arithmetic characters" in res.error


@pytest.mark.asyncio
async def test_json_validator_tool():
    valid_json = '{"agent": "PythonForge", "score": 4.87, "capabilities": ["python"]}'
    res = await ToolSandbox.execute_tool("json_validator", {"json_string": valid_json})
    assert res.success is True
    assert res.output["agent"] == "PythonForge"
    assert res.output["score"] == 4.87

    invalid_json = '{"agent": "broken", '
    res_bad = await ToolSandbox.execute_tool("json_validator", {"json_string": invalid_json})
    assert res_bad.success is False
    assert "Execution error" in res_bad.error


@pytest.mark.asyncio
async def test_word_counter_tool():
    text = "AgentHive platform provides multi-agent orchestration."
    res = await ToolSandbox.execute_tool("word_counter", {"text": text})
    assert res.success is True
    assert res.output["word_count"] == 5


@pytest.mark.asyncio
async def test_unregistered_tool_rejection():
    res = await ToolSandbox.execute_tool("bash_shell", {"command": "echo test"})
    assert res.success is False
    assert "not registered in the safe execution sandbox" in res.error
