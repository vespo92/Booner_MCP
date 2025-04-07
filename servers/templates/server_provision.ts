// Pulumi TypeScript program for server provisioning
// This is a template for the OPN_IaC system to use

import * as command from "@pulumi/command";
import * as pulumi from "@pulumi/pulumi";

// Configuration
const config = new pulumi.Config();
const serverName = config.require("server_name");
const serverIp = config.require("server_ip");
const serverRole = config.require("server_role");
const sshKeyPath = config.get("ssh_key_path") || "~/.ssh/mcp_id_ed25519.pub";

// Connection information for the target server
const connection = {
    host: serverIp,
    user: "mcp-service",
    privateKey: sshKeyPath.replace(".pub", ""),
};

// Initial server configuration
const serverSetup = new command.remote.Command(`${serverName}-setup`, {
    connection,
    create: pulumi.interpolate`
        # Update system
        sudo apt-get update && sudo apt-get upgrade -y

        # Install required packages
        sudo apt-get install -y docker.io python3 python3-pip git curl wget

        # Enable services
        sudo systemctl enable docker
        sudo systemctl start docker

        # Create service directories
        mkdir -p ~/mcp-managed
        mkdir -p ~/mcp-logs
        mkdir -p ~/mcp-data

        # Set hostname
        sudo hostnamectl set-hostname ${serverName}

        # Configure firewall based on role
        if [ "${serverRole}" = "worker" ]; then
            sudo ufw allow from 10.0.0.4 to any port 22
            sudo ufw allow from 10.0.0.2 to any port 22
        fi

        # Log completion
        echo "Server provisioning completed: $(date)" > ~/mcp-logs/provision.log
    `,
});

// Add server-specific configuration based on role
switch (serverRole) {
    case "worker":
        // Configure as worker node
        const workerSetup = new command.remote.Command(`${serverName}-worker-setup`, {
            connection,
            create: pulumi.interpolate`
                # Install worker-specific packages
                sudo apt-get install -y stress htop iotop

                # Configure worker services
                echo '{ "worker_name": "${serverName}", "manager_ip": "10.0.0.4" }' > ~/mcp-managed/worker-config.json

                # Log completion
                echo "Worker configuration completed: $(date)" >> ~/mcp-logs/provision.log
            `,
            opts: {
                dependsOn: [serverSetup],
            },
        });
        break;

    case "game_server":
        // Configure as game server
        const gameServerSetup = new command.remote.Command(`${serverName}-game-setup`, {
            connection,
            create: pulumi.interpolate`
                # Install game server prerequisites
                sudo apt-get install -y lib32gcc-s1 lib32stdc++6 libtinfo5
                
                # Create game server directories
                mkdir -p ~/mcp-managed/game-servers
                
                # Log completion
                echo "Game server configuration completed: $(date)" >> ~/mcp-logs/provision.log
            `,
            opts: {
                dependsOn: [serverSetup],
            },
        });
        break;

    default:
        // Generic configuration for other roles
        break;
}

// Export server information
export const serverDetails = {
    name: serverName,
    ip: serverIp,
    role: serverRole,
    provisionTime: serverSetup.stdout,
};
