#!/usr/bin/env python3
"""
Huapala Maintenance Script

This script performs routine maintenance tasks:
1. Validates data integrity across all sources
2. Regenerates web export if needed
3. Checks for corruption and inconsistencies
4. Generates maintenance reports

Usage:
  python3 scripts/maintenance.py --validate-only    # Just run validation
  python3 scripts/maintenance.py --full             # Full maintenance including export
  python3 scripts/maintenance.py --fix-corruption   # Fix any detected corruption
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Run a shell command and return success status"""
    print(f"⚙️  {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def validate_data() -> bool:
    """Run data integrity validation"""
    return run_command(
        f"PGPASSWORD={os.getenv('PGPASSWORD', '')} python3 scripts/validate_data_integrity.py",
        "Running data integrity validation"
    )

def fix_corruption() -> bool:
    """Fix any detected verse corruption"""
    return run_command(
        f"PGPASSWORD={os.getenv('PGPASSWORD', '')} python3 scripts/fix_verses_corruption.py",
        "Fixing verse data corruption"
    )

def regenerate_web_export() -> bool:
    """Regenerate the web export data"""
    return run_command(
        f"PGPASSWORD={os.getenv('PGPASSWORD', '')} python3 scripts/export_to_web.py",
        "Regenerating web export data"
    )

def check_script_integrity() -> bool:
    """Check that all required scripts exist"""
    required_scripts = [
        "scripts/validate_data_integrity.py",
        "scripts/fix_verses_corruption.py",
        "scripts/export_to_web.py",
        "scripts/migrate_to_postgres.py",
        "scripts/json_first_processor.py"
    ]
    
    missing = []
    for script in required_scripts:
        if not Path(script).exists():
            missing.append(script)
    
    if missing:
        print("❌ Missing required scripts:")
        for script in missing:
            print(f"   - {script}")
        return False
    
    print("✅ All required scripts are present")
    return True

def generate_maintenance_report():
    """Generate a summary maintenance report"""
    report = []
    report.append("=" * 60)
    report.append("HUAPALA MAINTENANCE REPORT")
    report.append(f"Generated: {datetime.now()}")
    report.append("=" * 60)
    report.append("")
    
    # Check for recent validation reports
    validation_reports = list(Path(".").glob("validation_report_*.txt"))
    if validation_reports:
        latest_report = max(validation_reports, key=lambda x: x.stat().st_mtime)
        report.append(f"Latest validation report: {latest_report.name}")
        
        # Get basic stats from the report
        try:
            with open(latest_report, 'r') as f:
                content = f.read()
                if "STATUS: ALL VALIDATIONS PASSED" in content:
                    report.append("✅ Last validation: PASSED")
                elif "WARNINGS (no critical errors)" in content:
                    report.append("⚠️  Last validation: WARNINGS ONLY")
                else:
                    report.append("❌ Last validation: ERRORS DETECTED")
        except:
            report.append("❓ Could not read validation report")
    else:
        report.append("❓ No validation reports found")
    
    report.append("")
    
    # Check file status
    important_files = {
        "public/songs-data.json": "Web export data",
        "data/extracted_json/": "Source JSON files",
        "scripts/migrate_to_postgres.py": "Migration script",
        "scripts/json_first_processor.py": "Processing script"
    }
    
    report.append("FILE STATUS:")
    for file_path, description in important_files.items():
        path = Path(file_path)
        if path.exists():
            if path.is_file():
                size = path.stat().st_size
                modified = datetime.fromtimestamp(path.stat().st_mtime)
                report.append(f"✅ {description}: {size:,} bytes, modified {modified}")
            else:  # Directory
                file_count = len(list(path.glob("*.json")))
                report.append(f"✅ {description}: {file_count} JSON files")
        else:
            report.append(f"❌ {description}: MISSING")
    
    report.append("")
    report.append("MAINTENANCE RECOMMENDATIONS:")
    
    # Check if web export is recent
    web_export = Path("public/songs-data.json")
    if web_export.exists():
        age_hours = (datetime.now().timestamp() - web_export.stat().st_mtime) / 3600
        if age_hours > 24:
            report.append(f"⚠️  Web export is {age_hours:.1f} hours old - consider regenerating")
        else:
            report.append("✅ Web export is recent")
    
    # Check for old validation reports (cleanup)
    old_reports = [r for r in validation_reports if (datetime.now().timestamp() - r.stat().st_mtime) > (7 * 24 * 3600)]
    if old_reports:
        report.append(f"💡 Consider cleaning up {len(old_reports)} old validation reports")
    
    report.append("")
    report.append("=" * 60)
    
    report_content = "\n".join(report)
    print(report_content)
    
    # Save report
    report_file = f"maintenance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report_content)
    print(f"\nMaintenance report saved to: {report_file}")

def main():
    parser = argparse.ArgumentParser(description="Huapala maintenance script")
    parser.add_argument("--validate-only", action="store_true", help="Only run validation")
    parser.add_argument("--full", action="store_true", help="Full maintenance including web export")
    parser.add_argument("--fix-corruption", action="store_true", help="Fix detected corruption")
    parser.add_argument("--report-only", action="store_true", help="Generate maintenance report only")
    
    args = parser.parse_args()
    
    print("🔧 HUAPALA MAINTENANCE SCRIPT")
    print(f"Started: {datetime.now()}")
    print()
    
    # Check environment
    if 'PGPASSWORD' not in os.environ:
        print("❌ Error: PGPASSWORD environment variable not set")
        print("Please run: export PGPASSWORD=your_password")
        sys.exit(1)
    
    success = True
    
    if args.report_only:
        generate_maintenance_report()
        return
    
    # Check script integrity
    if not check_script_integrity():
        sys.exit(1)
    
    # Fix corruption if requested
    if args.fix_corruption:
        success &= fix_corruption()
    
    # Always run validation unless it's a full run (validation included in full)
    if args.validate_only or not args.full:
        success &= validate_data()
    
    # Full maintenance
    if args.full:
        print("🔄 Running full maintenance...")
        
        # Validate first
        success &= validate_data()
        
        # If validation passed, regenerate web export
        if success:
            success &= regenerate_web_export()
            
            # Validate again after export
            print("🔍 Re-validating after web export...")
            success &= validate_data()
    
    # Generate summary report
    generate_maintenance_report()
    
    if success:
        print("\n✅ All maintenance tasks completed successfully!")
    else:
        print("\n❌ Some maintenance tasks failed - check logs above")
        sys.exit(1)

if __name__ == "__main__":
    main()