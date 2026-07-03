#!/bin/sh

set -eu

project_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cert_dir="$project_root/docker/certs"
cert_file="$cert_dir/localhost.crt"
key_file="$cert_dir/localhost.key"

mkdir -p "$cert_dir"

if command -v mkcert >/dev/null 2>&1; then
  mkcert -cert-file "$cert_file" -key-file "$key_file" app.localhost api.localhost localhost 127.0.0.1 ::1
else
  echo "mkcert not found; generating a self-signed certificate (the browser will show a trust warning)."
  openssl req -x509 -newkey rsa:2048 -sha256 -nodes -days 365 \
    -keyout "$key_file" \
    -out "$cert_file" \
    -subj "/CN=app.localhost" \
    -addext "subjectAltName=DNS:app.localhost,DNS:api.localhost,DNS:localhost,IP:127.0.0.1,IP:::1"
fi

chmod 600 "$key_file"
echo "Local TLS certificate written to $cert_dir"
