#!/usr/bin/env bash
# =====================================================================
# DEPOT — deploy helper (run this on the LAPTOP, not the Pi)
# =====================================================================
# Pushes updated code from your laptop into the Pi and bounces the
# server. Usage:
#
#   bash deploy.sh            # push server.py + index.html + restart
#   bash deploy.sh html       # push ONLY index.html (no restart needed)
#   bash deploy.sh server     # push ONLY server.py + restart
#   bash deploy.sh clear      # wipe the chat history on the Pi
#   bash deploy.sh configs    # push hostapd/dnsmasq confs + systemd units, reload
#   bash deploy.sh logs       # tail the server log
#   bash deploy.sh status     # show state of all three services
#
# NOTE: the Pi must be reachable over the ethernet cable (laptop ICS).
#       In the field, use the Pi's keyboard/serial instead.
PI="${DEPOT_PI:-netpie@192.168.137.142}"   # override: DEPOT_PI=netpie@<ip> bash deploy.sh
BASE="/home/netpie/depot"
# SSH uses your stored key (~/.ssh/id_ed25519). For sudo, the Pi's netpie user
# needs passwordless sudo OR set: DEPOT_SUDO="echo 'your-password' | sudo -S"
SUDO="${DEPOT_SUDO:-echo | sudo -S}"

cd "$(dirname "$0")"   # always run relative to the repo folder

case "$1" in
  ""|both)
    scp server.py  "$PI:$BASE/server.py"
    scp index.html  "$PI:$BASE/static/index.html"
    ssh $PI "mkdir -p $BASE/uploads && $SUDO systemctl restart depot && systemctl is-active depot"
    ;;
  html)
    scp index.html  "$PI:$BASE/static/index.html"
    echo "pushed — phones need to refresh their browser tab."
    ;;
  server)
    scp server.py  "$PI:$BASE/server.py"
    ssh $PI "$SUDO systemctl restart depot && systemctl is-active depot"
    ;;
  clear)
    ssh $PI "rm -f $BASE/depot.db $BASE/uploads/* && $SUDO systemctl restart depot"
    echo "chat history wiped."
    ;;
  configs)
    scp hostapd.conf dnsmasq-depot.conf "$PI:$BASE/"
    scp systemd/*.service "$PI:/tmp/"
    ssh $PI "$SUDO cp /tmp/depot.service /tmp/hostapd-depot.service /tmp/dnsmasq-depot.service /etc/systemd/system/ && \
             $SUDO systemctl daemon-reload && \
             $SUDO systemctl restart hostapd-depot dnsmasq-depot depot && \
             systemctl is-active hostapd-depot dnsmasq-depot depot"
    ;;
  status)
    ssh $PI "systemctl is-active hostapd-depot dnsmasq-depot depot; hostname -I"
    ;;
  logs)
    ssh $PI "journalctl -u depot -f --no-pager -o cat"
    ;;
  *)
    echo "unknown mode: $1 (use: both | html | server | clear | configs | status | logs)"
    ;;
esac
