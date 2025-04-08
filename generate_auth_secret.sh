#!/bin/bash

# Generate a secure authentication secret
AUTH_SECRET=$(openssl rand -hex 32)

# Update the .env file
sed -i "s/AUTH_SECRET=.*/AUTH_SECRET=$AUTH_SECRET/" .env

echo "Generated new AUTH_SECRET: $AUTH_SECRET"
echo "Updated .env file with the new secret."
echo "Make sure to deploy with this updated .env file."
