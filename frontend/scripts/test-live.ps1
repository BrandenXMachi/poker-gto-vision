# Verifies the deployed gate on lelabubu.ca.
$ErrorActionPreference = 'SilentlyContinue'
$base = 'https://lelabubu.ca'
$token = '4100cc6c18389514a35481bb514b5953d856e28f6dd07ccb0e4ed054e1fb1a6e'

function Get-Result {
  param($url, $cookie)
  $req = [System.Net.HttpWebRequest]::Create($url)
  $req.AllowAutoRedirect = $false
  $req.Timeout = 25000
  if ($cookie) { $req.Headers.Add('Cookie', "lelabubu_auth=$cookie") }
  try {
    $resp = $req.GetResponse()
    $code = [int]$resp.StatusCode
    $loc = $resp.Headers['Location']
    $resp.Close()
    if ($loc) { return "$code -> $loc" }
    return "$code"
  } catch [System.Net.WebException] {
    if ($_.Exception.Response) {
      $c = [int]$_.Exception.Response.StatusCode
      $l = $_.Exception.Response.Headers['Location']
      if ($l) { return "$c -> $l" }
      return "$c"
    }
    return 'CONNECTION ERROR'
  }
}

$paths = @('/', '/gto-trainer/index.html', '/gto-trainer/data/RFI/UTG/UTG.json')

Write-Output '=== LIVE: NO COOKIE (expect 307 -> /login) ==='
foreach ($p in $paths) { '{0,-40} {1}' -f $p, (Get-Result "$base$p" $null) }

Write-Output ''
Write-Output '=== LIVE: VALID TOKEN (expect 200) ==='
foreach ($p in $paths) { '{0,-40} {1}' -f $p, (Get-Result "$base$p" $token) }

Write-Output ''
Write-Output '=== LIVE: LOGIN PAGE (expect 200) ==='
'{0,-40} {1}' -f '/login', (Get-Result "$base/login" $null)
