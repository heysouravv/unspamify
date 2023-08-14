#!/bin/bash

# Define backup directory and filename
BACKUP_DIR="./"
BACKUP_NAME="nginx_certbot_backup_$(date +'%Y_%m_%d').zip"

# Backup nginx configuration
NGINX_CONFIG_PATH="/etc/nginx/sites-available/unspamify"

# Backup certbot (Let's Encrypt) configurations
CERTBOT_PATH="/etc/letsencrypt"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Use zip to compress and backup the files
zip -r "$BACKUP_DIR/$BACKUP_NAME" "$NGINX_CONFIG_PATH" "$CERTBOT_PATH"

# Print out the location of the backup for confirmation
echo "Backup created at $BACKUP_DIR/$BACKUP_NAME"

