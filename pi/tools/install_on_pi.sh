#!/usr/bin/env bash
# Runs ON THE PI (called by deploy_pi.bat). Backs up the live version,
# installs the new server.py + index.html, makes an HTTPS cert, restarts.
set -e
NEW=/tmp/depot_new
D=/home/netpie/depot
STAMP=$(date +%Y%m%d-%H%M%S)
BK=$D/backup-$STAMP
echo "== backing up current version to $BK"
mkdir -p "$BK"
cp -a "$D/server.py" "$BK/" 2>/dev/null || true
cp -a "$D/static/index.html" "$BK/" 2>/dev/null || true
[ -f "$D/depot.db" ] && cp -a "$D/depot.db" "$BK/"
echo "$BK" > "$D/.last_backup"

echo "== python / flask"
"$HOME/depot-venv/bin/python" -c "import flask, werkzeug, sys; print(sys.version.split()[0], 'flask', flask.__version__ if hasattr(flask,'__version__') else '?')" 2>/dev/null \
  || "$HOME/depot-venv/bin/python" -c "import importlib.metadata as m; print('flask', m.version('flask'))"

echo "== installing new files"
install -m 755 "$NEW/server.py" "$D/server.py"
install -m 644 "$NEW/index.html" "$D/static/index.html"
mkdir -p "$D/uploads" "$D/tls"
"$HOME/depot-venv/bin/python" -m py_compile "$D/server.py" && echo "server.py compiles OK"

if [ ! -f "$D/tls/cert.pem" ]; then
  echo "== generating self-signed HTTPS cert (for in-app voice recording)"
  openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=depot" \
    -addext "subjectAltName=IP:10.42.0.1,DNS:depot" \
    -keyout "$D/tls/key.pem" -out "$D/tls/cert.pem" 2>/dev/null \
  || openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=10.42.0.1" \
    -keyout "$D/tls/key.pem" -out "$D/tls/cert.pem"
  chmod 600 "$D/tls/key.pem"
fi

cat > "$D/rollback.sh" <<RB
#!/usr/bin/env bash
B=\$(cat $D/.last_backup)
cp -a "\$B/server.py" $D/server.py
cp -a "\$B/index.html" $D/static/index.html
sudo systemctl restart depot && echo "rolled back to \$B"
RB
chmod +x "$D/rollback.sh"

echo "== restarting depot (sudo will ask for the netpie password)"
sudo systemctl restart depot
sleep 6
echo "== service: $(systemctl is-active depot)"
journalctl -u depot -n 6 --no-pager -o cat
echo "== http  /api/status: $(curl -s -m 5 http://127.0.0.1/api/status)"
echo "== https /api/status: $(curl -sk -m 5 https://127.0.0.1/api/status)"
echo "== page: $(curl -s -m 5 -o /dev/null -w '%{http_code}' http://127.0.0.1/)"
echo "== DONE"
