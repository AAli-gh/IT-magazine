#!/bin/sh
# First-time HTTPS certificate. Run once on the server after filling .env:
#   sh deploy/init-letsencrypt.sh you@example.com
# It starts nginx with a temporary self-signed cert, requests the real one, then reloads nginx.
set -e
EMAIL="$1"
[ -z "$EMAIL" ] && { echo "usage: $0 <email>"; exit 1; }
. ./.env
COMPOSE="docker compose -f docker-compose.prod.yml"
LIVE="/etc/letsencrypt/live/$DOMAIN"

$COMPOSE run --rm --entrypoint sh certbot -c "mkdir -p $LIVE && \
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 -keyout $LIVE/privkey.pem -out $LIVE/fullchain.pem -subj /CN=localhost"
$COMPOSE up -d nginx
$COMPOSE run --rm --entrypoint sh certbot -c "rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf"
$COMPOSE run --rm certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" -d "www.$DOMAIN" \
  --email "$EMAIL" --agree-tos --no-eff-email
$COMPOSE exec nginx nginx -s reload
echo "HTTPS is ready for $DOMAIN"
