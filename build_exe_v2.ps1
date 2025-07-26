# 护眼助手构建脚本 v2.0
# 改进的 PyInstaller 构建脚本

Write-Host "开始构建护眼助手..." -ForegroundColor Cyan

try {
    # 使用 PyInstaller 构建可执行文件
    pyinstaller --onefile -w --name eye --clean `
        --add-data "eye_rest_config.json;." `
        --hidden-import=win32gui `
        --hidden-import=win32con `
        --hidden-import=win32api `
        --hidden-import=win32com.client `
        --hidden-import=winsound `
        --distpath=dist `
        --workpath=build `
        .\src\main.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PyInstaller 构建成功！" -ForegroundColor Green
        
        # 清理构建文件
        Write-Host "清理临时文件..." -ForegroundColor Yellow
        Remove-Item "*.spec" -ErrorAction SilentlyContinue
        Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
        
        # 创建日志目录（如果需要）
        $logPath = ".\dist\logs"
        if (!(Test-Path $logPath)) {
            New-Item -ItemType Directory -Force -Path $logPath | Out-Null
            Write-Host "创建日志目录: $logPath" -ForegroundColor Blue
        }
        
        # 验证可执行文件是否存在
        $exePath = ".\dist\eye.exe"
        if (Test-Path $exePath) {
            $fileSize = (Get-Item $exePath).Length / 1MB
            Write-Host "✅ 构建完成！" -ForegroundColor Green
            Write-Host "📁 可执行文件位于: $exePath" -ForegroundColor Green
            Write-Host "📊 文件大小: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Green
            Write-Host ""
            Write-Host "💡 提示: 可以运行 .\dist\eye.exe 来测试应用程序" -ForegroundColor Cyan
        } else {
            Write-Host "❌ 错误: 可执行文件未找到！" -ForegroundColor Red
            exit 1
        }
        
    } else {
        Write-Host "❌ PyInstaller 构建失败！退出代码: $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
} catch {
    Write-Host "❌ 构建过程中发生错误: $_" -ForegroundColor Red
    exit 1
}

Write-Host "🎉 所有操作完成！" -ForegroundColor Green 