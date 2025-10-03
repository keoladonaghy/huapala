#!/usr/bin/env python3
"""
Human Readable Formatter for Mele JSON Files

Converts structured JSON mele data to human-readable text format
with clear data type labels for review and editing, and can parse back.

Usage: 
  python format_human_readable.py export [input_dir] [output_dir]
  python format_human_readable.py import [input_dir] [output_dir]
"""

import json
import os
import sys
import re
from pathlib import Path


def format_value(value, depth=0):
    """Format a value for human readable output"""
    indent = "  " * depth
    
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        if '\n' in value:
            # Multi-line string - format with line breaks
            lines = value.split('\n')
            formatted_lines = [f"{indent}| {line}" for line in lines]
            return '\n' + '\n'.join(formatted_lines)
        else:
            return value
    elif isinstance(value, list):
        if not value:
            return "[]"
        elif all(isinstance(item, str) for item in value):
            # Simple string list
            return f"[{', '.join(value)}]"
        else:
            # Complex list - format each item
            result = "[\n"
            for i, item in enumerate(value):
                result += f"{indent}  [{i}] {format_value(item, depth + 1)}\n"
            result += f"{indent}]"
            return result
    elif isinstance(value, dict):
        if not value:
            return "{}"
        result = "{\n"
        for key, val in value.items():
            result += f"{indent}  {key}: {format_value(val, depth + 1)}\n"
        result += f"{indent}}}"
        return result
    else:
        return str(value)

def format_mele_to_text(mele_data):
    """Convert JSON mele data to complete human-readable text format"""
    
    lines = []
    
    # Header
    lines.append("=" * 80)
    lines.append("MELE DATA - EDITABLE FORMAT")
    lines.append("=" * 80)
    lines.append("")
    lines.append("# All JSON fields are preserved below for editing")
    lines.append("# Format: FIELD_NAME: value")
    lines.append("# Nested structures use indentation")
    lines.append("# Multi-line text uses | prefix")
    lines.append("")
    
    # Process all top-level fields
    for key, value in mele_data.items():
        lines.append(f"[{key.upper()}]")
        formatted_value = format_value(value)
        lines.append(formatted_value)
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("END OF MELE DATA")
    lines.append("=" * 80)
    
    return '\n'.join(lines)


def parse_value(text, depth=0):
    """Parse a formatted value back to Python object"""
    text = text.strip()
    
    if text == "null":
        return None
    elif text == "true":
        return True
    elif text == "false":
        return False
    elif text == "[]":
        return []
    elif text == "{}":
        return {}
    elif text.startswith('[') and text.endswith(']') and '\n' not in text:
        # Simple string list on one line
        content = text[1:-1].strip()
        if not content:
            return []
        # Split by comma but handle quoted strings
        items = []
        current_item = ""
        in_quotes = False
        for char in content:
            if char == '"' and (not current_item or current_item[-1] != '\\'):
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                items.append(current_item.strip())
                current_item = ""
            else:
                current_item += char
        if current_item.strip():
            items.append(current_item.strip())
        return items
    elif text.startswith('[\n') and text.endswith('\n]'):
        # Complex list with nested structures
        content = text[2:-2].strip()  # Remove [\n and \n]
        if not content:
            return []
        
        result = []
        lines = content.split('\n')
        current_item = ""
        bracket_count = 0
        
        for line in lines:
            if line.strip().startswith('[') and ']' in line and bracket_count == 0:
                # Start of new list item
                if current_item.strip():
                    # Process previous item
                    result.append(parse_value(current_item.strip(), depth + 1))
                
                # Extract value after [index]
                value_part = line.split(']', 1)[1].strip()
                current_item = value_part
                bracket_count += value_part.count('{') - value_part.count('}')
            else:
                # Continuation of current item
                current_item += '\n' + line
                bracket_count += line.count('{') - line.count('}')
        
        # Process last item
        if current_item.strip():
            result.append(parse_value(current_item.strip(), depth + 1))
        
        return result
    elif text.startswith('{\n') and text.endswith('\n}'):
        # Dictionary with nested structures
        content = text[2:-2].strip()  # Remove {\n and \n}
        if not content:
            return {}
        
        result = {}
        lines = content.split('\n')
        current_key = None
        current_value = ""
        bracket_count = 0
        
        for line in lines:
            if ':' in line and bracket_count == 0:
                # Process previous key-value pair
                if current_key and current_value.strip():
                    result[current_key] = parse_value(current_value.strip(), depth + 1)
                
                # Start new key-value pair
                key, value = line.split(':', 1)
                current_key = key.strip()
                current_value = value.strip()
                bracket_count += current_value.count('{') - current_value.count('}')
                bracket_count += current_value.count('[') - current_value.count(']')
            else:
                # Continuation of current value
                current_value += '\n' + line
                bracket_count += line.count('{') - line.count('}')
                bracket_count += line.count('[') - line.count(']')
        
        # Process last key-value pair
        if current_key and current_value.strip():
            result[current_key] = parse_value(current_value.strip(), depth + 1)
        
        return result
    elif text.startswith('\n') and '| ' in text:
        # Multi-line string
        lines = text.strip().split('\n')
        content_lines = []
        for line in lines:
            if line.strip().startswith('| '):
                content_lines.append(line.strip()[2:])  # Remove '| ' prefix
        return '\n'.join(content_lines)
    else:
        # Try to parse as number
        try:
            if '.' in text:
                return float(text)
            else:
                return int(text)
        except ValueError:
            # Return as string
            return text


def parse_text_to_mele(text_content):
    """Parse human-readable text back to JSON mele data"""
    
    lines = text_content.split('\n')
    mele_data = {}
    current_field = None
    current_content = []
    
    for line in lines:
        # Skip header/footer and comments
        if (line.startswith('=') or 
            line.startswith('#') or 
            line.strip() == "" or
            "MELE DATA" in line or
            "END OF MELE DATA" in line):
            continue
            
        # Check for field header
        if line.startswith('[') and line.endswith(']'):
            # Save previous field if exists
            if current_field and current_content:
                content_text = '\n'.join(current_content)
                mele_data[current_field.lower()] = parse_value(content_text)
            
            # Start new field
            current_field = line[1:-1]  # Remove brackets
            current_content = []
        else:
            # Accumulate content for current field
            if current_field:
                current_content.append(line)
    
    # Save last field
    if current_field and current_content:
        content_text = '\n'.join(current_content)
        mele_data[current_field.lower()] = parse_value(content_text)
    
    return mele_data


def export_to_text(input_dir, output_dir):
    """Export JSON files to human-readable text"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    json_files = list(input_path.glob('*.json'))
    mele_files = [f for f in json_files if 'summary' not in f.name.lower()]
    
    processed_count = 0
    
    for json_file in mele_files:
        print(f"Exporting: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                mele_data = json.load(f)
            
            formatted_text = format_mele_to_text(mele_data)
            
            base_name = json_file.stem
            output_file = output_path / f"{base_name}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_text)
            
            processed_count += 1
            title = mele_data.get('title', {}).get('hawaiian', 'Unknown')
            print(f"  -> Created: {output_file.name} ({title})")
            
        except Exception as e:
            print(f"  -> Error exporting {json_file}: {e}")
    
    print(f"\nExport complete! Processed {processed_count} files.")
    print(f"Output directory: {output_path}")


def import_from_text(input_dir, output_dir):
    """Import human-readable text files back to JSON"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    text_files = list(input_path.glob('*.txt'))
    
    processed_count = 0
    
    for text_file in text_files:
        print(f"Importing: {text_file.name}")
        
        try:
            with open(text_file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            mele_data = parse_text_to_mele(text_content)
            
            base_name = text_file.stem
            output_file = output_path / f"{base_name}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(mele_data, f, indent=2, ensure_ascii=False)
            
            processed_count += 1
            title = mele_data.get('title', {}).get('hawaiian', 'Unknown')
            print(f"  -> Created: {output_file.name} ({title})")
            
        except Exception as e:
            print(f"  -> Error importing {text_file}: {e}")
    
    print(f"\nImport complete! Processed {processed_count} files.")
    print(f"Output directory: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: ")
        print("  python format_human_readable.py export [input_dir] [output_dir]")
        print("  python format_human_readable.py import [input_dir] [output_dir]")
        print("  python format_human_readable.py [input_dir] [output_dir]  # legacy export mode")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command in ['export', 'import']:
        if len(sys.argv) < 3:
            print(f"Usage: python format_human_readable.py {command} [input_dir] [output_dir]")
            sys.exit(1)
        
        input_dir = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else f'./human_readable_{command}'
        
        if command == 'export':
            export_to_text(input_dir, output_dir)
        else:  # import
            import_from_text(input_dir, output_dir)
    
    else:
        # Legacy mode - assume first arg is input dir (export mode)
        input_dir = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else './human_readable'
        export_to_text(input_dir, output_dir)


if __name__ == '__main__':
    main()