# Fixing NVIDIA Container Toolkit for Ubuntu 24.04

## The Issue
Ubuntu 24.04 (Noble) is not yet officially supported by NVIDIA Container Toolkit repository, resulting in the error:
```
E: Unable to locate package nvidia-container-toolkit
```

## Solution: Use the Generic Repository

The repository-specific URLs (ubuntu22.04, etc.) are not working, but NVIDIA provides a generic repository that should work:

### Step 1: Remove the current broken repository file
```bash
sudo rm /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### Step 2: Add NVIDIA GPU key
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
```

### Step 3: Add the generic stable repository
```bash
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### Step 4: Update and install
```bash
sudo apt update
sudo apt install -y nvidia-container-toolkit
```

### Step 5: Configure Docker
```bash
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Step 6: Test with a container
```bash
sudo docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi
```

## Alternative: Manual Docker Configuration

If the above method still doesn't work, you can manually configure Docker to use the NVIDIA runtime:

```bash
# Create or modify /etc/docker/daemon.json
sudo nano /etc/docker/daemon.json
```

Add the following content:
```json
{
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```

Restart Docker:
```bash
sudo systemctl restart docker
```

## Alternative: Direct Package Download

As a last resort, you can manually download and install the .deb packages:

```bash
# Create a directory for the packages
mkdir -p ~/nvidia-packages
cd ~/nvidia-packages

# Download the latest packages
wget https://raw.githubusercontent.com/NVIDIA/libnvidia-container/gh-pages/stable/deb/amd64/libnvidia-container1_1.17.0-1_amd64.deb
wget https://raw.githubusercontent.com/NVIDIA/libnvidia-container/gh-pages/stable/deb/amd64/libnvidia-container-tools_1.17.0-1_amd64.deb
wget https://raw.githubusercontent.com/NVIDIA/libnvidia-container/gh-pages/stable/deb/amd64/nvidia-container-toolkit_1.17.0-1_amd64.deb

# Install the packages in the correct order
sudo dpkg -i libnvidia-container1_1.17.0-1_amd64.deb
sudo dpkg -i libnvidia-container-tools_1.17.0-1_amd64.deb
sudo dpkg -i nvidia-container-toolkit_1.17.0-1_amd64.deb

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

## Troubleshooting

If you encounter dependency issues, you may need to install additional packages:
```bash
sudo apt install -f
```

If the NVIDIA runtime is not recognized, verify the Docker configuration:
```bash
sudo docker info | grep Runtimes
```

Check your NVIDIA driver installation:
```bash
nvidia-smi
```

## Temporary Workaround for MCP

If you need a quick temporary solution to run your MCP without GPU acceleration:

1. Remove the `--gpus all` flag from your Docker Compose file
2. This will allow the containers to run without GPU access while you work on fixing the NVIDIA toolkit issue
