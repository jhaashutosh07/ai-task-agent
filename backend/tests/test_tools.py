"""
Tests for tools functionality.
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCalculatorTool:
    """Tests for the calculator tool."""

    @pytest.fixture
    def calculator_tool(self):
        """Get calculator tool instance."""
        from tools.basic_tools import CalculatorTool
        return CalculatorTool()

    @pytest.mark.asyncio
    async def test_addition(self, calculator_tool):
        """Test addition operation."""
        result = await calculator_tool.execute(
            operation="add",
            a=5,
            b=3
        )
        assert result["result"] == 8

    @pytest.mark.asyncio
    async def test_subtraction(self, calculator_tool):
        """Test subtraction operation."""
        result = await calculator_tool.execute(
            operation="subtract",
            a=10,
            b=4
        )
        assert result["result"] == 6

    @pytest.mark.asyncio
    async def test_multiplication(self, calculator_tool):
        """Test multiplication operation."""
        result = await calculator_tool.execute(
            operation="multiply",
            a=6,
            b=7
        )
        assert result["result"] == 42

    @pytest.mark.asyncio
    async def test_division(self, calculator_tool):
        """Test division operation."""
        result = await calculator_tool.execute(
            operation="divide",
            a=20,
            b=4
        )
        assert result["result"] == 5

    @pytest.mark.asyncio
    async def test_division_by_zero(self, calculator_tool):
        """Test division by zero returns error."""
        result = await calculator_tool.execute(
            operation="divide",
            a=10,
            b=0
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_power(self, calculator_tool):
        """Test power operation."""
        result = await calculator_tool.execute(
            operation="power",
            a=2,
            b=10
        )
        assert result["result"] == 1024

    @pytest.mark.asyncio
    async def test_unknown_operation(self, calculator_tool):
        """Test unknown operation returns error."""
        result = await calculator_tool.execute(
            operation="unknown",
            a=5,
            b=3
        )
        assert "error" in result


class TestDateTimeTool:
    """Tests for the datetime tool."""

    @pytest.fixture
    def datetime_tool(self):
        """Get datetime tool instance."""
        from tools.basic_tools import DateTimeTool
        return DateTimeTool()

    @pytest.mark.asyncio
    async def test_current_time(self, datetime_tool):
        """Test getting current time."""
        result = await datetime_tool.execute(action="current")
        assert "current_time" in result or "datetime" in result

    @pytest.mark.asyncio
    async def test_format_date(self, datetime_tool):
        """Test date formatting."""
        result = await datetime_tool.execute(
            action="format",
            date="2024-01-15",
            format="%B %d, %Y"
        )
        assert "January" in str(result) or "formatted" in str(result).lower()


class TestFileTools:
    """Tests for file operation tools."""

    @pytest.fixture
    def file_reader(self):
        """Get file reader tool instance."""
        from tools.basic_tools import FileReaderTool
        return FileReaderTool()

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, file_reader):
        """Test reading a file that doesn't exist."""
        result = await file_reader.execute(
            file_path="/nonexistent/path/to/file.txt"
        )
        assert "error" in result or "not found" in str(result).lower()


class TestToolRegistry:
    """Tests for the tool registry."""

    def test_tool_registration(self):
        """Test that tools are properly registered."""
        from tools import get_tool, list_tools

        # Check calculator is registered
        calc = get_tool("calculator")
        assert calc is not None

        # Check listing tools works
        tools = list_tools()
        assert len(tools) > 0
        assert any(t.get("name") == "calculator" or "calculator" in str(t) for t in tools)


class TestSafeExpressionEvaluator:
    """Tests for safe expression evaluation in workflow engine."""

    def test_safe_eval_simple_comparison(self):
        """Test simple comparisons work."""
        from simpleeval import EvalWithCompoundTypes

        evaluator = EvalWithCompoundTypes(names={"x": 5})
        result = evaluator.eval("x > 3")
        assert result is True

    def test_safe_eval_arithmetic(self):
        """Test arithmetic operations work."""
        from simpleeval import EvalWithCompoundTypes

        evaluator = EvalWithCompoundTypes(names={"a": 10, "b": 5})
        result = evaluator.eval("a + b")
        assert result == 15

    def test_safe_eval_boolean_logic(self):
        """Test boolean logic works."""
        from simpleeval import EvalWithCompoundTypes

        evaluator = EvalWithCompoundTypes(names={"status": "success"})
        result = evaluator.eval("status == 'success'")
        assert result is True

    def test_safe_eval_prevents_dangerous_code(self):
        """Test that dangerous operations are blocked."""
        from simpleeval import EvalWithCompoundTypes, FeatureNotAvailable

        evaluator = EvalWithCompoundTypes(names={})

        # Should not be able to import modules
        with pytest.raises((FeatureNotAvailable, Exception)):
            evaluator.eval("__import__('os').system('echo hacked')")

        # Should not be able to access builtins
        with pytest.raises((FeatureNotAvailable, Exception, NameError)):
            evaluator.eval("open('/etc/passwd')")
