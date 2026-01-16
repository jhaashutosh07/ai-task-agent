"""
Data format converter tool for converting between JSON, CSV, XML, and YAML.
"""

import csv
import io
import json
import logging
from pathlib import Path
from typing import Optional, Any
import xml.etree.ElementTree as ET
from xml.dom import minidom

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class DataConverterTool(BaseTool):
    """Tool for converting between data formats."""

    @property
    def name(self) -> str:
        return "data_converter"

    @property
    def description(self) -> str:
        return "Convert data between formats: JSON, CSV, XML, YAML. Can read from files or direct input."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "input_format": {
                    "type": "string",
                    "enum": ["json", "csv", "xml", "yaml"],
                    "description": "Format of the input data"
                },
                "output_format": {
                    "type": "string",
                    "enum": ["json", "csv", "xml", "yaml"],
                    "description": "Desired output format"
                },
                "input_data": {
                    "type": "string",
                    "description": "The data to convert (as a string)"
                },
                "input_file": {
                    "type": "string",
                    "description": "Path to input file (alternative to input_data)"
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to write output file (optional, returns data if not specified)"
                },
                "root_element": {
                    "type": "string",
                    "description": "Root element name for XML output",
                    "default": "root"
                },
                "item_element": {
                    "type": "string",
                    "description": "Item element name for XML arrays",
                    "default": "item"
                },
                "pretty": {
                    "type": "boolean",
                    "description": "Pretty print the output",
                    "default": True
                }
            },
            "required": ["input_format", "output_format"]
        }

    async def execute(
        self,
        input_format: str,
        output_format: str,
        input_data: Optional[str] = None,
        input_file: Optional[str] = None,
        output_file: Optional[str] = None,
        root_element: str = "root",
        item_element: str = "item",
        pretty: bool = True,
        **kwargs
    ) -> ToolResult:
        """Execute data conversion."""

        try:
            # Get input data
            if input_file:
                path = Path(input_file)
                if not path.exists():
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Input file not found: {input_file}"
                    )
                input_data = path.read_text(encoding="utf-8")
            elif not input_data:
                return ToolResult(
                    success=False,
                    output="",
                    error="Either input_data or input_file must be provided"
                )

            # Parse input
            parsed_data = self._parse_input(input_data, input_format, root_element)
            if parsed_data is None:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Failed to parse {input_format} input"
                )

            # Convert to output format
            output_data = self._format_output(
                parsed_data,
                output_format,
                root_element,
                item_element,
                pretty
            )
            if output_data is None:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Failed to convert to {output_format}"
                )

            # Write to file if specified
            if output_file:
                Path(output_file).write_text(output_data, encoding="utf-8")
                logger.info(f"Data converted: {input_format} -> {output_format}, saved to {output_file}")
                return ToolResult(
                    success=True,
                    output=f"Data converted successfully and saved to {output_file}"
                )

            logger.info(f"Data converted: {input_format} -> {output_format}")
            return ToolResult(
                success=True,
                output=output_data
            )

        except Exception as e:
            logger.error(f"Data conversion failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=f"Conversion failed: {str(e)}"
            )

    def _parse_input(self, data: str, format: str, root_element: str) -> Optional[Any]:
        """Parse input data based on format."""
        try:
            if format == "json":
                return json.loads(data)

            elif format == "csv":
                reader = csv.DictReader(io.StringIO(data))
                return list(reader)

            elif format == "xml":
                root = ET.fromstring(data)
                return self._xml_to_dict(root)

            elif format == "yaml":
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is not installed")
                return yaml.safe_load(data)

            return None

        except Exception as e:
            logger.error(f"Parse error for {format}: {e}")
            return None

    def _format_output(
        self,
        data: Any,
        format: str,
        root_element: str,
        item_element: str,
        pretty: bool
    ) -> Optional[str]:
        """Format data to output format."""
        try:
            if format == "json":
                if pretty:
                    return json.dumps(data, indent=2, ensure_ascii=False)
                return json.dumps(data, ensure_ascii=False)

            elif format == "csv":
                if not isinstance(data, list):
                    data = [data]
                if not data:
                    return ""

                output = io.StringIO()
                fieldnames = list(data[0].keys()) if isinstance(data[0], dict) else []
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    if isinstance(row, dict):
                        writer.writerow(row)
                return output.getvalue()

            elif format == "xml":
                root = self._dict_to_xml(data, root_element, item_element)
                if pretty:
                    xml_str = ET.tostring(root, encoding="unicode")
                    parsed = minidom.parseString(xml_str)
                    return parsed.toprettyxml(indent="  ")
                return ET.tostring(root, encoding="unicode")

            elif format == "yaml":
                if not YAML_AVAILABLE:
                    raise ImportError("PyYAML is not installed")
                return yaml.dump(data, default_flow_style=False, allow_unicode=True)

            return None

        except Exception as e:
            logger.error(f"Format error for {format}: {e}")
            return None

    def _xml_to_dict(self, element: ET.Element) -> dict:
        """Convert XML element to dictionary."""
        result = {}

        # Handle attributes
        if element.attrib:
            result["@attributes"] = element.attrib

        # Handle children
        children = list(element)
        if children:
            child_dict = {}
            for child in children:
                child_data = self._xml_to_dict(child)
                if child.tag in child_dict:
                    # Multiple children with same tag -> make list
                    if not isinstance(child_dict[child.tag], list):
                        child_dict[child.tag] = [child_dict[child.tag]]
                    child_dict[child.tag].append(child_data)
                else:
                    child_dict[child.tag] = child_data
            result.update(child_dict)
        elif element.text and element.text.strip():
            return element.text.strip()

        return result if result else (element.text or "").strip()

    def _dict_to_xml(self, data: Any, tag: str, item_element: str) -> ET.Element:
        """Convert dictionary/list to XML element."""
        element = ET.Element(tag)

        if isinstance(data, dict):
            for key, value in data.items():
                if key == "@attributes":
                    for attr_key, attr_val in value.items():
                        element.set(attr_key, str(attr_val))
                elif isinstance(value, list):
                    for item in value:
                        child = self._dict_to_xml(item, key, item_element)
                        element.append(child)
                elif isinstance(value, dict):
                    child = self._dict_to_xml(value, key, item_element)
                    element.append(child)
                else:
                    child = ET.SubElement(element, key)
                    child.text = str(value) if value is not None else ""
        elif isinstance(data, list):
            for item in data:
                child = self._dict_to_xml(item, item_element, item_element)
                element.append(child)
        else:
            element.text = str(data) if data is not None else ""

        return element
