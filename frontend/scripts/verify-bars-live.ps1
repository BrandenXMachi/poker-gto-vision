# Confirms the deployed stylesheet on lelabubu.ca contains the bar fix.
$token = '4100cc6c18389514a35481bb514b5953d856e28f6dd07ccb0e4ed054e1fb1a6e'
$url = 'https://lelabubu.ca/gto-trainer/style.css'

$req = [System.Net.HttpWebRequest]::Create($url)
$req.Headers.Add('Cookie', "lelabubu_auth=$token")
$req.Timeout = 25000
try {
  $resp = $req.GetResponse()
  $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
  $css = $reader.ReadToEnd()
  $reader.Close(); $resp.Close()
} catch {
  Write-Output ('Request failed: ' + $_.Exception.Message)
  exit 1
}

$m = [regex]::Match($css, '(?s)\.result-row \.result-bar-fill \{(.*?)\}')
if (-not $m.Success) {
  Write-Output 'FAIL: .result-bar-fill rule not found in deployed CSS'
  exit 1
}

$rule = $m.Groups[1].Value
Write-Output 'Deployed .result-bar-fill rule:'
Write-Output $rule.Trim()
Write-Output ''
if ($rule -match 'display\s*:\s*block') {
  Write-Output 'PASS: deployed CSS contains display:block - bars will fill.'
} else {
  Write-Output 'FAIL: deployed CSS still missing display:block (deploy may not be finished).'
}
