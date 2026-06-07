# Podman + Windows venv Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Podman container build and Windows venv install scripts for ibx-cli distribution.

**Architecture:** Two independent packaging targets — a Podman container (Linux, rootless) for Artifactory scanning and deployment, and a PowerShell venv script (Windows) for direct local use. Both share the same Python wheel from `dist/`.

**Tech Stack:** Python 3.12, Podman, Dockerfile/Containerfile, PowerShell, setuptools (wheel)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `Containerfile` | Create | Podman build definition — installs Python, copies wheel, sets entrypoint and non-root user |
| `scripts/build_and_push.sh` | Create | Linux shell script: build wheel, build image, push to Artifactory |
| `scripts/install_windows.ps1` | Create | PowerShell script: check Python, create venv, install wheel |
| `README.md` | Modify | Add "Container Deployment" and "Windows Installation" sections |
| `.dockerignore` | Create | Exclude `__pycache__`, `.git`, build artifacts from container context |

---

### Task 1: Create Containerfile

**Files:**
- Create: `Containerfile`
- Create: `.dockerignore`

- [ ] **Step 1: Write the Containerfile**

```dockerfile
# Containerfile — Podman build for ibx-cli
# Build:  podman build -t artifactory.company.com/ibx-cli:0.1.0 -f Containerfile .
# Run:    podman run --rm -v ~/.infoblox/config:/home/ibx/.infoblox/config:Z <image> dns zones

FROM python:3.12-slim

# Create non-root user
RUN groupadd -g 1000 ibx && \
    useradd -u 1000 -g ibx -m -s /bin/sh ibx && \
    mkdir -p /home/ibx/.infoblox && \
    chown -R ibx:ibx /home/ibx

WORKDIR /app

# Copy and install wheel
COPY dist/ibx_cli-*.whl /tmp/
RUN pip install --no-cache-dir /tmp/ibx_cli-*.whl && \
    rm /tmp/ibx_cli-*.whl

# Switch to non-root user
USER ibx

ENTRYPOINT ["ibx"]
CMD ["--help"]
```

- [ ] **Step 2: Create .dockerignore**

```text
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
build/
docs/
tests/
*.egg-info/
.claude/
```

- [ ] **Step 3: Commit**

```bash
git add Containerfile .dockerignore
git commit -m "feat: add Podman Containerfile and .dockerignore"
```

---

### Task 2: Create build_and_push.sh script

**Files:**
- Create: `scripts/build_and_push.sh`

- [ ] **Step 1: Write the build and push script**

```bash
#!/usr/bin/env bash
# build_and_push.sh — Build ibx-cli wheel, container image, and push to Artifactory
#
# Usage:
#   bash scripts/build_and_push.sh [IMAGE_TAG]
#
# Example:
#   bash scripts/build_and_push.sh 0.1.0
#   bash scripts/build_and_push.sh latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default tag
TAG="${1:-latest}"

# Artifactory registry — modify to match your company's registry
REGISTRY="artifactory.company.com"
IMAGE_NAME="${REGISTRY}/ibx-cli:${TAG}"

cd "$REPO_ROOT"

echo "=== Step 1: Building wheel ==="
python3 -m pip install --quiet build
python3 -m build --wheel
WHEEL_FILE=$(ls dist/ibx_cli-*.whl | tail -1)
echo "Built: ${WHEEL_FILE}"

echo "=== Step 2: Building container image ==="
podman build -t "${IMAGE_NAME}" -f Containerfile .
echo "Image: ${IMAGE_NAME}"

echo "=== Step 3: Pushing to Artifactory ==="
podman push "${IMAGE_NAME}"
echo "Pushed: ${IMAGE_NAME}"

echo ""
echo "=== Run commands ==="
echo "  podman run --rm -v ~/.infoblox/config:/home/ibx/.infoblox/config:Z ${IMAGE_NAME} dns zones"
echo "  podman run --rm -e IBX_HOST=... -e IBX_USERNAME=... -e IBX_PASSWORD=... ${IMAGE_NAME} dns a"
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x scripts/build_and_push.sh
git add scripts/build_and_push.sh
git commit -m "feat: add build_and_push.sh for Podman container automation"
```

---

### Task 3: Create install_windows.ps1 script

**Files:**
- Create: `scripts/install_windows.ps1`

- [ ] **Step 1: Write the PowerShell install script**

```powershell
# install_windows.ps1 — Install ibx-cli via venv on Windows
# Usage: .\scripts\install_windows.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== ibx-cli Windows Installer ===" -ForegroundColor Cyan

# Check Python 3.12+
Write-Host "`n[1/4] Checking Python version..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        Write-Host "ERROR: Python not found. Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Red
        exit 1
    }
    $pythonCmd = "py"
    $pythonVersion = & $pythonCmd -3 --version 2>&1
} else {
    $pythonCmd = "python"
    $pythonVersion = & $pythonCmd --version 2>&1
}

Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Extract version number
$versionMatch = [regex]::Match($pythonVersion, "Python (\d+)\.(\d+)")
if (-not $versionMatch.Success) {
    Write-Host "ERROR: Could not parse Python version." -ForegroundColor Red
    exit 1
}
$major = [int]$versionMatch.Groups[1].Value
$minor = [int]$versionMatch.Groups[2].Value
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 9)) {
    Write-Host "ERROR: Python 3.9+ required. Found $pythonVersion" -ForegroundColor Red
    exit 1
}

# Determine project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Check if wheel exists in dist/
$wheelPath = Get-ChildItem -Path (Join-Path $projectRoot "dist") -Filter "ibx_cli-*.whl" -ErrorAction SilentlyContinue | Select-Object -Last 1

# Create venv
$envPath = Join-Path $env:USERPROFILE "ibx-env"
Write-Host "`n[2/4] Creating virtual environment at $envPath..." -ForegroundColor Yellow
& $pythonCmd -m venv $envPath

# Activate venv
$activateScript = Join-Path $envPath "Scripts\Activate.ps1"
. $activateScript

# Install ibx-cli
if ($wheelPath) {
    Write-Host "`n[3/4] Installing ibx-cli from wheel: $($wheelPath.Name)..." -ForegroundColor Yellow
    pip install $wheelPath.FullName
} else {
    Write-Host "`n[3/4] No wheel found, installing from source..." -ForegroundColor Yellow
    pip install -e $projectRoot
}

# Verify installation
Write-Host "`n[4/4] Verifying installation..." -ForegroundColor Yellow
$ibxVersion = ibx --version 2>&1
Write-Host "Installed: $ibxVersion" -ForegroundColor Green

# Config directory
$configDir = Join-Path $env:USERPROFILE ".infoblox"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir | Out-Null
    Write-Host "`nConfig directory created: $configDir" -ForegroundColor Yellow
    Write-Host "Create your config file at: $configDir\config" -ForegroundColor Yellow
}

Write-Host "`n=== Installation Complete ===" -ForegroundColor Green
Write-Host "Activate venv before using: . $activateScript" -ForegroundColor Cyan
Write-Host "Then run: ibx --help" -ForegroundColor Cyan
```

- [ ] **Step 2: Commit**

```bash
git add scripts/install_windows.ps1
git commit -m "feat: add install_windows.ps1 for Windows venv installation"
```

---

### Task 4: Update README with deployment sections

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add Container and Windows sections to README**

Insert the following sections before `## 支持的 WAPI 版本` in README.md:

```markdown
---

## 容器部署 (Linux / Podman)

无需 root 权限，通过 Podman rootless 模式运行。

### 构建和推送

```bash
# 使用自动构建脚本 (自动构建 wheel + 镜像 + 推送到 Artifactory)
bash scripts/build_and_push.sh 0.1.0

# 或者手动分步执行
python3 -m build --wheel
podman build -t artifactory.company.com/ibx-cli:0.1.0 -f Containerfile .
podman push artifactory.company.com/ibx-cli:0.1.0
```

### 使用容器

```bash
# 通过配置文件 (推荐)
podman run --rm -v ~/.infoblox/config:/home/ibx/.infoblox/config:Z \
  artifactory.company.com/ibx-cli:0.1.0 dns zones

# 通过环境变量 (快速测试)
podman run --rm \
  -e IBX_HOST=10.0.0.2 -e IBX_USERNAME=admin -e IBX_PASSWORD=secret \
  artifactory.company.com/ibx-cli:0.1.0 dns a

# 调试模式 (进入容器 shell)
podman run --rm -it --entrypoint /bin/sh artifactory.company.com/ibx-cli:0.1.0
```

---

## Windows 安装

通过 PowerShell 脚本在 Windows 上创建虚拟环境并安装。

### 前置条件

- Python 3.9+ 已安装 (https://www.python.org/downloads/)

### 安装步骤

1. 克隆仓库或下载源码

2. 运行安装脚本：

```powershell
.\scripts\install_windows.ps1
```

3. 激活虚拟环境：

```powershell
. $HOME\ibx-env\Scripts\Activate.ps1
```

4. 验证安装：

```powershell
ibx --version
```

配置文件位于 `%USERPROFILE%\.infoblox\config`，格式与 Linux 相同。
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add container deployment and Windows installation sections"
```

---

### Task 5: Regenerate install script and push all

- [ ] **Step 1: Regenerate install_ibxcli.sh and push**

```bash
python3 dist/gen_installer.py
git add dist/install_ibxcli.sh
git commit -m "chore: regenerate install script for packaging updates"
git push
```
