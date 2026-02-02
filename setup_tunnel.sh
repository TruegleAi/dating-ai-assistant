#!/bin/bash
# Setup Cloudflare Tunnel for external access

echo "Setting up Cloudflare Tunnel..."

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ cloudflared is not installed"
    echo "Please install it first:"
    echo "  macOS: brew install cloudflare/cloudflare/cloudflared"
    echo "  Ubuntu: curl -L https://pkg.cloudflare.com/pubkey.gpg | sudo apt-key add -"
    exit 1
fi

# Check if config directory exists
if [ ! -d "config" ]; then
    mkdir config
fi

# Create cloudflared configuration
cat > config/cloudflared_config.yml << EOF
tunnel: $(uuidgen | tr -d '-')
credentials-file: config/creds.json

ingress:
  - hostname: munch-yourname.trycloudflare.com
    service: http://localhost:5000
  - service: http_status:404
EOF

echo "✅ Cloudflare tunnel configuration created"
echo "Configuration file: config/cloudflared_config.yml"
echo ""
echo "To complete the setup:"
echo "1. Run: cloudflared tunnel --config ./config/cloudflared_config.yml create"
echo "2. Follow the prompts to authenticate with Cloudflare"
echo "3. Update the config/cloudflared_config.yml with the generated tunnel ID"
echo "4. Run: cloudflared tunnel --config ./config/cloudflared_config.yml run"
echo ""
echo "Alternatively, you can run the tunnel directly with:"
echo "cloudflared tunnel --url http://localhost:5000"