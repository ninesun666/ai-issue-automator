"""
End-to-end automation test script.

This script simulates the complete workflow:
1. Receive issue webhook
2. Parse and analyze issue
3. Create branch
4. Generate feature list
5. Simulate code changes
6. Create PR (mock)

No GitHub token required - all operations are simulated locally.
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Colors:
    """ANSI colors for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_step(step_num: int, title: str):
    """Print a step header."""
    print(f"\n{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}[Step {step_num}] {title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")


def print_success(msg: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")


def print_info(msg: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}→ {msg}{Colors.ENDC}")


def simulate_issue_webhook():
    """Simulate receiving an issue webhook."""
    print_step(1, "Receive Issue Webhook")
    
    webhook_data = {
        "action": "opened",
        "issue": {
            "number": 101,
            "title": "前端分类界面优化",
            "body": """## 问题描述

当前的分类界面存在以下问题：
- 分类列表展示不够直观
- 缺少分类图标
- 响应式布局存在问题

## 期望效果

- [ ] 优化分类卡片样式，增加图标展示
- [ ] 支持分类拖拽排序
- [ ] 修复移动端响应式布局问题
- [ ] 添加分类搜索功能

## 技术方案

- 使用 CSS Grid 优化布局
- 引入 react-beautiful-dnd 实现拖拽
- 添加防抖搜索功能
""",
            "html_url": "https://github.com/ninesun666/ninesun-blog/issues/101",
            "state": "open",
            "labels": [
                {"name": "enhancement"},
                {"name": "frontend"},
                {"name": "priority:high"}
            ],
        },
        "repository": {
            "name": "ninesun-blog",
            "full_name": "ninesun666/ninesun-blog",
        },
        "sender": {
            "login": "ninesun666",
        },
    }
    
    print_info(f"Repository: {webhook_data['repository']['full_name']}")
    print_info(f"Issue #{webhook_data['issue']['number']}: {webhook_data['issue']['title']}")
    print_info(f"Labels: {[l['name'] for l in webhook_data['issue']['labels']]}")
    print_success("Webhook received and parsed")
    
    return webhook_data


def analyze_issue(webhook_data: dict):
    """Analyze issue and generate task breakdown."""
    print_step(2, "Analyze Issue & Generate Tasks")
    
    issue = webhook_data["issue"]
    
    # Simulated AI analysis result
    analysis_result = {
        "summary": "优化前端分类界面，包括样式优化、拖拽排序、响应式布局和搜索功能",
        "overall_approach": """
1. 首先重构分类卡片组件，优化视觉样式
2. 实现拖拽排序功能
3. 修复响应式布局问题
4. 最后添加搜索功能
""",
        "potential_risks": [
            "拖拽功能可能与现有滚动行为冲突",
            "移动端触摸事件需要特殊处理",
            "搜索性能需要考虑大数据量场景"
        ],
        "tasks": [
            {
                "id": "T001",
                "title": "优化分类卡片组件样式",
                "description": "重构 CategoryCard 组件，添加图标支持，优化视觉效果",
                "priority": "high",
                "dependencies": [],
                "files_to_modify": [
                    "src/components/CategoryCard.tsx",
                    "src/components/CategoryCard.module.css"
                ],
                "estimated_complexity": "medium",
                "passes": False
            },
            {
                "id": "T002",
                "title": "实现分类拖拽排序功能",
                "description": "使用 react-beautiful-dnd 实现分类拖拽排序，支持持久化排序结果",
                "priority": "high",
                "dependencies": ["T001"],
                "files_to_modify": [
                    "src/components/CategoryList.tsx",
                    "src/hooks/useDragSort.ts",
                    "src/api/category.ts"
                ],
                "estimated_complexity": "high",
                "passes": False
            },
            {
                "id": "T003",
                "title": "修复响应式布局问题",
                "description": "使用 CSS Grid 重构布局，修复移动端显示问题",
                "priority": "medium",
                "dependencies": ["T001"],
                "files_to_modify": [
                    "src/components/CategoryList.module.css",
                    "src/styles/responsive.css"
                ],
                "estimated_complexity": "low",
                "passes": False
            },
            {
                "id": "T004",
                "title": "添加分类搜索功能",
                "description": "实现分类搜索功能，支持实时搜索和防抖优化",
                "priority": "medium",
                "dependencies": ["T003"],
                "files_to_modify": [
                    "src/components/CategorySearch.tsx",
                    "src/hooks/useDebounce.ts"
                ],
                "estimated_complexity": "medium",
                "passes": False
            },
            {
                "id": "T005",
                "title": "添加单元测试",
                "description": "为新功能添加单元测试和集成测试",
                "priority": "low",
                "dependencies": ["T001", "T002", "T003", "T004"],
                "files_to_modify": [
                    "src/__tests__/CategoryCard.test.tsx",
                    "src/__tests__/CategoryList.test.tsx"
                ],
                "estimated_complexity": "medium",
                "passes": False
            }
        ]
    }
    
    print_info(f"Summary: {analysis_result['summary']}")
    print_info(f"Tasks generated: {len(analysis_result['tasks'])}")
    print()
    
    for task in analysis_result["tasks"]:
        deps = f" (depends: {', '.join(task['dependencies'])})" if task['dependencies'] else ""
        print(f"  [{task['id']}] {task['title']}{deps}")
    
    print_success("Issue analysis completed")
    
    return analysis_result


def create_branch(webhook_data: dict) -> str:
    """Simulate creating a feature branch."""
    print_step(3, "Create Feature Branch")
    
    issue = webhook_data["issue"]
    labels = [l["name"] for l in issue["labels"]]
    
    # Determine branch type from labels
    if "bug" in labels or "fix" in labels:
        branch_type = "fix"
    else:
        branch_type = "feat"
    
    # Generate branch name
    import re
    title_slug = re.sub(r"[^a-zA-Z0-9\s-]", "", issue["title"])
    title_slug = re.sub(r"\s+", "-", title_slug).lower()[:30]
    branch_name = f"{branch_type}/issue-{issue['number']}-{title_slug}"
    
    print_info(f"Branch type: {branch_type} (based on labels)")
    print_info(f"Branch name: {branch_name}")
    print_success("Branch created from main")
    
    return branch_name


def generate_feature_list(analysis_result: dict, work_dir: Path) -> Path:
    """Generate feature_list.json file."""
    print_step(4, "Generate Feature List")
    
    # Create .agent-harness directory
    harness_dir = work_dir / ".agent-harness"
    harness_dir.mkdir(parents=True, exist_ok=True)
    
    # Create feature list
    feature_list = {
        "project": {
            "source_issue": analysis_result.get("source_issue", 101),
            "created_at": datetime.now().isoformat(),
        },
        "features": analysis_result["tasks"],
        "overall_approach": analysis_result["overall_approach"],
        "potential_risks": analysis_result["potential_risks"],
    }
    
    feature_list_path = harness_dir / "feature_list.json"
    with open(feature_list_path, "w", encoding="utf-8") as f:
        json.dump(feature_list, f, indent=2, ensure_ascii=False)
    
    print_info(f"Created: {feature_list_path}")
    print_success(f"Feature list generated with {len(analysis_result['tasks'])} tasks")
    
    return feature_list_path


def simulate_code_changes(work_dir: Path, analysis_result: dict):
    """Simulate AI harness executing code changes."""
    print_step(5, "Execute AI Harness (Simulated)")
    
    # Create simulated source files
    src_dir = work_dir / "src" / "components"
    src_dir.mkdir(parents=True, exist_ok=True)
    
    # Create CategoryCard component
    category_card = src_dir / "CategoryCard.tsx"
    category_card.write_text("""import React from 'react';
import styles from './CategoryCard.module.css';

interface CategoryCardProps {
  id: string;
  name: string;
  icon?: string;
  count: number;
  onDragStart?: () => void;
  onDragEnd?: () => void;
}

export const CategoryCard: React.FC<CategoryCardProps> = ({
  id,
  name,
  icon,
  count,
  onDragStart,
  onDragEnd,
}) => {
  return (
    <div 
      className={styles.card}
      draggable
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      data-testid={`category-card-${id}`}
    >
      {icon && <span className={styles.icon}>{icon}</span>}
      <h3 className={styles.name}>{name}</h3>
      <span className={styles.count}>{count} 篇文章</span>
    </div>
  );
};
""", encoding="utf-8")
    
    # Create CSS module
    css_module = src_dir / "CategoryCard.module.css"
    css_module.write_text(""".card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1.5rem;
  border-radius: 12px;
  background: var(--card-bg, #fff);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: grab;
}

.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.card:active {
  cursor: grabbing;
}

.icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary, #333);
  margin: 0 0 0.25rem 0;
}

.count {
  font-size: 0.875rem;
  color: var(--text-secondary, #666);
}

/* Responsive */
@media (max-width: 768px) {
  .card {
    padding: 1rem;
  }
  
  .icon {
    font-size: 1.5rem;
  }
}
""", encoding="utf-8")
    
    # Create CategoryList component
    category_list = src_dir / "CategoryList.tsx"
    category_list.write_text("""import React, { useState, useMemo } from 'react';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import { CategoryCard } from './CategoryCard';
import { CategorySearch } from './CategorySearch';
import { useDebounce } from '../hooks/useDebounce';
import styles from './CategoryList.module.css';

interface Category {
  id: string;
  name: string;
  icon?: string;
  count: number;
}

interface CategoryListProps {
  categories: Category[];
  onReorder?: (categories: Category[]) => void;
}

export const CategoryList: React.FC<CategoryListProps> = ({
  categories: initialCategories,
  onReorder,
}) => {
  const [categories, setCategories] = useState(initialCategories);
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearch = useDebounce(searchTerm, 300);

  const filteredCategories = useMemo(() => {
    if (!debouncedSearch) return categories;
    return categories.filter(c => 
      c.name.toLowerCase().includes(debouncedSearch.toLowerCase())
    );
  }, [categories, debouncedSearch]);

  const handleDragEnd = (result: any) => {
    if (!result.destination) return;
    
    const items = Array.from(categories);
    const [reorderedItem] = items.splice(result.source.index, 1);
    items.splice(result.destination.index, 0, reorderedItem);
    
    setCategories(items);
    onReorder?.(items);
  };

  return (
    <div className={styles.container}>
      <CategorySearch 
        value={searchTerm}
        onChange={setSearchTerm}
      />
      
      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="categories">
          {(provided) => (
            <div 
              className={styles.grid}
              {...provided.droppableProps}
              ref={provided.innerRef}
            >
              {filteredCategories.map((category, index) => (
                <Draggable 
                  key={category.id} 
                  draggableId={category.id} 
                  index={index}
                >
                  {(provided) => (
                    <div
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      {...provided.dragHandleProps}
                    >
                      <CategoryCard {...category} />
                    </div>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </div>
          )}
        </Droppable>
      </DragDropContext>
    </div>
  );
};
""", encoding="utf-8")
    
    # Update feature list to mark tasks as complete
    feature_list_path = work_dir / ".agent-harness" / "feature_list.json"
    with open(feature_list_path, "r", encoding="utf-8") as f:
        feature_list = json.load(f)
    
    for task in feature_list["features"]:
        task["passes"] = True
    
    with open(feature_list_path, "w", encoding="utf-8") as f:
        json.dump(feature_list, f, indent=2, ensure_ascii=False)
    
    # Show created files
    created_files = [
        category_card,
        css_module,
        category_list,
    ]
    
    print_info(f"Working directory: {work_dir}")
    print_info("Files created/modified:")
    for f in created_files:
        print(f"    {f.relative_to(work_dir)}")
    
    print_success("AI Harness execution completed")
    print_success("All tasks marked as passed")


def create_pull_request(webhook_data: dict, branch_name: str, analysis_result: dict):
    """Simulate creating a pull request."""
    print_step(6, "Create Pull Request")
    
    issue = webhook_data["issue"]
    
    pr_info = {
        "number": 42,
        "title": f"feat: {issue['title']} (#{issue['number']})",
        "head": branch_name,
        "base": "main",
        "body": f"""## Summary

Closes #{issue['number']}

**Issue:** {issue['title']}

## Changes

{analysis_result['overall_approach']}

## Tasks Completed

""" + "\n".join([f"- [x] {t['title']}" for t in analysis_result['tasks']]) + """

## Testing

- [x] Unit tests added/updated
- [x] Manual testing completed

## Checklist

- [x] Code follows project conventions
- [x] No breaking changes
- [x] Documentation updated if needed

---

*This PR was automatically generated by AI Harness.*
""",
        "html_url": f"https://github.com/ninesun666/ninesun-blog/pull/42",
    }
    
    print_info(f"PR Title: {pr_info['title']}")
    print_info(f"Branch: {pr_info['head']} -> {pr_info['base']}")
    print_info(f"URL: {pr_info['html_url']}")
    print_success("Pull request created successfully")


def notify_completion(webhook_data: dict, pr_info: dict):
    """Simulate notification."""
    print_step(7, "Notify Completion")
    
    issue = webhook_data["issue"]
    
    print_info(f"Posted comment on issue #{issue['number']}")
    print_info("Notification content:")
    print()
    print("─" * 50)
    print("✅ AI Automation Completed")
    print()
    print(f"Pull request created: {pr_info['html_url']}")
    print()
    print("Please review and merge when ready.")
    print("─" * 50)
    
    print_success("Notification sent")


def run_e2e_test():
    """Run the complete end-to-end test."""
    print()
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  AI Harness - End-to-End Automation Test{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print()
    print(f"Scenario: 前端分类界面优化")
    print(f"Repository: ninesun666/ninesun-blog")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Receive webhook
    webhook_data = simulate_issue_webhook()
    
    # Step 2: Analyze issue
    analysis_result = analyze_issue(webhook_data)
    
    # Step 3: Create branch
    branch_name = create_branch(webhook_data)
    
    # Step 4: Generate feature list
    work_dir = Path(tempfile.mkdtemp(prefix="ai-harness-test-"))
    try:
        feature_list_path = generate_feature_list(analysis_result, work_dir)
        
        # Step 5: Execute AI harness
        simulate_code_changes(work_dir, analysis_result)
        
        # Step 6: Create PR
        pr_info = {
            "number": 42,
            "title": f"feat: {webhook_data['issue']['title']} (#{webhook_data['issue']['number']})",
            "html_url": f"https://github.com/ninesun666/ninesun-blog/pull/42",
        }
        create_pull_request(webhook_data, branch_name, analysis_result)
        
        # Step 7: Notify
        notify_completion(webhook_data, pr_info)
        
    finally:
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)
    
    # Summary
    print()
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.BOLD}  Test Summary{Colors.ENDC}")
    print(f"{Colors.HEADER}{'=' * 60}{Colors.ENDC}")
    print()
    print(f"  Issue:     #{webhook_data['issue']['number']} - {webhook_data['issue']['title']}")
    print(f"  Branch:    {branch_name}")
    print(f"  Tasks:     {len(analysis_result['tasks'])} completed")
    print(f"  PR:        #{pr_info['number']}")
    print()
    print(f"{Colors.OKGREEN}✓ End-to-end test completed successfully!{Colors.ENDC}")
    print()


if __name__ == "__main__":
    run_e2e_test()
