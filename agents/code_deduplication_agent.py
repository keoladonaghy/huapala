#!/usr/bin/env python3
"""
Code Deduplication Analysis Agent

Periodically scans the codebase to identify code duplication patterns that could be
consolidated into shared modules or single sources of truth. Generates actionable
reports for refactoring opportunities.

Based on the authentication centralization success, this agent identifies similar
patterns where functionality is reimplemented instead of shared.
"""

import os
import re
import ast
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter
from dataclasses import dataclass
import difflib

@dataclass
class DuplicationPattern:
    """Represents a detected code duplication pattern"""
    pattern_type: str
    description: str
    locations: List[Dict[str, Any]]
    similarity_score: float
    lines_duplicated: int
    suggested_solution: str
    priority: str  # "high", "medium", "low"
    estimated_savings: str

@dataclass
class AnalysisReport:
    """Complete analysis report"""
    timestamp: str
    total_files_analyzed: int
    patterns_found: List[DuplicationPattern]
    summary: Dict[str, Any]
    recommendations: List[str]

class CodeDeduplicationAgent:
    """Agent to analyze and detect code duplication patterns"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.ignored_patterns = {
            "__pycache__", ".git", "node_modules", ".env", "venv",
            "*.pyc", "*.log", "*.tmp", "backups"
        }
        self.file_extensions = {".py", ".js", ".html", ".css", ".sql"}
        
    def should_analyze_file(self, file_path: Path) -> bool:
        """Determine if file should be included in analysis"""
        if any(pattern in str(file_path) for pattern in self.ignored_patterns):
            return False
        if file_path.suffix not in self.file_extensions:
            return False
        if file_path.stat().st_size > 1024 * 1024:  # Skip files > 1MB
            return False
        return True
    
    def extract_functions(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract function definitions from Python files"""
        functions = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function source
                    lines = content.split('\n')
                    start_line = node.lineno - 1
                    
                    # Find end of function (rough estimation)
                    end_line = start_line + 1
                    while end_line < len(lines) and (
                        lines[end_line].startswith('    ') or 
                        lines[end_line].strip() == ''
                    ):
                        end_line += 1
                    
                    func_source = '\n'.join(lines[start_line:end_line])
                    
                    functions.append({
                        'name': node.name,
                        'file': str(file_path),
                        'start_line': node.lineno,
                        'end_line': end_line,
                        'source': func_source,
                        'args': [arg.arg for arg in node.args.args],
                        'hash': hashlib.md5(func_source.encode()).hexdigest()
                    })
        except (SyntaxError, UnicodeDecodeError):
            pass  # Skip files with syntax errors
        
        return functions
    
    def extract_patterns(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract common code patterns from any file type"""
        patterns = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            # Database connection patterns
            db_patterns = self.find_database_patterns(lines, file_path)
            patterns.extend(db_patterns)
            
            # Authentication patterns
            auth_patterns = self.find_auth_patterns(lines, file_path)
            patterns.extend(auth_patterns)
            
            # Error handling patterns
            error_patterns = self.find_error_handling_patterns(lines, file_path)
            patterns.extend(error_patterns)
            
            # Configuration patterns
            config_patterns = self.find_config_patterns(lines, file_path)
            patterns.extend(config_patterns)
            
            # HTTP request patterns
            http_patterns = self.find_http_patterns(lines, file_path)
            patterns.extend(http_patterns)
            
        except UnicodeDecodeError:
            pass  # Skip binary files
        
        return patterns
    
    def find_database_patterns(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Find database connection and query patterns"""
        patterns = []
        
        # Database connection patterns
        for i, line in enumerate(lines):
            if re.search(r'psycopg2\.connect\(|get_db_connection\(|SessionLocal\(', line):
                patterns.append({
                    'type': 'database_connection',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'pattern': 'database_connection'
                })
        
        # SQL query patterns (look for repeated query structures)
        sql_patterns = []
        for i, line in enumerate(lines):
            if re.search(r'SELECT|INSERT|UPDATE|DELETE', line, re.IGNORECASE):
                # Normalize query for pattern matching
                normalized = re.sub(r'["\'].*?["\']', '?', line)  # Replace string literals
                normalized = re.sub(r'\b\d+\b', '?', normalized)  # Replace numbers
                sql_patterns.append({
                    'type': 'sql_query',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'normalized': normalized,
                    'pattern': 'sql_query'
                })
        
        patterns.extend(sql_patterns)
        return patterns
    
    def find_auth_patterns(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Find authentication and session patterns"""
        patterns = []
        
        for i, line in enumerate(lines):
            # Session validation patterns
            if re.search(r'cookies\.get.*session|validate_session|check.*auth', line, re.IGNORECASE):
                patterns.append({
                    'type': 'auth_check',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'pattern': 'authentication'
                })
            
            # Password/credential patterns
            if re.search(r'password|credential|token.*generate|auth.*header', line, re.IGNORECASE):
                patterns.append({
                    'type': 'credential_handling',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'pattern': 'authentication'
                })
        
        return patterns
    
    def find_error_handling_patterns(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Find error handling patterns"""
        patterns = []
        
        for i, line in enumerate(lines):
            if re.search(r'try:|except|raise HTTPException|raise.*Error', line):
                # Look for similar try/except blocks
                context = []
                for j in range(max(0, i-2), min(len(lines), i+5)):
                    context.append(lines[j].strip())
                
                patterns.append({
                    'type': 'error_handling',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'context': context,
                    'pattern': 'error_handling'
                })
        
        return patterns
    
    def find_config_patterns(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Find configuration and environment variable patterns"""
        patterns = []
        
        for i, line in enumerate(lines):
            if re.search(r'os\.getenv|os\.environ|getenv|config\.|settings\.', line):
                patterns.append({
                    'type': 'config_access',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'pattern': 'configuration'
                })
        
        return patterns
    
    def find_http_patterns(self, lines: List[str], file_path: Path) -> List[Dict[str, Any]]:
        """Find HTTP request/response patterns"""
        patterns = []
        
        for i, line in enumerate(lines):
            if re.search(r'@app\.(get|post|put|delete)|fetch\(|axios\.|requests\.', line):
                patterns.append({
                    'type': 'http_endpoint',
                    'file': str(file_path),
                    'line': i + 1,
                    'content': line.strip(),
                    'pattern': 'http_handling'
                })
        
        return patterns
    
    def analyze_similarity(self, items: List[Dict[str, Any]], threshold: float = 0.7) -> List[DuplicationPattern]:
        """Analyze items for similarity and duplication"""
        duplications = []
        processed = set()
        
        for i, item1 in enumerate(items):
            if i in processed:
                continue
                
            similar_items = [item1]
            for j, item2 in enumerate(items[i+1:], i+1):
                if j in processed:
                    continue
                
                similarity = self.calculate_similarity(item1, item2)
                if similarity >= threshold:
                    similar_items.append(item2)
                    processed.add(j)
            
            if len(similar_items) > 1:
                duplications.append(self.create_duplication_pattern(similar_items))
                processed.add(i)
        
        return duplications
    
    def calculate_similarity(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """Calculate similarity between two code items"""
        if item1.get('type') != item2.get('type'):
            return 0.0
        
        # Use different similarity metrics based on type
        if item1.get('type') == 'sql_query':
            return self.sql_similarity(item1, item2)
        elif 'source' in item1 and 'source' in item2:
            return self.code_similarity(item1['source'], item2['source'])
        elif 'content' in item1 and 'content' in item2:
            return self.text_similarity(item1['content'], item2['content'])
        
        return 0.0
    
    def sql_similarity(self, item1: Dict[str, Any], item2: Dict[str, Any]) -> float:
        """Calculate similarity between SQL queries"""
        norm1 = item1.get('normalized', '')
        norm2 = item2.get('normalized', '')
        return difflib.SequenceMatcher(None, norm1, norm2).ratio()
    
    def code_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between code blocks"""
        # Normalize whitespace and comments
        normalized1 = re.sub(r'#.*', '', code1)
        normalized2 = re.sub(r'#.*', '', code2)
        normalized1 = re.sub(r'\s+', ' ', normalized1).strip()
        normalized2 = re.sub(r'\s+', ' ', normalized2).strip()
        
        return difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
    
    def text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between text lines"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def create_duplication_pattern(self, similar_items: List[Dict[str, Any]]) -> DuplicationPattern:
        """Create a duplication pattern from similar items"""
        pattern_type = similar_items[0].get('type', 'unknown')
        
        # Calculate average similarity
        similarities = []
        for i in range(len(similar_items)):
            for j in range(i+1, len(similar_items)):
                similarities.append(self.calculate_similarity(similar_items[i], similar_items[j]))
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Estimate lines of code
        lines_count = 0
        for item in similar_items:
            if 'source' in item:
                lines_count += len(item['source'].split('\n'))
            else:
                lines_count += 1
        
        # Generate suggestions based on pattern type
        suggestion = self.generate_suggestion(pattern_type, similar_items)
        priority = self.calculate_priority(pattern_type, len(similar_items), avg_similarity)
        
        return DuplicationPattern(
            pattern_type=pattern_type,
            description=f"Found {len(similar_items)} similar {pattern_type} patterns",
            locations=[{
                'file': item.get('file', ''),
                'line': item.get('line', 0),
                'content': item.get('content', '')[:100] + '...' if len(item.get('content', '')) > 100 else item.get('content', '')
            } for item in similar_items],
            similarity_score=avg_similarity,
            lines_duplicated=lines_count,
            suggested_solution=suggestion,
            priority=priority,
            estimated_savings=f"{lines_count} lines, {len(similar_items)} locations"
        )
    
    def generate_suggestion(self, pattern_type: str, items: List[Dict[str, Any]]) -> str:
        """Generate refactoring suggestions based on pattern type"""
        suggestions = {
            'database_connection': "Create shared database connection utility in `database.py` or `auth.py`",
            'sql_query': "Consider creating shared query functions or use an ORM query builder",
            'auth_check': "Use centralized authentication from `auth.py` module",
            'error_handling': "Create shared error handling decorators or middleware",
            'config_access': "Centralize configuration access in a `config.py` module",
            'http_endpoint': "Consider grouping similar endpoints or creating shared response handlers",
            'credential_handling': "Use shared credential management from `auth.py`"
        }
        
        base_suggestion = suggestions.get(pattern_type, "Consider extracting common functionality into a shared module")
        
        if len(items) >= 5:
            return base_suggestion + " (HIGH PRIORITY - Found in many locations)"
        elif len(items) >= 3:
            return base_suggestion + " (MEDIUM PRIORITY - Multiple locations)"
        else:
            return base_suggestion + " (LOW PRIORITY - Few locations)"
    
    def calculate_priority(self, pattern_type: str, count: int, similarity: float) -> str:
        """Calculate priority based on pattern characteristics"""
        # High-priority patterns
        if pattern_type in ['auth_check', 'database_connection', 'credential_handling']:
            if count >= 3 and similarity >= 0.8:
                return "high"
        
        # Medium priority
        if count >= 4 or (count >= 2 and similarity >= 0.9):
            return "medium"
        
        return "low"
    
    def analyze_project(self) -> AnalysisReport:
        """Perform complete project analysis"""
        print("🔍 Starting code deduplication analysis...")
        
        all_functions = []
        all_patterns = []
        file_count = 0
        
        # Collect all code patterns
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and self.should_analyze_file(file_path):
                file_count += 1
                print(f"📄 Analyzing: {file_path}")
                
                if file_path.suffix == '.py':
                    functions = self.extract_functions(file_path)
                    all_functions.extend(functions)
                
                patterns = self.extract_patterns(file_path)
                all_patterns.extend(patterns)
        
        print(f"📊 Analysis complete: {file_count} files, {len(all_functions)} functions, {len(all_patterns)} patterns")
        
        # Analyze for duplications
        duplications = []
        
        # Analyze function duplications
        func_duplications = self.analyze_similarity(all_functions, threshold=0.7)
        duplications.extend(func_duplications)
        
        # Group patterns by type and analyze
        pattern_groups = defaultdict(list)
        for pattern in all_patterns:
            pattern_groups[pattern['type']].append(pattern)
        
        for pattern_type, patterns in pattern_groups.items():
            if len(patterns) > 1:
                type_duplications = self.analyze_similarity(patterns, threshold=0.6)
                duplications.extend(type_duplications)
        
        # Sort by priority and similarity
        duplications.sort(key=lambda x: (
            {"high": 3, "medium": 2, "low": 1}[x.priority],
            x.similarity_score,
            len(x.locations)
        ), reverse=True)
        
        # Generate summary
        summary = {
            "total_duplications": len(duplications),
            "high_priority": len([d for d in duplications if d.priority == "high"]),
            "medium_priority": len([d for d in duplications if d.priority == "medium"]),
            "low_priority": len([d for d in duplications if d.priority == "low"]),
            "total_lines_duplicated": sum(d.lines_duplicated for d in duplications),
            "pattern_types": list(set(d.pattern_type for d in duplications))
        }
        
        # Generate recommendations
        recommendations = self.generate_recommendations(duplications)
        
        return AnalysisReport(
            timestamp=datetime.now().isoformat(),
            total_files_analyzed=file_count,
            patterns_found=duplications,
            summary=summary,
            recommendations=recommendations
        )
    
    def generate_recommendations(self, duplications: List[DuplicationPattern]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        high_priority = [d for d in duplications if d.priority == "high"]
        if high_priority:
            recommendations.append(
                f"🚨 HIGH PRIORITY: Address {len(high_priority)} critical duplication patterns immediately"
            )
        
        # Pattern-specific recommendations
        pattern_counts = Counter(d.pattern_type for d in duplications)
        for pattern_type, count in pattern_counts.most_common(3):
            if count >= 3:
                recommendations.append(
                    f"🔧 Consider creating shared utilities for {pattern_type} (found {count} times)"
                )
        
        # General recommendations
        if len(duplications) > 10:
            recommendations.append(
                "📋 Create a refactoring plan to address duplications systematically"
            )
        
        recommendations.append(
            "🔄 Run this analysis weekly to catch new duplication patterns early"
        )
        
        return recommendations
    
    def generate_report(self, report: AnalysisReport) -> str:
        """Generate human-readable report"""
        output = []
        output.append("=" * 80)
        output.append("CODE DEDUPLICATION ANALYSIS REPORT")
        output.append("=" * 80)
        output.append(f"Generated: {report.timestamp}")
        output.append(f"Files Analyzed: {report.total_files_analyzed}")
        output.append("")
        
        # Summary
        output.append("📊 SUMMARY")
        output.append("-" * 40)
        output.append(f"Total Duplication Patterns: {report.summary['total_duplications']}")
        output.append(f"High Priority: {report.summary['high_priority']}")
        output.append(f"Medium Priority: {report.summary['medium_priority']}")
        output.append(f"Low Priority: {report.summary['low_priority']}")
        output.append(f"Total Lines Duplicated: {report.summary['total_lines_duplicated']}")
        output.append("")
        
        # Recommendations
        output.append("💡 RECOMMENDATIONS")
        output.append("-" * 40)
        for rec in report.recommendations:
            output.append(f"• {rec}")
        output.append("")
        
        # Detailed patterns
        output.append("🔍 DETAILED PATTERNS")
        output.append("-" * 40)
        
        for i, pattern in enumerate(report.patterns_found[:10], 1):  # Top 10
            output.append(f"\n{i}. {pattern.description}")
            output.append(f"   Type: {pattern.pattern_type}")
            output.append(f"   Priority: {pattern.priority.upper()}")
            output.append(f"   Similarity: {pattern.similarity_score:.2%}")
            output.append(f"   Estimated Savings: {pattern.estimated_savings}")
            output.append(f"   Suggestion: {pattern.suggested_solution}")
            output.append("   Locations:")
            for loc in pattern.locations[:5]:  # First 5 locations
                output.append(f"     - {loc['file']}:{loc['line']} - {loc['content']}")
            if len(pattern.locations) > 5:
                output.append(f"     ... and {len(pattern.locations) - 5} more locations")
        
        if len(report.patterns_found) > 10:
            output.append(f"\n... and {len(report.patterns_found) - 10} more patterns")
        
        output.append("\n" + "=" * 80)
        
        return "\n".join(output)
    
    def save_report(self, report: AnalysisReport, output_file: str = None) -> str:
        """Save report to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"code_deduplication_report_{timestamp}.txt"
        
        report_text = self.generate_report(report)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return output_file

def main():
    """Run the code deduplication analysis"""
    agent = CodeDeduplicationAgent()
    report = agent.analyze_project()
    
    # Print summary to console
    print("\n" + "=" * 80)
    print("CODE DEDUPLICATION ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Found {report.summary['total_duplications']} duplication patterns")
    print(f"High Priority: {report.summary['high_priority']}")
    print(f"Potential Savings: {report.summary['total_lines_duplicated']} lines")
    
    # Save detailed report
    report_file = agent.save_report(report)
    print(f"📄 Detailed report saved to: {report_file}")
    
    # Show top recommendations
    print("\n💡 TOP RECOMMENDATIONS:")
    for rec in report.recommendations[:3]:
        print(f"   • {rec}")

if __name__ == "__main__":
    main()