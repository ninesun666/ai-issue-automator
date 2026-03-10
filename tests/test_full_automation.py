"""
Complete automation test with real GitHub API.

This script simulates a full automation workflow:
1. Simulates receiving a webhook
2. Runs the actual pipeline (without pushing to GitHub)
3. Shows what would happen in production

No GitHub write permissions required - only reads repo info.
"""

import os
import json
import logging
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


def check_github_access():
    """Check if we can access the GitHub repo."""
    import requests
    
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN not set")
        return False, None
    
    # Check repo access
    url = "https://api.github.com/repos/ninesun666/ninesun-blog"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        repo = response.json()
        return True, repo
    else:
        return False, None


def simulate_full_automation():
    """Run the complete automation simulation."""
    print("=" * 60)
    print("  AI Harness - Full Automation Test")
    print("=" * 60)
    print()
    
    # Load environment
    load_env()
    
    # Check GitHub access
    print("[1/8] Checking GitHub access...")
    has_access, repo = check_github_access()
    
    if has_access:
        print(f"  ✓ Repository access confirmed")
        print(f"    Name: {repo['full_name']}")
        print(f"    Default branch: {repo['default_branch']}")
        print(f"    URL: {repo['html_url']}")
    else:
        print("  ✗ Cannot access repository")
        print("    Please check your GITHUB_TOKEN permissions")
        return
    
    print()
    
    # Simulate issue webhook
    print("[2/8] Simulating issue webhook...")
    issue_number = 999
    issue_title = "前端分类界面优化"
    issue_body = """## 问题描述

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
"""
    
    print(f"  Issue #{issue_number}: {issue_title}")
    print(f"  Labels: enhancement, frontend")
    print("  ✓ Webhook simulated")
    print()
    
    # Analyze issue
    print("[3/8] Analyzing issue requirements...")
    tasks = [
        {"id": "T001", "title": "优化分类卡片组件样式", "priority": "high"},
        {"id": "T002", "title": "实现分类拖拽排序功能", "priority": "high"},
        {"id": "T003", "title": "修复响应式布局问题", "priority": "medium"},
        {"id": "T004", "title": "添加分类搜索功能", "priority": "medium"},
    ]
    
    for task in tasks:
        print(f"  [{task['id']}] {task['title']} (priority: {task['priority']})")
    print("  ✓ Task breakdown generated")
    print()
    
    # Create branch name
    print("[4/8] Generating branch name...")
    branch_name = f"feat/issue-{issue_number}-frontend-category-optimize"
    print(f"  Branch: {branch_name}")
    print(f"  Base: {repo['default_branch']}")
    print("  ✓ Branch name generated")
    print()
    
    # Create feature list
    print("[5/8] Creating feature list...")
    work_dir = Path(tempfile.mkdtemp(prefix="ai-harness-"))
    harness_dir = work_dir / ".agent-harness"
    harness_dir.mkdir(parents=True, exist_ok=True)
    
    feature_list = {
        "project": {
            "source_issue": issue_number,
            "repository": repo["full_name"],
            "branch": branch_name,
            "created_at": datetime.now().isoformat(),
        },
        "features": [
            {
                "id": t["id"],
                "title": t["title"],
                "priority": t["priority"],
                "passes": False,
            }
            for t in tasks
        ],
    }
    
    feature_list_path = harness_dir / "feature_list.json"
    with open(feature_list_path, "w", encoding="utf-8") as f:
        json.dump(feature_list, f, indent=2, ensure_ascii=False)
    
    print(f"  Created: {feature_list_path}")
    print("  ✓ Feature list created")
    print()
    
    # Simulate code generation
    print("[6/8] Simulating code generation...")
    src_dir = work_dir / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # CategoryCard component
    (src_dir / "CategoryCard.tsx").write_text("""import React from 'react';
import styles from './CategoryCard.module.css';

interface CategoryCardProps {
  id: string;
  name: string;
  icon?: string;
  count: number;
}

export const CategoryCard: React.FC<CategoryCardProps> = ({
  id, name, icon, count
}) => {
  return (
    <div className={styles.card} data-testid={`category-${id}`}>
      {icon && <span className={styles.icon}>{icon}</span>}
      <h3 className={styles.name}>{name}</h3>
      <span className={styles.count}>{count} 篇文章</span>
    </div>
  );
};
""", encoding="utf-8")
    
    # CSS
    (src_dir / "CategoryCard.module.css").write_text(""".card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  border-radius: 12px;
  background: var(--card-bg, #fff);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.icon { font-size: 2rem; margin-bottom: 0.5rem; }
.name { font-size: 1rem; font-weight: 600; margin: 0; }
.count { font-size: 0.875rem; color: #666; }

@media (max-width: 768px) {
  .card { padding: 1rem; }
}
""", encoding="utf-8")
    
    # CategoryList component
    (src_dir / "CategoryList.tsx").write_text("""import React, { useState, useMemo } from 'react';
import { CategoryCard } from './CategoryCard';

interface Category {
  id: string;
  name: string;
  icon?: string;
  count: number;
}

export const CategoryList: React.FC<{ categories: Category[] }> = ({
  categories
}) => {
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search) return categories;
    return categories.filter(c => 
      c.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [categories, search]);

  return (
    <div className="category-list">
      <input
        type="search"
        placeholder="搜索分类..."
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <div className="category-grid">
        {filtered.map(cat => (
          <CategoryCard key={cat.id} {...cat} />
        ))}
      </div>
    </div>
  );
};
""", encoding="utf-8")
    
    created_files = list(src_dir.glob("*"))
    print(f"  Working directory: {work_dir}")
    print(f"  Created files:")
    for f in created_files:
        print(f"    - {f.relative_to(work_dir)}")
    print("  ✓ Code generated")
    print()
    
    # Update feature list
    for task in feature_list["features"]:
        task["passes"] = True
    with open(feature_list_path, "w", encoding="utf-8") as f:
        json.dump(feature_list, f, indent=2, ensure_ascii=False)
    print("  ✓ All tasks marked as complete")
    print()
    
    # Simulate PR creation
    print("[7/8] Preparing Pull Request...")
    pr_info = {
        "title": f"feat: {issue_title} (#{issue_number})",
        "head": branch_name,
        "base": repo["default_branch"],
        "body": f"""## Summary

Closes #{issue_number}

**Issue:** {issue_title}

## Changes

- 优化分类卡片组件样式
- 实现分类拖拽排序功能
- 修复响应式布局问题
- 添加分类搜索功能

## Tasks Completed

""" + "\n".join([f"- [x] {t['title']}" for t in tasks]) + """

---

*This PR was automatically generated by AI Harness.*
""",
    }
    
    print(f"  Title: {pr_info['title']}")
    print(f"  Branch: {pr_info['head']} -> {pr_info['base']}")
    print("  ✓ PR prepared (not pushed - dry run mode)")
    print()
    
    # Summary
    print("[8/8] Automation Summary")
    print("=" * 60)
    print(f"  Repository: {repo['full_name']}")
    print(f"  Issue: #{issue_number} - {issue_title}")
    print(f"  Branch: {branch_name}")
    print(f"  Tasks: {len(tasks)} completed")
    print(f"  Files: {len(created_files)} generated")
    print()
    print("  Generated files location:")
    print(f"    {work_dir}")
    print()
    print("=" * 60)
    print("  ✓ Full automation test completed!")
    print("=" * 60)
    
    # Cleanup option
    print()
    print(f"Working directory preserved at: {work_dir}")
    print("To clean up, delete the directory manually.")
    
    return work_dir


if __name__ == "__main__":
    simulate_full_automation()
