"""
Prompt templates for issue analysis.

This module contains prompt templates used by the analyzer
to interact with iFlow CLI for intelligent issue analysis.
"""

# Main issue analysis prompt
ISSUE_ANALYSIS_PROMPT = """You are an expert software architect analyzing a GitHub issue to break it down into actionable implementation tasks.

## Issue Details

**Issue Number:** #{issue_number}
**Title:** {issue_title}
**Type:** {issue_type}
**Priority:** {issue_priority}
**Labels:** {labels}

## Issue Body

{issue_body}

## Acceptance Criteria

{acceptance_criteria}

## Repository Context

{repo_context}

---

## Your Task

Analyze this issue and provide a detailed breakdown of implementation tasks.

## Output Format

Respond with a JSON object in the following format:

```json
{{
  "summary": "Brief summary of what needs to be implemented",
  "overall_approach": "High-level approach to solve this issue",
  "potential_risks": [
    "Risk 1",
    "Risk 2"
  ],
  "tasks": [
    {{
      "id": "T001",
      "title": "Task title",
      "description": "Detailed description of what needs to be done",
      "priority": "high|medium|low",
      "dependencies": [],
      "files_to_modify": ["path/to/file.py"],
      "estimated_complexity": "high|medium|low"
    }}
  ]
}}
```

## Guidelines

1. Break down the issue into small, atomic tasks that can be implemented independently
2. Each task should be completable in a single coding session
3. Order tasks by dependency (tasks with no dependencies first)
4. Include specific file paths when possible
5. Consider edge cases and error handling
6. For bug fixes, include a task to add tests that reproduce the bug
7. For features, include a task to add unit tests
8. Be realistic about complexity estimates

Provide your analysis now.
"""

# Prompt for requirement splitting
REQUIREMENT_SPLIT_PROMPT = """You are analyzing a software requirement to break it down into smaller, implementable tasks.

## Requirement

{requirement}

## Context

{context}

---

## Your Task

Break down this requirement into specific, actionable tasks that can be implemented by an AI coding assistant.

## Output Format

Respond with a JSON array of tasks:

```json
[
  {{
    "id": "T001",
    "title": "Task title",
    "description": "Detailed description",
    "priority": "high|medium|low",
    "dependencies": [],
    "files_to_modify": [],
    "estimated_complexity": "high|medium|low"
  }}
]
```

## Guidelines

1. Each task should be atomic and self-contained
2. Tasks should be ordered by dependency
3. Include specific file paths when known
4. Estimate complexity based on the scope of changes required
"""

# Prompt for task generation from code analysis
TASK_GENERATION_PROMPT = """You are analyzing existing code to generate implementation tasks for a new feature.

## Feature Description

{feature_description}

## Current Codebase Structure

{codebase_structure}

## Related Files

{related_files}

---

## Your Task

Analyze the current codebase and generate implementation tasks for adding this feature.

## Output Format

Respond with a JSON object:

```json
{{
  "analysis": "Brief analysis of how the feature fits into the codebase",
  "tasks": [
    {{
      "id": "T001",
      "title": "Task title",
      "description": "Detailed description",
      "priority": "high|medium|low",
      "dependencies": [],
      "files_to_modify": ["path/to/file.py"],
      "estimated_complexity": "high|medium|low"
    }}
  ],
  "new_files": [
    {{
      "path": "path/to/new_file.py",
      "purpose": "Purpose of this file"
    }}
  ],
  "modifications": [
    {{
      "file": "path/to/existing_file.py",
      "changes": "Description of changes needed"
    }}
  ]
}}
```

## Guidelines

1. Consider the existing architecture and patterns
2. Minimize changes to existing code when possible
3. Follow existing code style and conventions
4. Include tests in your task list
5. Consider backwards compatibility if applicable
"""

# Prompt for bug fix analysis
BUG_FIX_PROMPT = """You are analyzing a bug report to create a fix plan.

## Bug Report

**Issue Number:** #{issue_number}
**Title:** {issue_title}

## Bug Description

{bug_description}

## Steps to Reproduce

{steps_to_reproduce}

## Expected vs Actual Behavior

Expected: {expected_behavior}
Actual: {actual_behavior}

## Stack Trace / Error Logs

{stack_trace}

---

## Your Task

Analyze this bug and create a plan to fix it.

## Output Format

```json
{{
  "root_cause_analysis": "Analysis of what's causing the bug",
  "fix_approach": "High-level approach to fix the bug",
  "tasks": [
    {{
      "id": "T001",
      "title": "Write failing test",
      "description": "Create a test that reproduces the bug",
      "priority": "high",
      "dependencies": [],
      "files_to_modify": ["tests/test_file.py"],
      "estimated_complexity": "low"
    }},
    {{
      "id": "T002",
      "title": "Implement fix",
      "description": "Fix the root cause",
      "priority": "high",
      "dependencies": ["T001"],
      "files_to_modify": ["src/module.py"],
      "estimated_complexity": "medium"
    }},
    {{
      "id": "T003",
      "title": "Verify fix",
      "description": "Run tests and verify the bug is fixed",
      "priority": "high",
      "dependencies": ["T002"],
      "files_to_modify": [],
      "estimated_complexity": "low"
    }}
  ]
}}
```

## Guidelines

1. Always start with a test that reproduces the bug
2. Fix the root cause, not just the symptoms
3. Consider edge cases that might cause similar issues
4. Update documentation if the fix changes behavior
"""
