from logging import root
from subprocess import Popen, PIPE, run
from requests import post, get
from json import load, dump
from threading import Thread
from datetime import datetime
from customtkinter import CTk, CTkFrame, CTkLabel, StringVar, CTkScrollableFrame, CTkButton, set_appearance_mode, set_default_color_theme
from psutil import cpu_percent, virtual_memory, disk_usage, sensors_temperatures


def user_input():
    """
    reads the cec commands sent to the pi from the tv and parses them
    """

    # monitors the cec commands
    process = Popen(
        ["sudo", "cec-ctl", "-d", "/dev/cec0", "--monitor"],
        stdout=PIPE,
        text=True,
        bufsize=1
    )

    # parses command output
    for line in process.stdout:
        if "ui-cmd" in line:
            cec = line.split(" ")[1]

            # controls this program
            if root.winfo_viewable():
                prev = app_grid["active"]
                root.after(0, lambda: app_grid[prev].configure(fg_color=app_grid[prev].cget("hover_color"), hover_color=app_grid[prev].cget("fg_color")))
                match cec:
                    case "up":
                        app_grid["active"] = ((app_grid["active"][0] - 1), app_grid["active"][1])
                    case "down":
                        app_grid["active"] = ((app_grid["active"][0] + 1), app_grid["active"][1])
                    case "left":
                        app_grid["active"] = (app_grid["active"][0], (app_grid["active"][1] - 1))
                    case "right":
                        app_grid["active"] = (app_grid["active"][0], (app_grid["active"][1] + 1))
                    case "select":
                        root.after(0, app_grid[app_grid["active"]].invoke)
                if app_grid["active"] not in app_grid: app_grid["active"] = prev
                root.after(0, lambda: app_grid[app_grid["active"]].configure(fg_color=app_grid[app_grid["active"]].cget("hover_color"), hover_color=app_grid[app_grid["active"]].cget("fg_color")))
                root.after(0, lambda: apps._parent_canvas.yview_moveto(max(0, min(1, (app_grid[app_grid["active"]].winfo_y() if app_grid[app_grid["active"]].winfo_y() < apps._parent_canvas.canvasy(0) else app_grid[app_grid["active"]].winfo_y() + app_grid[app_grid["active"]].winfo_height() - apps._parent_canvas.winfo_height()) / apps._parent_canvas.bbox("all")[3]))) if app_grid[app_grid["active"]].winfo_y() < apps._parent_canvas.canvasy(0) or app_grid[app_grid["active"]].winfo_y() + app_grid[app_grid["active"]].winfo_height() > apps._parent_canvas.canvasy(0) + apps._parent_canvas.winfo_height() else None)

            # sends control to running program
            else:
                try:
                    post("http://localhost:5000", json={"input": cec})
                except:
                    pass


def launch_app(command):
    """
    launches an app with the given command
    
    :param command: the command to launch the app
    """

    root.withdraw()
    Thread(target=lambda: [Popen(**command, shell=True).wait(), root.deiconify()], daemon=True).start()


def update_ui():
    """
    updates UI elements on the screen every second
    """

    # sets time
    root.after(1000, update_ui)
    now = datetime.now()
    prev_min = time.get()[-4] if time.get() else ""
    time.set(now.strftime("%I %M %p" if ":" in time.get() else "%I:%M %p"))
    date.set(now.strftime("%A, %B %-d, %Y"))

    # sets system stats
    if now.second % 3 == 0:
        cpu.set(f"{cpu_percent()}%")
        ram.set(f"{virtual_memory().percent}%")
        cpu_temp.set(f"{sensors_temperatures()['cpu_thermal'][0].current:.1f}°C")
        disk.set(f"{disk_usage('/').percent}%")

    # updates button statuses
    for button in app_grid["status_btns"]:
        button.update_status()

    # only updates weather every minute
    if prev_min == time.get()[-4]:
        return

    # gets the weather
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": settings["lat"],
        "longitude": settings["long"],
        "daily": "moon_phase",
        "current": ["temperature_2m", "weather_code", "is_day"],
        "timezone": "America/New_York",
        "temperature_unit": "fahrenheit",
    }
    try:
        response = get(url, params=params)
        data = response.json()
        current = data["current"]
    except:
        return

    # weather code mappings
    moon_phase = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"][round(data["daily"]["moon_phase"][0] * 8) % 8]
    weather_code_map = {
        -1: ("🌡️", "🌡️", ""),
        0:  ("☀️", moon_phase, "Clear"),
        1:  ("🌤️", moon_phase, "Mostly clear"),
        2:  ("⛅", "☁️", "Partly cloudy"),
        3:  ("☁️", "☁️", "Overcast"),
        45: ("🌥️", "🌥️", "Fog"),
        48: ("🌥️", "🌥️", "Freezing fog"),
        51: ("🌦️", "🌧️", "Light drizzle"),
        53: ("🌦️", "🌧️", "Drizzle"),
        55: ("🌧️", "🌧️", "Heavy drizzle"),
        56: ("🌦️", "🌧️", "Freezing drizzle"),
        57: ("🌧️", "🌧️", "Heavy freezing drizzle"),
        61: ("🌦️", "🌧️", "Light rain"),
        63: ("🌧️", "🌧️", "Rain"),
        65: ("🌧️", "🌧️", "Heavy rain"),
        66: ("🌦️", "🌧️", "Freezing rain"),
        67: ("🌧️", "🌧️", "Heavy freezing rain"),
        71: ("🌨️", "🌨️", "Light snow"),
        73: ("🌨️", "🌨️", "Snow"),
        75: ("❄️", "❄️", "Heavy snow"),
        77: ("❄️", "❄️", "Snow grains"),
        80: ("🌦️", "🌧️", "Light showers"),
        81: ("🌧️", "🌧️", "Showers"),
        82: ("⛈️", "⛈️", "Heavy showers"),
        85: ("🌨️", "🌨️", "Snow showers"),
        86: ("❄️", "❄️", "Heavy snow showers"),
        95: ("⛈️", "⛈️", "Storm"),
        96: ("⛈️", "⛈️", "Storm, hail"),
        97: ("⛈️", "⛈️", "Heavy storm"),
        99: ("⛈️", "⛈️", "Severe storm")
    }

    # sets weather
    if current["weather_code"] not in weather_code_map: current["weather_code"] = -1
    weather_emoji.set(weather_code_map[current["weather_code"]][0 if current["is_day"] else 1])
    outside_temp.set(f"{current['temperature_2m']}°F")
    weather_str.set(weather_code_map[current["weather_code"]][2])

# reads the list of apps from the settings file
try:
    with open("settings.json", "r") as f:
        settings = load(f)

# if file doesn't exist create it. key is display name of app, value is the command to run it
except:
    with open("settings.json", "w") as f:
        dump({"lat": 35.2271, "long": -80.8431, "apps": [{"name": "Reboot System", "cmd": {"args": "sudo reboot", "cwd": None}}]}, f, indent=4)
        print("config file created, edit before running again")
        exit(0)

# creates UI elements
updates = 0
root = CTk()
root.geometry("3840x2160")
root.configure(cursor="none")
time = StringVar(root)
date = StringVar(root)
weather_emoji = StringVar(root)
outside_temp = StringVar(root)
weather_str = StringVar(root)
cpu = StringVar(root)
ram = StringVar(root)
cpu_temp = StringVar(root)
disk = StringVar(root)

# creates top section of the UI
top = CTkFrame(root)
top.pack(fill="x", padx=24, pady=24)
top.columnconfigure(1, weight=1)
CTkLabel(top, textvariable=time, font=("Rubik", 64, "bold")).grid(row=0, column=0, sticky="sw", padx=24)
CTkLabel(top, textvariable=date, font=("Rubik", 24)).grid(row=1, column=0, sticky="nw", padx=24)
CTkLabel(top, textvariable=weather_emoji, font=("Rubik", 128)).grid(row=0, column=2, rowspan=2, sticky="e")
CTkLabel(top, textvariable=outside_temp, font=("Rubik", 64, "bold")).grid(row=0, column=3, sticky="sw", padx=24)
CTkLabel(top, textvariable=weather_str, font=("Rubik", 24)).grid(row=1, column=3, sticky="nw", padx=24)

# creates app launcher
CTkLabel(root, text="Services & Apps:", font=("Rubik", 24, "bold")).pack(anchor="w", padx=24)
apps = CTkScrollableFrame(root)
apps.pack(fill="both", expand=True, padx=24)
app_grid = {"active": (0, 0), "status_btns": []}
for i, app in enumerate(settings["apps"]):
    btn = CTkButton(apps, height=150, text=app["name"], font=("Rubik", 64, "bold"), command=lambda cmd=app["cmd"]: launch_app(cmd))
    btn.grid(row=i // 3, column=i % 3, sticky="nsew", padx=12, pady=12)
    app_grid[i // 3, i % 3] = btn

    # adds status functionality to buttons that have a status
    if "status" in app: 
        app_grid["status_btns"].append(btn)
        btn.update_status = lambda b=btn, a=app: b.configure(text=f"{a['name']} {'🔴' if run(**a['status'], shell=True).returncode else '🟢'}")
app_grid[app_grid["active"]].configure(fg_color=app_grid[app_grid["active"]].cget("hover_color"), hover_color=app_grid[app_grid["active"]].cget("fg_color"))

# creates bottom section of the UI
bottom = CTkFrame(root)
bottom.pack(fill="x", padx=24, pady=34)
CTkLabel(bottom, text="CPU", font=("Rubik", 24)).grid(row=0, column=0, pady=(24, 0))
CTkLabel(bottom, text="RAM", font=("Rubik", 24)).grid(row=0, column=1, pady=(24, 0))
CTkLabel(bottom, text="TEMP", font=("Rubik", 24)).grid(row=0, column=2, pady=(24, 0))
CTkLabel(bottom, text="DISK", font=("Rubik", 24)).grid(row=0, column=3, pady=(24, 0))
CTkLabel(bottom, textvariable=cpu, font=("Rubik", 64, "bold")).grid(row=1, column=0, pady=24)
CTkLabel(bottom, textvariable=ram, font=("Rubik", 64, "bold")).grid(row=1, column=1, pady=24)
CTkLabel(bottom, textvariable=cpu_temp, font=("Rubik", 64, "bold")).grid(row=1, column=2, pady=24)
CTkLabel(bottom, textvariable=disk, font=("Rubik", 64, "bold")).grid(row=1, column=3, pady=24)

# final UI setup and starts the program
apps.columnconfigure(0, weight=1, uniform="col")
apps.columnconfigure(1, weight=1, uniform="col")
apps.columnconfigure(2, weight=1, uniform="col")
bottom.columnconfigure(0, weight=1, uniform="col")
bottom.columnconfigure(1, weight=1, uniform="col")
bottom.columnconfigure(2, weight=1, uniform="col")
bottom.columnconfigure(3, weight=1, uniform="col")
set_appearance_mode("dark")
set_default_color_theme("dark-blue")
update_ui()
Thread(target=user_input, daemon=True).start()
root.mainloop()
