from argparse import ArgumentParser
import json
import vdf

STEAM_CONFIG_FILE = "/home/mikkel/.steam/steam/userdata/10150287/config/localconfig.vdf"

GAMESCOPE_OPTIONS_MAP = {
    "native_width": "-W",
    "native_height": "-H",
    "ingame_width": "-w",
    "ingame_height": "-h",
    "fullscreen": "-f",
}
GAMESCOPE_DEFAULT_VALUES = {
    "-W": 3840,
    "-H": 2160,
    "-w": 3840,
    "-h": 2160,
    "-r": 144,
    "-f": True,
    "--backend": "wayland",
    "--force-grab-cursor": True,
    "--hdr-enabled": True,
}

START_REPLAY_COMMAND = "bash /mnt/h/Misc_Scripts/screen_recorder/start_replay.sh"
STOP_REPLAY_COMMAND = "bash /mnt/h/Misc_Scripts/screen_recorder/stop_replay.sh"
NO_OVERLAY_COMMAND = 'LD_PRELOAD=""'

def parse_gamescope_options(options):
    gamescope_options = {GAMESCOPE_OPTIONS_MAP[option]: options[option] for option in options}
    merged_options = dict(GAMESCOPE_DEFAULT_VALUES)
    merged_options.update(gamescope_options)

    command_list = []
    for key in merged_options:
        value = merged_options[key]
        if isinstance(value, bool):
            command_list.append(key)
        else:
            command_list.append(f"{key} {value}")

    return command_list

def simplify_game_name(game_name):
    return game_name.replace(" ", "_").replace("-", "_").replace(":", "").lower()

if __name__ == "__main__":
    with open("games.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)

    parser = ArgumentParser()
    parser.add_argument("-g", "--game", choices=[simplify_game_name(data["games"][app_id]["name"]) for app_id in data["games"]])
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()

    with open(STEAM_CONFIG_FILE, "r", encoding="utf-8") as fp:
        steam_config_data = vdf.parse(fp)

    for app_id in data["games"]:
        game_options = data["games"][app_id]
        if args.game is not None and simplify_game_name(game_options["name"]) != args.game:
            continue

        command_list = []
        if game_options.get("record", True):
            command_list.extend([START_REPLAY_COMMAND, "&"])

        if not game_options.get("overlay", True):
            command_list.append(NO_OVERLAY_COMMAND)

        if game_options.get("use_gamescope", False) or "gamescope" in game_options:
            gamescope_options = parse_gamescope_options(game_options.get("gamescope", {}))
            command_list.append("gamescope")
            command_list.extend(gamescope_options)
            command_list.append("--")

        if command_list != []:
            command_list.append("%command%")

        if (game_specific_options := game_options.get("game")):
            command_list.extend(game_specific_options)

        if game_options.get("record", True):
            command_list[-1] += ";"
            command_list.append(STOP_REPLAY_COMMAND)

        if args.print:
            print("=" * 5, game_options["name"], "=" * 5)
            print(" ".join(command_list))
            continue

        steam_config_data["UserLocalConfigStore"]["Software"]["Valve"]["Steam"]["apps"][app_id]["LaunchOptions"] = " ".join(command_list)

    if not args.print:
        with open(STEAM_CONFIG_FILE, "w", encoding="utf-8") as fp:
            vdf.dump(steam_config_data, fp, True)
