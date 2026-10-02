#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill验证和打包脚本
"""
import os
import sys
import zipfile
from pathlib import Path

def validate_skill(skill_path):
    """验证Skill结构"""
    skill_md = os.path.join(skill_path, "SKILL.md")
    
    if not os.path.exists(skill_md):
        return False, "SKILL.md not found"
    
    with open(skill_md, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查frontmatter
    if not content.startswith('---'):
        return False, "Missing YAML frontmatter"
    
    # 检查必需字段
    if 'name:' not in content:
        return False, "Missing 'name' in frontmatter"
    
    if 'description:' not in content:
        return False, "Missing 'description' in frontmatter"
    
    return True, "Valid"

def package_skill(skill_path, output_dir):
    """打包Skill为zip"""
    skill_path = Path(skill_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = output_dir / f"{skill_path.name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(skill_path):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(skill_path.parent)
                zf.write(file_path, arcname)
    
    return zip_path

if __name__ == "__main__":
    skill_path = sys.argv[1] if len(sys.argv) > 1 else r"c:\Users\user\.workbuddy\skills\kibana-log-analyzer"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else r"c:\Users\user\WorkBuddy\Claw"
    
    print(f"Validating skill: {skill_path}")
    valid, msg = validate_skill(skill_path)
    
    if not valid:
        print(f"Validation failed: {msg}")
        sys.exit(1)
    
    print(f"Validation passed: {msg}")
    print(f"Packaging skill...")
    
    zip_path = package_skill(skill_path, output_dir)
    print(f"Skill packaged: {zip_path}")
