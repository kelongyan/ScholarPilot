# ScholarPilot — Ollama WSL 防火墙规则
#
# 用途：允许 WSL 子网访问 Windows 上 Ollama 的 11434 端口。
# 必须以管理员身份运行。
#
# 运行方式（以管理员身份打开 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File D:\ScholarPilot\scripts\add-firewall-rule.ps1

$ErrorActionPreference = "Stop"

# 移除旧规则（如果存在）
Get-NetFirewallRule -DisplayName "Ollama WSL Access" -ErrorAction SilentlyContinue | Remove-NetFirewallRule

# 添加入站规则：允许 WSL 子网 (172.16.0.0/12) 访问 11434 端口
New-NetFirewallRule `
    -DisplayName "Ollama WSL Access" `
    -Direction Inbound `
    -LocalPort 11434 `
    -Protocol TCP `
    -Action Allow `
    -RemoteAddress 172.16.0.0/12 `
    -Profile Private

Write-Host "防火墙规则已添加：允许 WSL (172.16.0.0/12) 访问 11434 端口" -ForegroundColor Green
Write-Host ""
Write-Host "验证："
Get-NetFirewallRule -DisplayName "Ollama WSL Access" | Format-Table DisplayName, Enabled, Direction, Action
