@echo off
REM ScholarPilot - Ollama startup with D drive model storage and LAN binding.
REM OLLAMA_HOST=0.0.0.0 lets the WSL worker reach Ollama via the Windows gateway IP.
set OLLAMA_MODELS=D:\Ollama\models
set OLLAMA_HOST=0.0.0.0:11434
"C:\Users\admin\AppData\Local\Programs\Ollama\ollama.exe" serve
