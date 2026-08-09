$root = Get-Location
$htmlFiles = @('index.html','activities.html','biography.html','form.html','member.html','researchs.html')
$cssFiles = @('index.css','activities.css','biography.css','form.css','member.css','researchs.css','site.css')
$legacyPattern = '(?<![A-Za-z0-9_-])(?:home|activities|form|biography|member|researchs)-e-\d+(?![A-Za-z0-9_-])'

function Find-MatchingBrace {
    param([string]$Text, [int]$OpenIndex)
    $depth = 0
    $inSingle = $false
    $inDouble = $false
    for ($i = $OpenIndex; $i -lt $Text.Length; $i++) {
        $ch = $Text[$i]
        if ($ch -eq "'" -and -not $inDouble) {
            $inSingle = -not $inSingle
        }
        elseif ($ch -eq '"' -and -not $inSingle) {
            $inDouble = -not $inDouble
        }
        elseif (-not $inSingle -and -not $inDouble) {
            if ($ch -eq '{') {
                $depth++
            }
            elseif ($ch -eq '}') {
                $depth--
                if ($depth -eq 0) {
                    return $i
                }
            }
        }
    }
    return -1
}

function Remove-LegacyCSSBlocks {
    param([string]$Text)
    $result = [System.Text.StringBuilder]::new()
    $start = 0
    while ($start -lt $Text.Length) {
        $openIndex = $Text.IndexOf('{', $start)
        if ($openIndex -lt 0) {
            [void]$result.Append($Text.Substring($start))
            break
        }
        $prefix = $Text.Substring($start, $openIndex - $start)
        $closeIndex = Find-MatchingBrace -Text $Text -OpenIndex $openIndex
        if ($closeIndex -lt 0) {
            [void]$result.Append($Text.Substring($start))
            break
        }
        $body = $Text.Substring($openIndex + 1, $closeIndex - $openIndex - 1)
        $selectorText = $prefix.Trim()
        if ($selectorText -and $selectorText -notmatch '^@' -and $selectorText -match $legacyPattern) {
            $start = $closeIndex + 1
            continue
        }
        [void]$result.Append($prefix)
        [void]$result.Append('{')
        [void]$result.Append((Remove-LegacyCSSBlocks -Text $body))
        [void]$result.Append('}')
        $start = $closeIndex + 1
    }
    return $result.ToString()
}

foreach ($file in $htmlFiles) {
    $path = Join-Path $root $file
    $text = [System.IO.File]::ReadAllText($path, [System.Text.UTF8Encoding]::new($false))
    $text = [regex]::Replace($text, 'class\s*=\s*(["''])(.*?)\1', {
        param($m)
        $quote = $m.Groups[1].Value
        $value = $m.Groups[2].Value
        $tokens = @($value -split '\s+' | Where-Object { $_ -and $_ -notmatch $legacyPattern })
        return "class=$quote$($tokens -join ' ')$quote"
    })
    $text = $text -replace 'class=""', ''
    $text = $text -replace "class=''", ''
    [System.IO.File]::WriteAllText($path, $text, [System.Text.UTF8Encoding]::new($false))
}

foreach ($file in $cssFiles) {
    $path = Join-Path $root $file
    $text = [System.IO.File]::ReadAllText($path, [System.Text.UTF8Encoding]::new($false))
    $text = Remove-LegacyCSSBlocks -Text $text
    $text = $text -replace '\n{3,}', "`n`n"
    [System.IO.File]::WriteAllText($path, $text.Trim() + "`n", [System.Text.UTF8Encoding]::new($false))
}

Write-Host 'Legacy class cleanup complete.'
