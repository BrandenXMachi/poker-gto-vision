# Verifies the deployed gate on lelabubu.ca.
$ErrorActionPreference = 'SilentlyContinue'
$base = 'https://lelabubu.ca'
$token = '7de45996143b4417284bfebd69f37a282effb4938376155e961d545afde258ce'

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
