# Download Qwen 2.5 7B Instruct (GGUF) para o LLM local.
# O arquivo no Hugging Face esta split em 2 partes; cada parte e verificada
# por SHA-256 antes de ser concatenada no arquivo final esperado pelo backend.

$ErrorActionPreference = "Stop"

$baseUrl = "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main"
$parts = @(
    @{
        Name   = "qwen2.5-7b-instruct-q4_k_m-00001-of-00002.gguf"
        Sha256 = "dfce12e3862a5283ccfb88221b48480e58745165de856439950d0f22590580db"
    },
    @{
        Name   = "qwen2.5-7b-instruct-q4_k_m-00002-of-00002.gguf"
        Sha256 = "539cf93f78e887edea1c04e2d7d8cdaca9d01dae9c9025bcb8accbe29df3d72a"
    }
)

$modelDir = Join-Path $PSScriptRoot ".." "models" "qwen"
$modelFile = Join-Path $modelDir "qwen2.5-7b-instruct-q4_k_m.gguf"

New-Item -ItemType Directory -Path $modelDir -Force | Out-Null

if (Test-Path $modelFile) {
    Write-Host "Model already exists at $modelFile"
    exit 0
}

function Get-FileSha256($Path) {
    (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

foreach ($part in $parts) {
    $partPath = Join-Path $modelDir $part.Name
    $url = "$baseUrl/$($part.Name)"

    if (Test-Path $partPath) {
        if ((Get-FileSha256 $partPath) -eq $part.Sha256) {
            Write-Host "Part OK (cached): $($part.Name)"
            continue
        }
        Write-Host "Hash mismatch on existing part, re-downloading: $($part.Name)"
        Remove-Item $partPath -Force
    }

    Write-Host "Downloading $($part.Name)..."
    Write-Host "URL: $url"
    try {
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($url, $partPath)
    } catch {
        Write-Host "Download failed: $_"
        Write-Host "Try manually downloading from:"
        Write-Host $url
        exit 1
    }

    $hash = Get-FileSha256 $partPath
    if ($hash -ne $part.Sha256) {
        Write-Host "SHA-256 mismatch for $($part.Name)!"
        Write-Host "  expected: $($part.Sha256)"
        Write-Host "  got:      $hash"
        Remove-Item $partPath -Force
        exit 1
    }
    Write-Host "SHA-256 OK: $($part.Name)"
}

Write-Host "Concatenating parts into $modelFile..."
$out = [System.IO.File]::Create($modelFile)
try {
    foreach ($part in $parts) {
        $in = [System.IO.File]::OpenRead((Join-Path $modelDir $part.Name))
        try { $in.CopyTo($out) } finally { $in.Close() }
    }
} finally {
    $out.Close()
}

Write-Host "Model ready: $modelFile"
