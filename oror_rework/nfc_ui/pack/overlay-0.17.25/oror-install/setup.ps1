param([Parameter(Mandatory=$true)][string]$Root, [switch]$MenuOnly)
Set-StrictMode -Version 2
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$Root = [IO.Path]::GetFullPath($Root)
$Install = Join-Path $Root 'oror-install'
$Config = Get-Content -LiteralPath (Join-Path $Install 'install.json') -Raw | ConvertFrom-Json
$Cache = Join-Path $Install 'cache'
$Mods = Join-Path $Root 'mods'
[void][IO.Directory]::CreateDirectory($Cache)
[void][IO.Directory]::CreateDirectory($Mods)

function File-Sha([string]$Path) {
    $algorithm = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
    finally { $stream.Dispose(); $algorithm.Dispose() }
}
function Valid-File([string]$Path, $Spec) {
    return ((Test-Path -LiteralPath $Path -PathType Leaf) -and (Get-Item -LiteralPath $Path).Length -eq [long]$Spec.bytes -and (File-Sha $Path) -eq $Spec.sha256)
}
function Fetch-Verified($Spec, [string]$Path) {
    if (Valid-File $Path $Spec) { return }
    $temporary = $Path + '.download'
    if ((Test-Path -LiteralPath $temporary) -and (Get-Item -LiteralPath $temporary).Length -ge [long]$Spec.bytes) {
        Remove-Item -LiteralPath $temporary
    }
    Write-Host ('Downloading ' + $Spec.filename + ' ...')
    $output = [IO.File]::Open($temporary, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try {
        while ($output.Length -lt [long]$Spec.bytes) {
            $begin = $output.Length
            $last = [Math]::Min($begin + 2097151, [long]$Spec.bytes - 1)
            $request = [Net.HttpWebRequest]::Create([string]$Spec.url)
            $request.UserAgent = 'OROR-Nightfall-Verified-Installer/1'
            $request.Timeout = 60000
            $request.ReadWriteTimeout = 60000
            $request.AddRange([long]$begin, [long]$last)
            $response = $null
            try {
                $response = $request.GetResponse()
                if ([int]$response.StatusCode -eq 206) {
                    $range = [string]$response.Headers['Content-Range']
                    if ($range -notmatch '^bytes (\d+)-(\d+)/(\d+)$') { throw 'Invalid download range.' }
                    if ([long]$Matches[1] -ne $begin -or [long]$Matches[3] -ne [long]$Spec.bytes) { throw 'Wrong download range.' }
                    $output.Position = $begin
                } elseif ([int]$response.StatusCode -eq 200) {
                    $output.SetLength(0)
                    $output.Position = 0
                } else { throw 'Unexpected HTTP status.' }
                $sourceStream = $response.GetResponseStream()
                try { $sourceStream.CopyTo($output) } finally { $sourceStream.Dispose() }
                $output.Flush()
                if ($output.Length -gt [long]$Spec.bytes -or $output.Length -le $begin) { throw 'Invalid download length.' }
            } finally { if ($null -ne $response) { $response.Dispose() } }
        }
    } finally { $output.Dispose() }
    if (-not (Valid-File $temporary $Spec)) {
        Remove-Item -LiteralPath $temporary
        throw ('SHA-256 verification failed: ' + $Spec.filename)
    }
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path }
    [IO.File]::Move($temporary, $Path)
}
function Valid-SwordJar([string]$Path, $Members) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    $jar = $null
    try {
        $expected = New-Object 'System.Collections.Generic.Dictionary[string,string]' ([StringComparer]::Ordinal)
        foreach ($property in $Members.PSObject.Properties) { $expected.Add($property.Name, [string]$property.Value) }
        $seen = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
        $jar = [IO.Compression.ZipFile]::OpenRead($Path)
        foreach ($entry in $jar.Entries) {
            if ($entry.FullName.EndsWith('/')) { continue }
            if (-not $expected.ContainsKey($entry.FullName) -or -not $seen.Add($entry.FullName)) { return $false }
            $stream = $entry.Open(); $hash = [Security.Cryptography.SHA256]::Create()
            try { $actual = ([BitConverter]::ToString($hash.ComputeHash($stream))).Replace('-','').ToLowerInvariant() }
            finally { $stream.Dispose(); $hash.Dispose() }
            if ($actual -ne $expected[$entry.FullName]) { return $false }
        }
        return ($seen.Count -eq $expected.Count)
    } catch { return $false }
    finally { if ($null -ne $jar) { $jar.Dispose() } }
}
function Build-SwordJar([string]$Original, [string]$Overlay, [string]$Target) {
    $source = [IO.Compression.ZipFile]::OpenRead($Original)
    $patch = [IO.Compression.ZipFile]::OpenRead($Overlay)
    $result = $null
    try {
        $replaced = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::Ordinal)
        foreach ($entry in $patch.Entries) { [void]$replaced.Add($entry.FullName) }
        $result = [IO.Compression.ZipFile]::Open($Target, [IO.Compression.ZipArchiveMode]::Create)
        foreach ($archive in @($source,$patch)) {
            foreach ($entry in $archive.Entries) {
                if ($entry.FullName.EndsWith('/')) { continue }
                if ($archive -eq $source -and $replaced.Contains($entry.FullName)) { continue }
                $new = $result.CreateEntry($entry.FullName, [IO.Compression.CompressionLevel]::Optimal)
                $sourceStream = $entry.Open(); $output = $new.Open()
                try { $sourceStream.CopyTo($output) } finally { $output.Dispose(); $sourceStream.Dispose() }
            }
        }
    } finally {
        if ($null -ne $result) { $result.Dispose() }
        $patch.Dispose(); $source.Dispose()
    }
}
function Install-Atomic([string]$From, [string]$To) {
    $stage = $To + '.installing'
    [IO.File]::Copy($From, $stage, $true)
    if (Test-Path -LiteralPath $To) {
        $backups = Join-Path $Install 'backups'; [void][IO.Directory]::CreateDirectory($backups)
        $backup = Join-Path $backups (([IO.Path]::GetFileName($To)) + '.' + [Guid]::NewGuid().ToString('N'))
        [IO.File]::Replace($stage, $To, $backup)
    } else { [IO.File]::Move($stage, $To) }
}

# 0.17.25: NightfallCraft's title, loading and world-loading screens (config/fancymenu) use TCR Core's menu images.
# TCR Core has no 1.21.1 build, so the images are copied out of NightfallCraft's 1.20.1 TCR Core jar, each one checked
# against install.json. A failure here only leaves the title screen without its images; it does not stop the setup.
$MenuDir = Join-Path (Join-Path (Join-Path (Join-Path $Root 'config') 'fancymenu') 'assets') 'nightfallcraft'
function Menu-Target([string]$Member) {
    $target = $MenuDir
    foreach ($part in $Member.Substring('assets/tcrcore/textures/'.Length).Split('/')) { $target = Join-Path $target $part }
    return $target
}
function Valid-Menu {
    foreach ($property in $Config.menu.members.PSObject.Properties) {
        $target = Menu-Target $property.Name
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { return $false }
        if ((File-Sha $target) -ne [string]$property.Value) { return $false }
    }
    return $true
}
function Install-Menu {
    $jarPath = Join-Path $Cache $Config.menu.filename
    Fetch-Verified $Config.menu $jarPath
    $jar = [IO.Compression.ZipFile]::OpenRead($jarPath)
    try {
        foreach ($property in $Config.menu.members.PSObject.Properties) {
            $entry = $jar.GetEntry($property.Name)
            if ($null -eq $entry) { throw ('Missing in TCR Core: ' + $property.Name) }
            $target = Menu-Target $property.Name
            [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
            $stage = $target + '.installing'
            $source = $entry.Open(); $output = [IO.File]::Create($stage)
            try { $source.CopyTo($output) } finally { $output.Dispose(); $source.Dispose() }
            if ((File-Sha $stage) -ne [string]$property.Value) {
                Remove-Item -LiteralPath $stage
                throw ('SHA-256 verification failed: ' + $property.Name)
            }
            if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target }
            [IO.File]::Move($stage, $target)
        }
    } finally { $jar.Dispose() }
    Remove-Item -LiteralPath $jarPath
}
if ($null -ne $Config.PSObject.Properties['menu']) {
    if (Valid-Menu) {
        Write-Host 'NightfallCraft menu images are ready.'
    } else {
        try {
            Install-Menu
            Write-Host 'NightfallCraft menu images installed.'
        } catch {
            Write-Warning ('NightfallCraft menu images could not be installed: ' + $_.Exception.Message + ' The game still works; run this file again later for the NightfallCraft title screen.')
        }
    }
}
if ($MenuOnly) { return }

$Nightfall = Join-Path $Mods $Config.nightfall.filename
$Sword = Join-Path $Mods $Config.sword_target
$Overlay = Join-Path $Install 'sword-soaring-overlay.zip'
if ((File-Sha $Overlay) -ne $Config.overlay_sha256) { throw 'The bundled compatibility overlay is damaged.' }
if ((Valid-File $Nightfall $Config.nightfall) -and (Valid-SwordJar $Sword $Config.sword_members)) {
    Write-Host 'Setup is already complete. You can launch the game.'
    Write-Output '{"status":"passed","already_installed":true}'
    return
}
$NfCache = Join-Path $Cache $Config.nightfall.filename
$SwordCache = Join-Path $Cache $Config.sword_source.filename
Fetch-Verified $Config.nightfall $NfCache
Fetch-Verified $Config.sword_source $SwordCache
$SwordReady = Join-Path $Cache 'sword-soaring-ready.jar'
if (Test-Path -LiteralPath $SwordReady) { Remove-Item -LiteralPath $SwordReady }
Build-SwordJar $SwordCache $Overlay $SwordReady
if (-not (Valid-SwordJar $SwordReady $Config.sword_members)) { throw 'Rebuilt Sword Soaring did not match the tested files.' }
# No mods are replaced until both downloads and the entire patched JAR pass verification.
Install-Atomic $NfCache $Nightfall
Install-Atomic $SwordReady $Sword
if (-not ((Valid-File $Nightfall $Config.nightfall) -and (Valid-SwordJar $Sword $Config.sword_members))) {
    throw 'Final installed files did not pass verification.'
}
foreach ($cachedFile in @($NfCache,$SwordCache,$SwordReady)) {
    if (Test-Path -LiteralPath $cachedFile) { Remove-Item -LiteralPath $cachedFile }
    if (Test-Path -LiteralPath $cachedFile) { throw 'A temporary installer cache file could not be removed.' }
}
Write-Host 'Setup complete. Nightfall and the OROR Sword Soaring compatibility port are ready.'
Write-Output '{"status":"passed","already_installed":false}'
