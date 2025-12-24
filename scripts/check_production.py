#!/usr/bin/env python3
"""
OmniChatX Production Readiness Check
Verifies all production configuration files are in place
"""
import os
import sys
from pathlib import Path
from typing import Tuple

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
CHECK = "✓"
CROSS = "✗"
WARN = "⚠"


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{BLUE}{'='*60}")
    print(f" {text}")
    print(f"{'='*60}{RESET}\n")


def print_result(name: str, exists: bool, required: bool = True):
    """Print check result."""
    if exists:
        print(f"  {GREEN}{CHECK}{RESET} {name}")
    elif required:
        print(f"  {RED}{CROSS}{RESET} {name} (MISSING)")
    else:
        print(f"  {YELLOW}{WARN}{RESET} {name} (optional, missing)")


def check_files() -> Tuple[int, int, int]:
    """Check if all required files exist."""
    base = Path(__file__).parent.parent

    # Required files for production
    required_files = [
        ("Dockerfile.production", True),
        ("docker-compose.production.yml", True),
        (".env.production.example", True),
        ("app/core/config.py", True),
        ("app/core/middleware.py", True),
        ("app/core/health.py", True),
        ("app/core/logging.py", True),
        ("deploy/nginx/nginx.conf", True),
        ("deploy/prometheus/prometheus.yml", True),
        ("deploy/grafana/provisioning/datasources/datasource.yml", True),
        ("scripts/deploy.sh", True),
        (".github/workflows/ci-cd.yml", True),
        ("tests/test_production.py", True),
        ("pytest.ini", True),
        (".coveragerc", True),
        ("docs/PRODUCTION_DEPLOYMENT.md", True),
        # Optional but recommended
        ("requirements.txt", True),
        ("requirements-optional.txt", False),
        ("setup.cfg", False),
        ("pyproject.toml", True),
    ]

    print_header("Production Files Check")

    passed = 0
    failed = 0
    warnings = 0

    for file_path, required in required_files:
        full_path = base / file_path
        exists = full_path.exists()
        print_result(file_path, exists, required)

        if exists:
            passed += 1
        elif required:
            failed += 1
        else:
            warnings += 1

    return passed, failed, warnings


def check_environment_variables():
    """Check for important environment variables."""
    print_header("Environment Variables Check")

    env_vars = [
        ("APP_ENV", False),
        ("SECRET_KEY", True),
        ("AUTH_TOKEN", True),
        ("OPENAI_API_KEY", True),
        ("DATABASE_URL", False),
        ("REDIS_URL", False),
        ("CORS_ORIGINS", False),
        ("LOG_LEVEL", False),
        ("DEBUG", False),
    ]

    for var, sensitive in env_vars:
        value = os.environ.get(var)
        if value:
            display = "***" if sensitive else value[:20] + "..." if len(value) > 20 else value
            print(f"  {GREEN}{CHECK}{RESET} {var} = {display}")
        else:
            print(f"  {YELLOW}{WARN}{RESET} {var} (not set)")


def check_directories():
    """Check if required directories exist."""
    print_header("Directory Structure Check")

    base = Path(__file__).parent.parent

    required_dirs = [
        "app/core",
        "deploy/nginx",
        "deploy/prometheus",
        "deploy/grafana/provisioning/datasources",
        "scripts",
        ".github/workflows",
        "tests",
        "docs",
        "logs",
        "data",
    ]

    for dir_path in required_dirs:
        full_path = base / dir_path
        exists = full_path.exists() and full_path.is_dir()
        print_result(dir_path, exists)


def check_docker():
    """Check Docker availability."""
    print_header("Docker Check")

    import subprocess

    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  {GREEN}{CHECK}{RESET} Docker: {result.stdout.strip()}")
        else:
            print(f"  {RED}{CROSS}{RESET} Docker not working properly")
    except FileNotFoundError:
        print(f"  {RED}{CROSS}{RESET} Docker not installed")

    try:
        result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  {GREEN}{CHECK}{RESET} Docker Compose: {result.stdout.strip()}")
        else:
            # Try docker compose (v2)
            result = subprocess.run(
                ["docker", "compose", "version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  {GREEN}{CHECK}{RESET} Docker Compose (v2): {result.stdout.strip()}")
            else:
                print(f"  {RED}{CROSS}{RESET} Docker Compose not working")
    except FileNotFoundError:
        print(f"  {YELLOW}{WARN}{RESET} Docker Compose command not found (try 'docker compose')")


def check_python_deps():
    """Check Python dependencies."""
    print_header("Python Dependencies Check")

    critical_deps = [
        "fastapi",
        "uvicorn",
        "streamlit",
        "redis",
        "prometheus_client",
        "pydantic",
        "requests",
        "httpx",
        "pytest",
    ]

    for dep in critical_deps:
        try:
            __import__(dep.replace("-", "_"))
            print(f"  {GREEN}{CHECK}{RESET} {dep}")
        except ImportError:
            print(f"  {YELLOW}{WARN}{RESET} {dep} (not installed)")


def generate_summary(passed: int, failed: int, warnings: int):
    """Generate summary report."""
    print_header("Summary")

    total = passed + failed + warnings

    print(f"  Total checks:  {total}")
    print(f"  {GREEN}Passed:        {passed}{RESET}")
    print(f"  {RED}Failed:        {failed}{RESET}")
    print(f"  {YELLOW}Warnings:      {warnings}{RESET}")

    if failed == 0:
        print(f"\n  {GREEN}🎉 Production readiness check PASSED!{RESET}")
        print("  Your project is ready for production deployment.")
    else:
        print(f"\n  {RED}❌ Production readiness check FAILED!{RESET}")
        print(f"  Please address the {failed} missing required file(s).")

    print(f"\n  {BLUE}Next Steps:{RESET}")
    print("  1. Configure .env with your values (copy from .env.production.example)")
    print("  2. Add SSL certificates to deploy/nginx/ssl/")
    print("  3. Run: ./scripts/deploy.sh deploy")
    print("  4. Access the app at https://your-domain.com")

    return failed == 0


def main():
    """Run all checks."""
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════════╗")
    print("║       OmniChatX Production Readiness Checker             ║")
    print(f"╚══════════════════════════════════════════════════════════╝{RESET}")

    passed, failed, warnings = check_files()
    check_directories()
    check_docker()
    check_python_deps()
    check_environment_variables()

    success = generate_summary(passed, failed, warnings)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
