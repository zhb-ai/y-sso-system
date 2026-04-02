# 分析 CSS 类使用情况
$cssFiles = Get-ChildItem -Path "src/styles" -Filter "*.css" -Recurse
$vueFiles = Get-ChildItem -Path "src" -Filter "*.vue" -Recurse
$jsFiles = Get-ChildItem -Path "src" -Filter "*.js" -Recurse

# 收集所有 CSS 类定义
$cssClasses = @{}
foreach ($file in $cssFiles) {
    $content = Get-Content $file.FullName -Raw
    # 匹配类名定义
    $matches = [regex]::Matches($content, '\.([a-zA-Z_-][a-zA-Z0-9_-]*)\s*[{:,]')
    foreach ($match in $matches) {
        $className = $match.Groups[1].Value
        if (-not $cssClasses.ContainsKey($className)) {
            $cssClasses[$className] = @{
                File = $file.FullName
                Count = 0
            }
        }
    }
}

# 在 Vue 文件中搜索类使用
$allSourceFiles = $vueFiles + $jsFiles
foreach ($file in $allSourceFiles) {
    $content = Get-Content $file.FullName -Raw
    foreach ($className in $cssClasses.Keys) {
        # 匹配 class="..." 或 class='...' 中的类名
        $pattern = 'class=["\''][^"\'']*\b' + [regex]::Escape($className) + '\b[^"\'']*["\'']'
        $matches = [regex]::Matches($content, $pattern)
        $cssClasses[$className].Count += $matches.Count
        
        # 匹配 :class="..." 中的类名
        $pattern2 = ':class=["\''][^"\'']*\b' + [regex]::Escape($className) + '\b[^"\'']*["\'']'
        $matches2 = [regex]::Matches($content, $pattern2)
        $cssClasses[$className].Count += $matches2.Count
    }
}

# 输出未使用的类
Write-Host "=== 未使用的 CSS 类 ===" -ForegroundColor Red
$unusedClasses = $cssClasses.GetEnumerator() | Where-Object { $_.Value.Count -eq 0 } | Sort-Object Key
foreach ($item in $unusedClasses) {
    $relativePath = $item.Value.File.Replace($PWD.Path + '\', '')
    Write-Host "$($item.Key) - $relativePath" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== 统计 ===" -ForegroundColor Green
Write-Host "总 CSS 类数: $($cssClasses.Count)"
Write-Host "未使用类数: $($unusedClasses.Count)"
Write-Host "使用类数: $($cssClasses.Count - $unusedClasses.Count)"
