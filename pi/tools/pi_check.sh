echo "== host"; hostname; uname -a; uptime; vcgencmd measure_temp 2>/dev/null; vcgencmd get_throttled 2>/dev/null
echo "== ip"; ip -4 -br addr; ip route
echo "== static ip / dhcpcd / NM"; ls /etc/dhcpcd.conf 2>&1; grep -v '^#' /etc/dhcpcd.conf 2>/dev/null | grep -A3 'interface eth0'; nmcli -t -f NAME,DEVICE,TYPE con show 2>&1; nmcli -t dev 2>&1; nmcli -f ipv4.method,ipv4.addresses con show "$(nmcli -t -f NAME,DEVICE con show --active | grep eth0 | cut -d: -f1)" 2>&1
echo "== avahi"; systemctl is-active avahi-daemon 2>&1; dpkg -l avahi-daemon 2>/dev/null | tail -1
echo "== services"; for s in hostapd-depot dnsmasq-depot depot; do echo "$s: $(systemctl is-enabled $s 2>&1) / $(systemctl is-active $s 2>&1)"; done
echo "== depot dir"; ls -la ~/depot ~/depot/static 2>&1; ls ~/depot-venv/bin/python 2>&1
echo "== deployed unit files"; for s in hostapd-depot dnsmasq-depot depot; do echo "--- $s"; systemctl cat $s 2>&1 | grep -v '^\s*#' | grep -v '^\s*$'; done
echo "== unit warnings"; journalctl -b --no-pager 2>/dev/null | grep -iE 'depot.*(ignoring|failed)' | tail -10
echo "== logs"; for s in hostapd-depot dnsmasq-depot depot; do echo "--- $s"; journalctl -u $s -b -n 12 --no-pager -o cat 2>&1; done
echo "== server.py compiles?"; ~/depot-venv/bin/python -m py_compile ~/depot/server.py && echo OK
echo "== md5"; md5sum ~/depot/server.py ~/depot/static/index.html ~/depot/hostapd.conf ~/depot/dnsmasq-depot.conf 2>&1
echo "== http"; curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1/ 2>&1
echo "== sudo nopasswd?"; sudo -n true 2>&1 && echo yes
echo "== wlan"; iw dev 2>&1 | head; rfkill list 2>&1 | head
