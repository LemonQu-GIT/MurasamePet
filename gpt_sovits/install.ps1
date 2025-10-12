Param (
    [ValidateSet("CU126", "CU128", "CPU")]
    [string]$Device = "CPU",
    [Parameter(Mandatory = $true)]
    [ValidateSet("HF", "HF-Mirror", "ModelScope")]
    [string]$Source,
    [switch]$DownloadUVR5
)

$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO]:" -ForegroundColor Green -NoNewline
    Write-Host " $Message"
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "[WARNING]:" -ForegroundColor Yellow -NoNewline
    Write-Host " $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS]:" -ForegroundColor Cyan -NoNewline
    Write-Host " $Message"
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "[ERROR]:" -ForegroundColor Red -NoNewline
    Write-Host " $Message"
}

function Invoke-Download {
    param(
        [Parameter(Mandatory = $true)][string]$Uri,
        [Parameter(Mandatory = $true)][string]$OutFile
    )
    try {
        Write-Info "Downloading $OutFile ..."
        Invoke-WebRequest -Uri $Uri -OutFile $OutFile -UseBasicParsing -ErrorAction Stop
    } catch {
        Write-ErrorMessage "Failed to download: $Uri"
        throw
    }
}

function Invoke-Unzip {
    param(
        [Parameter(Mandatory = $true)][string]$ZipPath,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force
    Remove-Item $ZipPath -Force
}

trap {
    Write-ErrorMessage $_.Exception.Message
    exit 1
}

chcp 65001 | Out-Null
Set-Location $PSScriptRoot

Write-Info "MurasamePet GPT-SoVITS 预训练模型下载脚本 (PowerShell)"
Write-Info "目标设备参数: $Device (仅用于日志提示)"

$PretrainedURL = ""
$G2PWURL = ""
$UVR5URL = ""
$NLTKURL = ""
$OpenJTalkURL = ""

switch ($Source) {
    "HF" {
        Write-Info "使用 HuggingFace 作为下载源"
        $PretrainedURL = "https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip"
        $G2PWURL = "https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip"
        $UVR5URL = "https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/uvr5_weights.zip"
        $NLTKURL = "https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/nltk_data.zip"
        $OpenJTalkURL = "https://huggingface.co/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/open_jtalk_dic_utf_8-1.11.tar.gz"
    }
    "HF-Mirror" {
        Write-Info "使用 HuggingFace Mirror 作为下载源"
        $PretrainedURL = "https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/pretrained_models.zip"
        $G2PWURL = "https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/G2PWModel.zip"
        $UVR5URL = "https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/uvr5_weights.zip"
        $NLTKURL = "https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/nltk_data.zip"
        $OpenJTalkURL = "https://hf-mirror.com/XXXXRT/GPT-SoVITS-Pretrained/resolve/main/open_jtalk_dic_utf_8-1.11.tar.gz"
    }
    "ModelScope" {
        Write-Info "使用 ModelScope 作为下载源"
        $PretrainedURL = "https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/pretrained_models.zip"
        $G2PWURL = "https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/G2PWModel.zip"
        $UVR5URL = "https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/uvr5_weights.zip"
        $NLTKURL = "https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/nltk_data.zip"
        $OpenJTalkURL = "https://www.modelscope.cn/models/XXXXRT/GPT-SoVITS-Pretrained/resolve/master/open_jtalk_dic_utf_8-1.11.tar.gz"
    }
}

if (-not (Test-Path "GPT_SoVITS/pretrained_models/sv")) {
    Write-Info "下载预训练模型..."
    $zipPath = "pretrained_models.zip"
    Invoke-Download -Uri $PretrainedURL -OutFile $zipPath
    Invoke-Unzip -ZipPath $zipPath -Destination "GPT_SoVITS"
    Write-Success "预训练模型下载完成"
} else {
    Write-Info "预训练模型已存在，跳过下载"
}

if (-not (Test-Path "GPT_SoVITS/text/G2PWModel")) {
    Write-Info "下载 G2PWModel..."
    $zipPath = "G2PWModel.zip"
    Invoke-Download -Uri $G2PWURL -OutFile $zipPath
    Invoke-Unzip -ZipPath $zipPath -Destination "GPT_SoVITS/text"
    Write-Success "G2PWModel 下载完成"
} else {
    Write-Info "G2PWModel 已存在，跳过下载"
}

if ($DownloadUVR5) {
    $uvrTarget = "tools/uvr5"
    if (-not (Test-Path "$uvrTarget/uvr5_weights")) {
        Write-Info "下载 UVR5 语音分离模型..."
        $zipPath = "uvr5_weights.zip"
        Invoke-Download -Uri $UVR5URL -OutFile $zipPath
        Invoke-Unzip -ZipPath $zipPath -Destination $uvrTarget
        Write-Success "UVR5 模型下载完成"
    } else {
        Write-Info "UVR5 模型已存在，跳过下载"
    }
}

$pythonCmd = $null
foreach ($candidate in @("python", "python3")) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($cmd) {
        $pythonCmd = $cmd.Path
        break
    }
}

if (-not $pythonCmd) {
    Write-WarningMessage "未找到 Python，可在安装依赖后重新运行脚本以下载 NLTK 数据和 Open JTalk 字典"
} else {
    try {
        $pythonPrefix = (& $pythonCmd "-c" "import sys; print(sys.prefix)").Trim()
    } catch {
        $pythonPrefix = ""
    }

    if ($pythonPrefix -and -not (Test-Path (Join-Path $pythonPrefix "nltk_data\tokenizers\punkt"))) {
        Write-Info "下载 NLTK 数据..."
        $zipPath = "nltk_data.zip"
        Invoke-Download -Uri $NLTKURL -OutFile $zipPath
        Invoke-Unzip -ZipPath $zipPath -Destination $pythonPrefix
        Write-Success "NLTK 数据下载完成"
    } elseif ($pythonPrefix) {
        Write-Info "NLTK 数据已存在，跳过下载"
    } else {
        Write-WarningMessage "Python 环境未就绪，跳过 NLTK 数据下载"
    }

    try {
        $pyopenjtalkPath = (& $pythonCmd "-c" "import os, pyopenjtalk; print(os.path.dirname(pyopenjtalk.__file__))").Trim()
    } catch {
        $pyopenjtalkPath = ""
    }

    if ($pyopenjtalkPath -and -not (Test-Path (Join-Path $pyopenjtalkPath "open_jtalk_dic_utf_8-1.11"))) {
        Write-Info "下载 Open JTalk 字典..."
        $tgzPath = "open_jtalk_dic_utf_8-1.11.tar.gz"
        Invoke-Download -Uri $OpenJTalkURL -OutFile $tgzPath
        tar -xzf $tgzPath -C $pyopenjtalkPath
        Remove-Item $tgzPath -Force
        Write-Success "Open JTalk 字典下载完成"
    } elseif ($pyopenjtalkPath) {
        Write-Info "Open JTalk 字典已存在，跳过下载"
    } else {
        Write-WarningMessage "pyopenjtalk 未安装，跳过 Open JTalk 字典下载"
    }
}

Write-Host ""
Write-Success "================================"
Write-Success "所有模型下载完成"
Write-Success "================================"
Write-Host ""
Write-Info "下一步操作："
Write-Info "  1. 返回项目根目录：cd .."
Write-Info "  2. 安装 Python 依赖：uv sync"
Write-Info "  3. 启动 TTS 服务：uv run python gpt_sovits/api_v2.py"
