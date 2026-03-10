"""
Create a test issue on GitHub using the API.

This script creates a real issue to test the automation pipeline.
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path


def create_github_issue():
    """Create a test issue on GitHub."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        return None

    repo_owner = "ninesun666"
    repo_name = "ninesun-blog"

    # Issue data
    issue_data = {
        "title": "[AI-Harness测试] 前端分类界面优化",
        "body": f"""## 问题描述

当前的分类界面存在以下问题：
- 分类列表展示不够直观
- 缺少分类图标
- 响应式布局存在问题

## 期望效果

- [ ] 优化分类卡片样式，增加图标展示
- [ ] 支持分类拖拽排序
- [ ] 修复移动端响应式布局问题

## 技术方案

- 使用 CSS Grid 优化布局
- 引入拖拽库实现排序
- 添加防抖搜索功能

---
*此 Issue 由 AI-Harness 自动化测试创建*
*测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*""",
        "labels": ["enhancement", "frontend"],
    }

    # Create issue via API
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    print(f"Creating issue in {repo_owner}/{repo_name}...")
    print(f"Title: {issue_data['title']}")

    response = requests.post(url, headers=headers, json=issue_data)

    if response.status_code == 201:
        issue = response.json()
        print(f"\n✓ Issue created successfully!")
        print(f"  Number: #{issue['number']}")
        print(f"  URL: {issue['html_url']}")
        return issue
    else:
        print(f"\n✗ Failed to create issue")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        return None


def close_github_issue(issue_number: int):
    """Close a test issue."""
    token = os.environ.get("GITHUB_TOKEN")
    repo_owner = "ninesun666"
    repo_name = "ninesun-blog"

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{issue_number}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.patch(url, headers=headers, json={"state": "closed"})

    if response.status_code == 200:
        print(f"✓ Issue #{issue_number} closed")
    else:
        print(f"✗ Failed to close issue: {response.status_code}")


if __name__ == "__main__":
    # Load .env file from parent directory
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value

    issue = create_github_issue()
    if issue:
        print(f"\nIssue Number: {issue['number']}")
        print("\nTo close this issue, run:")
        print(f"  python create_test_issue.py --close {issue['number']}")
