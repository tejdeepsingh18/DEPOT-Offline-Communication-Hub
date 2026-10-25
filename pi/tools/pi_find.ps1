# Sweep 192.168.137.0/24, then find the Pi by MAC prefix b8-27-eb (Raspberry Pi Foundation)
$pings = 1..254 | ForEach-Object { (New-Object System.Net.NetworkInformation.Ping).SendPingAsync("192.168.137.$_", 600) }
[System.Threading.Tasks.Task]::WaitAll($pings)
$alive = @(); $i = 1; foreach ($p in $pings) { if ($p.Result.Status -eq 'Success' -and $i -ne 1) { $alive += "192.168.137.$i" }; $i++ }
"ping-alive: $($alive -join ', ')"
$pi = (arp -a | Select-String 'b8-27-eb' | ForEach-Object { ($_ -split '\s+')[1] } | Select-Object -First 1)
if (-not $pi -and $alive.Count -gt 0) { $pi = $alive[0] }
"pi-ip: $pi"
if ($pi) { Set-Content -Path "$PSScriptRoot\pi_ip.txt" -Value $pi -NoNewline } else { Remove-Item "$PSScriptRoot\pi_ip.txt" -ErrorAction SilentlyContinue }
