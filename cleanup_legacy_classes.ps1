$root = Get-Location
$htmlFiles = @('index.html','activities.html','biography.html','form.html','member.html','researchs.html')
$cssFiles = @('index.css','activities.css','biography.css','form.css','member.css','researchs.css','site.css')
$legacyPattern = '(?<![A-Za-z0-9_-])(?:home|activities|form|biography|member|researchs)-e-\d+(?![A-Za-z0-9_-])'

foreach ($file in $htmlFiles) {
    $path = Join-Path $root $file
    $text = Get-Content -Path $path -Raw -Encoding utf8
    $text = [regex]::Replace($text, '(?<prefix>class=["''])?(?<value>[^"'']*)(?<suffix>["''])', {
        param($m)
        $prefix = $m.Groups['prefix'].Value
        $value = $m.Groups['value'].Value
        $suffix = $m.Groups['suffix'].Value
        if ($prefix -eq '') { return $m.Value }
        $tokens = $value -split '\s+' | Where-Object { $_ -and $_ -notmatch $legacyPattern }
        return "$prefix$($tokens -join ' ')$suffix"
    })
    $text = $text -replace 'class=""', ''
    $text = $text -replace "class=''", ''
    Set-Content -Path $path -Value $text -Encoding utf8
}

foreach ($file in $cssFiles) {
    $path = Join-Path $root $file
    $text = Get-Content -Path $path -Raw -Encoding utf8
    $pattern = '(?ms)(?<selector>[^{}]+\{)'
    $matches = [regex]::Matches($text, $pattern)
    $sb = [System.Text.StringBuilder]::new()
    $lastIndex = 0
    foreach ($m in $matches) {
        $selector = $m.Groups['selector'].Value
        $openBrace = $selector.LastIndexOf('{')
        if ($openBrace -ge 0) {
            $selText = $selector.Substring(0, $openBrace).Trim()
        } else {
            $selText = $selector.Trim()
        }
        if ($selText -match $legacyPattern) {
            $start = $m.Index
            $end = $start + $m.Length
            $sb.Append($text.Substring($lastIndex, $start - $lastIndex)) | Out-Null
            $lastIndex = $end
        }
    }
    $sb.Append($text.Substring($lastIndex)) | Out-Null
    $text = $sb.ToString()
    $text = $text -replace '(?m)^\s*\n', ''
    $text = $text -replace '\n{3,}', "`n`n"
    Set-Content -Path $path -Value $text.Trim() -Encoding utf8
}

Write-Host 'Legacy class cleanup complete.'
