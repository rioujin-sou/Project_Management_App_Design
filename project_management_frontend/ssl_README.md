# SSL Certificates

Place your SSL certificate files in this directory:

## Required files

- `cert.pem` — your SSL certificate (for Let's Encrypt, use `fullchain.pem`)
- `key.pem`  — your private key

## Using Let's Encrypt (certbot)

```bash
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem   ./ssl/key.pem
```

## Using a self-signed certificate (development/testing only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./ssl/key.pem \
  -out ./ssl/cert.pem \
  -subj "/CN=localhost"
```

## After placing certificates

Update BACKEND_CORS_ORIGINS in docker-compose.yml to match your domain:

  BACKEND_CORS_ORIGINS: '["https://yourdomain.com"]'

Then start the stack:

  docker compose up -d --build
