# Production Docker Secrets Setup

To run `docker-compose.prod.yml`, create the `./deploy/secrets/` directory and populate the 4 secret files.
(These files are ignored by git in `.gitignore`):

```bash
mkdir -p deploy/secrets

# 1. Database password (alphanumeric, at least 32 characters)
openssl rand -hex 24 > deploy/secrets/db_password.secret

# 2. Session signing key (at least 32 bytes)
openssl rand -hex 32 > deploy/secrets/secret_key.secret

# 3. Master encryption key (exactly 32 bytes base64-encoded)
openssl rand -base64 32 > deploy/secrets/master_key.secret

# 4. Blind index key (exactly 32 bytes base64-encoded)
openssl rand -base64 32 > deploy/secrets/index_key.secret

# Restrict permissions to owner only
chmod 600 deploy/secrets/*.secret
```
