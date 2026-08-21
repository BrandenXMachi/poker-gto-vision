# Verifies the site gate: unauthenticated requests must be redirected,
# a valid session token must pass, and a forged token must be rejected.
$ErrorActionPreference = 'SilentlyContinue'
$base = 'http://localhost:3000'
$token = '4100cc6c18389514a35481bb514b5953d856e28f6dd07ccb0e4ed054e1fb1a6e'

$paths = @(
  '/',
  '/gto-trainer/index.html',
  '/gto-trainer/app.js',
  '/gto-trainer/data/RFI/UTG/UTG.json'
)

function Get-Code {
  param($url, $cookie)
  $req = [System.Net.HttpWebRequest]::Create($url)
  $req.AllowAutoRedirect = $false
  $req.Timeout = 15000
  if ($cookie) { $req.Headers.Add('Cookie', "lelabubu_auth=$cookie") }
  try {
    $resp = $req.GetResponse()
    $code = [int]$resp.StatusCode
    $resp.Close()
    return $code
  } catch [System.Net.WebException] {
    if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
    return 0
  }
}

Write-Output '=== NO COOKIE (expect 307 -> /login) ==='
foreach ($p in $paths) {
  '{0,-42} {1}' -f $p, (Get-Code "$base$p" $null)
}

Write-Output ''
Write-Output '=== VALID TOKEN (expect 200) ==='
foreach ($p in $paths) {
  '{0,-42} {1}' -f $p, (Get-Code "$base$p" $token)
}

Write-Output ''
Write-Output '=== FORGED TOKEN (expect 307) ==='
'{0,-42} {1}' -f '/gto-trainer/data/RFI/UTG/UTG.json', (Get-Code "$base/gto-trainer/data/RFI/UTG/UTG.json" 'deadbeef')

Write-Output ''
Write-Output '=== LOGIN PAGE reachable (expect 200) ==='
'{0,-42} {1}' -f '/login', (Get-Code "$base/login" $null)
