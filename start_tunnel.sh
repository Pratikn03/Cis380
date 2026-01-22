#!/bin/bash

# 1. Go to https://dashboard.ngrok.com/domains to claim your free static domain.
# 2. Replace the value below with your actual domain (e.g., "funny-cat.ngrok-free.app")
YOUR_DOMAIN="replace-this-with-your-domain.ngrok-free.app"

echo "Starting ngrok tunnel on port 8001 with domain: $YOUR_DOMAIN"
ngrok http --domain=$YOUR_DOMAIN 8001