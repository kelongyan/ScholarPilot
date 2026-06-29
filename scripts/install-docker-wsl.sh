#!/usr/bin/env bash
#
# Kairos — Docker Engine 安装脚本（WSL Ubuntu-22.04 内执行）
#
# 用途：在 WSL Ubuntu-22.04 发行版内安装 Docker Engine + docker compose 插件，
#       并配置为 systemd 自启。WSL 数据已在 D:\WSL\Ubuntu\ext4.vhdx，
#       因此 Docker 数据天然存储在 D 盘，无需额外迁移。
#
# 执行方式（在 Windows 终端里）：
#   wsl -d Ubuntu-22.04 -- bash -c 'curl -fsSL https://raw.githubusercontent.com/.../install-docker-wsl.sh | bash'
#   或者把本文件复制进 WSL 后执行：
#   wsl -d Ubuntu-22.04 -- bash /mnt/d/Kairos/scripts/install-docker-wsl.sh
#
# 注意：脚本需要 sudo 权限，执行时会提示输入密码。
#
set -euo pipefail

echo "=========================================="
echo " Kairos: Docker Engine 安装 (WSL)"
echo "=========================================="

# 0. 确认在 WSL 内
if [ ! -f /proc/sys/fs/binfmt_misc/WSLInterop ] && ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "错误：此脚本必须在 WSL 内执行。" >&2
  exit 1
fi
echo "[0] 运行环境: $(uname -a)"

# 1. 清理 Docker Desktop 残留的死链接
echo "[1] 清理 Docker Desktop 残留死链接..."
for link in /usr/bin/docker /usr/bin/hub-tool; do
  if [ -L "$link" ] && [ ! -e "$link" ]; then
    sudo rm -f "$link"
    echo "    已删除死链接: $link"
  fi
done

# 2. 卸载旧版本（避免冲突）
echo "[2] 卸载可能的旧版本..."
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# 3. 安装依赖
echo "[3] 安装 apt 依赖..."
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# 4. 添加 Docker 官方 GPG key 和 apt 源
echo "[4] 添加 Docker 官方 apt 源..."
sudo install -m 0755 -d /etc/apt/keyrings
if [ ! -f /etc/apt/keyrings/docker.gpg ]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 5. 安装 Docker Engine + compose 插件
echo "[5] 安装 docker-ce..."
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 6. 让当前用户免 sudo 使用 docker
echo "[6] 将当前用户加入 docker 组..."
sudo usermod -aG docker "$USER"
echo "    已将 $USER 加入 docker 组（需重新进入 WSL 生效）"

# 7. 配置 Docker 数据目录（确认默认 /var/lib/docker，已在 D 盘 vhdx 内）
echo "[7] Docker 数据目录配置..."
echo "    Docker 数据将存储在 /var/lib/docker（位于 D:\\WSL\\Ubuntu\\ext4.vhdx 内）"
echo "    无需额外迁移 —— WSL 虚拟磁盘已在 D 盘。"

# 8. 启动 docker 服务（systemd）
echo "[8] 启动 docker 服务..."
sudo systemctl enable docker
sudo systemctl start docker || sudo service docker start

# 9. 验证
echo "[9] 验证安装..."
sudo docker version 2>&1 | head -5
sudo docker compose version 2>&1

echo ""
echo "=========================================="
echo " 安装完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "  1. 退出并重新进入 WSL（让 docker 组生效）："
echo "     exit  (在 WSL 内)"
echo "     wsl --shutdown  (在 Windows 终端)"
echo "     wsl -d Ubuntu-22.04"
echo "  2. 验证免 sudo："
echo "     docker ps"
echo "  3. 启动 Kairos 基础设施："
echo "     cd /mnt/d/Kairos"
echo "     docker compose up -d"
echo "     docker compose ps"
echo ""
echo "  注意：docker compose 命令需在 WSL 内执行（数据在 D 盘）。"
