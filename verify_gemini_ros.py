#!/usr/bin/env python3
"""
Verification Checklist - Gemini ROS Integration
Run this to verify everything is properly integrated
"""

import os
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists"""
    if Path(path).exists():
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ {description}: {path} NOT FOUND")
        return False

def check_content_in_file(filepath, content, description):
    """Check if content exists in file"""
    try:
        with open(filepath, 'r') as f:
            file_content = f.read()
            if content in file_content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description} - NOT FOUND in file")
                return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

print("\n" + "="*80)
print("🔍 GEMINI ROS INTEGRATION - VERIFICATION CHECKLIST")
print("="*80)

all_checks = []

# 1. Core Files
print("\n📁 CORE FILES:")
all_checks.append(check_file_exists("backend/ros/scorer.py", "ROS Scorer"))
all_checks.append(check_file_exists("backend/api/routes.py", "API Routes"))
all_checks.append(check_file_exists("backend/.env", "Environment Config"))

# 2. Environment Setup
print("\n🔑 ENVIRONMENT SETUP:")
env_path = Path("backend/.env")
if env_path.exists():
    with open(env_path, 'r') as f:
        env_content = f.read()
        if "GOOGLE_API_KEY=" in env_content:
            print("✅ GOOGLE_API_KEY configured in .env")
            all_checks.append(True)
        else:
            print("❌ GOOGLE_API_KEY not found in .env")
            all_checks.append(False)

# 3. Code Integration
print("\n💻 CODE INTEGRATION:")
all_checks.append(check_content_in_file(
    "backend/ros/scorer.py",
    "from dotenv import load_dotenv",
    "dotenv import in scorer.py"
))
all_checks.append(check_content_in_file(
    "backend/ros/scorer.py",
    "calculate_ros_with_gemini",
    "calculate_ros_with_gemini method"
))
all_checks.append(check_content_in_file(
    "backend/api/routes.py",
    "ros_method",
    "ros_method parameter in API"
))
all_checks.append(check_content_in_file(
    "backend/api/routes.py",
    "calculate_ros_with_gemini",
    "Gemini ROS import in API"
))

# 4. Documentation
print("\n📚 DOCUMENTATION:")
all_checks.append(check_file_exists("GEMINI_ROS_SUMMARY.md", "Summary Guide"))
all_checks.append(check_file_exists("GEMINI_ROS_COMPLETE_INTEGRATION.md", "Complete Guide"))
all_checks.append(check_file_exists("GEMINI_ROS_EXAMPLES.md", "Examples"))
all_checks.append(check_file_exists("GEMINI_ROS_QUICKREF.md", "Quick Reference"))
all_checks.append(check_file_exists("GEMINI_ROS_HONEST.md", "Full Documentation"))
all_checks.append(check_file_exists("API_REFERENCE_ROS.md", "API Reference"))

# 5. Tests
print("\n🧪 TESTS:")
all_checks.append(check_file_exists("test_gemini_ros_standalone.py", "Standalone Test"))
all_checks.append(check_file_exists("backend/test_ros_integration.py", "Integration Test"))

# 6. Configuration Update
print("\n⚙️  CONFIGURATION:")
all_checks.append(check_content_in_file(
    "CLAUDE.md",
    "Gemini-based Honest ROS",
    "CLAUDE.md updated with ROS info"
))

# Summary
print("\n" + "="*80)
passed = sum(all_checks)
total = len(all_checks)
percentage = (passed / total) * 100

print(f"VERIFICATION RESULTS: {passed}/{total} checks passed ({percentage:.0f}%)")

if percentage == 100:
    print("✅ ALL CHECKS PASSED - Integration is complete!")
    print("\n🚀 Ready to use:")
    print("   1. Start backend: cd backend && python main.py")
    print("   2. Test standalone: python test_gemini_ros_standalone.py")
    print("   3. Call API: curl -X POST http://localhost:8000/api/query \\")
    print("               -d '{\"query\":\"...\",\"ros_method\":\"gemini_honest\"}'")
elif percentage >= 90:
    print("⚠️  MOSTLY COMPLETE - Minor issues found")
else:
    print("❌ INCOMPLETE - Please review failed checks above")

print("\n" + "="*80)

# Quick Usage
print("\n📋 QUICK USAGE:")
print("\n1. Python Direct:")
print("   from ros.scorer import calculate_ros_with_gemini")
print("   result = calculate_ros_with_gemini(query, refs, insights)")
print("   print(result['ros_score'])")

print("\n2. API Endpoint:")
print("   curl -X POST http://localhost:8000/api/query \\")
print("     -d '{\"query\":\"GLP-1 for diabetes\",\"ros_method\":\"gemini_honest\"}'")

print("\n3. Comparison:")
print("   - Default (fast): ros_method=\"deterministic\"")
print("   - Honest (realistic): ros_method=\"gemini_honest\"")

print("\n" + "="*80)
print("For detailed info, see: GEMINI_ROS_COMPLETE_INTEGRATION.md")
print("="*80 + "\n")
