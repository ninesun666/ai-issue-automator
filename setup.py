from setuptools import setup, find_packages

setup(
    name="issue-automator",
    version="0.1.0",
    description="GitHub Issue Automation with AI-powered workflow",
    author="",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "Click>=8.0",
        "PyYAML>=6.0",
        "colorama>=0.4",
        # Automation dependencies
        "Flask>=2.0.0",
        "PyGithub>=1.58.0",
        "GitPython>=3.1.0",
    ],
    entry_points={"console_scripts": [
        "issue-automator=issue_automator.cli.__init__:main",
        "ia=issue_automator.cli.__init__:main",
    ]},
)
