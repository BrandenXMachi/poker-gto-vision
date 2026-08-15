# Confirms the deployed stylesheet on lelabubu.ca contains the bar fix.
$token = '7de45996143b4417284bfebd69f37a282effb4938376155e961d545afde258ce'
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
