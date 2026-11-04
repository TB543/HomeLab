# HomeLab 🏠

A Raspberry Pi home lab that runs 24/7 in my apartment, hosting various network services, automation scripts, and applications. The goal is to have a centralized system that handles networking, home automation, remote access, and entertainment.

## Features

The Raspberry Pi currently runs the following services:

| Service | Description |
|---|---|
| **Pi-hole** | Network-wide ad blocking and DNS filtering. |
| **Wi-Fi Access Point** | Turns the Raspberry Pi into a wireless access point. |
| **Tailscale** | Provides secure remote access to the home lab from anywhere. |
| **App Launcher** | A custom application launcher and dashboard for managing services and applications. Supports weather information and status indicators. |
| **CEC Remote Integration** | Allows the app launcher to be controlled using a TV remote through HDMI-CEC. It can also forward remote inputs to currently running applications. |
| **Home Automation** | Automatically turns apartment lights on and off based on the state of a switch-controlled smart outlet. |
| **Minecraft Server** | Hosts a Minecraft server with [playit.gg](https://playit.gg/) tunneling so people can connect without requiring port forwarding. |
| **CEC Device Name** | A service that sets the Raspberry Pi's HDMI-CEC device name. |

More services and automations will be added over time. Potential future additions include a VPN and other network services.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/TB543/HomeLab.git
   cd HomeLab
   ```

2. Run the setup script:

   ```bash
   bash resources/setup.sh
   ```

3. Follow the installation prompts.

The setup script will:
- Ask for some basic user and system information.
- Install and configure the required services.
- Prompt you to create accounts or provide credentials for certain services.
- Configure the Raspberry Pi to run the services automatically.

Some services require additional account setup during installation. Follow the prompts provided by the script.

## Configuration

### App Launcher

The app launcher configuration is located at:

```text
services/app-launcher/settings.json
```

This file controls the dashboard's location information and the applications displayed in the launcher.

#### Location

The `lat` and `long` properties specify the geographic coordinates used by the weather display.

The default coordinates are set to Charlotte, NC.

```json
{
    "lat": 35.2271,
    "long": -80.8431
}
```

#### Applications

The `apps` array contains the applications and commands displayed in the launcher.

Each application supports the following properties:

| Property | Required | Description |
|---|---|---|
| `name` | Yes | Display name shown on the launcher button. |
| `cmd` | Yes | Command to execute when the application is selected. |
| `cmd.args` | Yes | Shell command to execute. |
| `cmd.cwd` | No | Working directory in which to execute the command. |
| `status` | No | Command used to determine whether an application or service is running. |
| `status.args` | Yes, if status is defined | Shell command that returns an exit code of `0` or `1`. |

The status command is used to display an emoji next to the application name, indicating whether the associated service is running.

- Exit code `0`: Running.
- Exit code `1`: Not running.

For example, the following configuration adds a button to toggle the Minecraft server and displays its current status:

```json
{
    "name": "Toggle MC-Server",
    "cmd": {
        "args": "systemctl is-active --quiet minecraft-server.service && sudo systemctl disable --now minecraft-server.service || sudo systemctl enable --now minecraft-server.service"
    },
    "status": {
        "args": "test \"$(systemctl is-active minecraft-server.service)\" = \"active\""
    }
}
```

#### Example Configuration

Here is an example of a complete app launcher configuration:

```json
{
    "lat": 35.2271,
    "long": -80.8431,
    "apps": [
        {
            "name": "4RunnerFX",
            "cmd": {
                "args": "python main.py",
                "cwd": "~/4RunnerEffects/src"
            }
        },
        {
            "name": "Toggle Lights",
            "cmd": {
                "args": "curl -X POST http://localhost:5001/"
            },
            "status": {
                "args": "test \"$(curl -s http://localhost:5001/)\" = \"ON\""
            }
        },
        {
            "name": "Toggle MC-Server",
            "cmd": {
                "args": "systemctl is-active --quiet minecraft-server.service && sudo systemctl disable --now minecraft-server.service || sudo systemctl enable --now minecraft-server.service"
            },
            "status": {
                "args": "test \"$(systemctl is-active minecraft-server.service)\" = \"active\""
            }
        },
        {
            "name": "Reboot System",
            "cmd": {
                "args": "sudo reboot"
            }
        }
    ]
}
```

The commands above are examples. Applications can execute any commands supported by the underlying system.

### Home Automation

The home automation configuration is located at:

```text
services/home-automation/settings.json
```

This file contains the connection information required to communicate with the Kasa smart switches.

It includes:
- Kasa account username.
- Kasa account password.
- IP addresses of the smart devices being monitored or controlled.

**Security note:** The Kasa password is currently stored in plaintext in this configuration file. This is required by the Kasa module being used by the project. Be careful when sharing this file or committing configuration changes to a public repository.

## HDMI-CEC Remote Integration

One of the main features of the app launcher is its ability to receive input from a TV remote through HDMI-CEC.

The launcher handles navigation and application selection. Additionally, when another application is running, the launcher can automatically forward remote inputs to that application.

For an application to receive forwarded remote controls, it must expose a POST endpoint on:

```text
http://localhost:5000/
```

The launcher sends a JSON request with the following format:

```json
{
    "input": "up"
}
```

The `input` property can contain one of the following values:

| Input | Description |
|---|---|
| `up` | Up navigation |
| `down` | Down navigation |
| `left` | Left navigation |
| `right` | Right navigation |
| `select` | Select / confirm |

Applications can implement this endpoint to integrate with the home lab's remote control system.

For example, a simple Flask implementation:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/", methods=["POST"])
def remote_input():
    data = request.get_json()
    input_value = data.get("input")

    if input_value == "up":
        print("Up pressed")
    elif input_value == "down":
        print("Down pressed")
    elif input_value == "left":
        print("Left pressed")
    elif input_value == "right":
        print("Right pressed")
    elif input_value == "select":
        print("Select pressed")

    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
```

This makes it possible to build applications that integrate directly with the TV remote without needing additional input hardware.

## Notes

- **Pi-hole:** The default password is `admin`. Change this after installation.
- **App Launcher:** Application commands and dashboard settings can be customized in `services/app-launcher/settings.json`.
- **Home Automation:** Smart switch credentials and device IP addresses are configured in `services/home-automation/settings.json`.
- **CEC Integration:** Applications can receive forwarded remote inputs by implementing the local HTTP POST endpoint described above.
- **Availability:** The Raspberry Pi is intended to run continuously, with services configured to start automatically.

## Future Plans

This is an ongoing project, and I plan to continue adding services and automations as I find new things to host.

Some potential additions:
- VPN server.
- Additional network services.
- More home automation integrations.
- Additional applications for the TV dashboard.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.