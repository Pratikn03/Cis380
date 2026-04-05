#!/usr/bin/env python3
"""
Sentifargo Production Readiness Check
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


def _split_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _is_explicit_list(value: str | None) -> bool:
    entries = _split_csv(value)
    return bool(entries) and all(entry != "*" for entry in entries)


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


def check_compose_configuration() -> Tuple[int, int, int]:
    """Validate production compose hardening rules."""
    base = Path(__file__).parent.parent
    compose_path = base / "docker-compose.production.yml"
    print_header("Compose Configuration Check")

    if not compose_path.exists():
        print_result("docker-compose.production.yml", False)
        return 0, 1, 0

    raw = compose_path.read_text(encoding="utf-8")
    checks = [
        ("API service present", "Sentifargo-api:"),
        ("Worker service present", "Sentifargo-worker:"),
        ("Postgres service present", "\n  postgres:\n"),
        ("Redis service present", "\n  redis:\n"),
        ("API requires SECRET_KEY", "SECRET_KEY=${SECRET_KEY:?"),
        ("API requires CORS_ORIGINS", "CORS_ORIGINS=${CORS_ORIGINS:?"),
        ("API requires ALLOWED_HOSTS", "ALLOWED_HOSTS=${ALLOWED_HOSTS:?"),
        ("API forces HTTPS", "FORCE_HTTPS=true"),
        ("API healthcheck uses readiness", "http://localhost:8000/health/ready"),
        ("API waits for worker health", "Sentifargo-worker:\n        condition: service_healthy"),
        ("Worker checks Celery ping", "celery.control.inspect(timeout=2)"),
    ]

    passed = failed = warnings = 0
    for name, marker in checks:
        exists = marker in raw
        print_result(name, exists)
        if exists:
            passed += 1
        else:
            failed += 1

    return passed, failed, warnings


def check_environment_variables():
    """Check for important environment variables."""
    print_header("Environment Variables Check")

    env_vars = [
        ("APP_ENV", False, lambda v: v == "production"),
        ("SECRET_KEY", True, lambda v: bool(v.strip())),
        ("DATABASE_URL", False, lambda v: not v.startswith("sqlite")),
        ("REDIS_URL", False, lambda v: bool(v.strip())),
        ("CORS_ORIGINS", False, _is_explicit_list),
        ("ALLOWED_HOSTS", False, _is_explicit_list),
        ("FORCE_HTTPS", False, lambda v: v.lower() == "true"),
        ("AUTH_TOKEN", True, lambda v: True),
        ("OPENAI_API_KEY", True, lambda v: True),
    ]

    passed = failed = warnings = 0
    for var, sensitive, validator in env_vars:
        value = os.environ.get(var)
        if value:
            display = "***" if sensitive else value[:20] + "..." if len(value) > 20 else value
            valid = validator(value)
            if valid:
                print(f"  {GREEN}{CHECK}{RESET} {var} = {display}")
                passed += 1
            else:
                print(f"  {RED}{CROSS}{RESET} {var} = {display} (invalid)")
                failed += 1
        else:
            if var in {"APP_ENV", "SECRET_KEY", "DATABASE_URL", "REDIS_URL", "CORS_ORIGINS", "ALLOWED_HOSTS", "FORCE_HTTPS"}:
                print(f"  {RED}{CROSS}{RESET} {var} (not set)")
                failed += 1
            else:
                print(f"  {YELLOW}{WARN}{RESET} {var} (not set)")
                warnings += 1

    return passed, failed, warnings


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
    print("║       Sentifargo Production Readiness Checker             ║")
    print(f"╚══════════════════════════════════════════════════════════╝{RESET}")

    passed, failed, warnings = check_files()
    config_passed, config_failed, config_warnings = check_compose_configuration()
    env_passed, env_failed, env_warnings = check_environment_variables()
    passed += config_passed + env_passed
    failed += config_failed + env_failed
    warnings += config_warnings + env_warnings
    check_directories()
    check_docker()
    check_python_deps()

    success = generate_summary(passed, failed, warnings)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
