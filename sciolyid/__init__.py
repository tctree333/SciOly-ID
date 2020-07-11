# __init__.py | package functions
# Copyright (C) 2019-2020  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sciolyid.config as config


def setup(*args, **kwargs):
    required = config.required.keys()
    optional = config.optional.keys()
    id_required = config.id_required.keys()

    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]

    for option in required:
        try:
            config.options[option] = kwargs[option]
        except KeyError:
            raise config.BotConfigError(f"Required setup argument {option}")

    for option in optional:
        try:
            config.options[option] = kwargs[option]
        except KeyError:
            continue

    if config.options["id_groups"]:
        for option in id_required:
            try:
                config.options[option] = kwargs[option]
            except KeyError:
                raise config.BotConfigError(
                    f"Required setup argument {option} when id_groups is True"
                )
        config.options["category_name"] = config.options["category_name"].title()

    if config.options["bot_files_dir"] and not config.options["bot_files_dir"].endswith("/"):
        config.options["bot_files_dir"] += "/"

    if config.options["data_dir"] and not config.options["data_dir"].endswith("/"):
        config.options["data_dir"] += "/"

    if config.options["backups_dir"] and not config.options["backups_dir"].endswith("/"):
        config.options["backups_dir"] += "/"

    if config.options["download_dir"] and not config.options["download_dir"].endswith("/"):
        config.options["download_dir"] += "/"

    if config.options["list_dir"] and not config.options["list_dir"].endswith("/"):
        config.options["list_dir"] += "/"

    if config.options["restricted_list_dir"] and not config.options[
        "restricted_list_dir"
    ].endswith("/"):
        config.options["restricted_list_dir"] += "/"

    if config.options["log_dir"] and not config.options["log_dir"].endswith("/"):
        config.options["log_dir"] += "/"

    config.options["log_dir"] = f"{config.options['bot_files_dir']}{config.options['log_dir']}"
    config.options[
        "download_dir"
    ] = f"{config.options['bot_files_dir']}{config.options['download_dir']}"
    config.options[
        "backups_dir"
    ] = f"{config.options['bot_files_dir']}{config.options['backups_dir']}"

    config.options["list_dir"] = f"{config.options['data_dir']}{config.options['list_dir']}"

    if config.options["restricted_list_dir"]:
        config.options[
            "restricted_list_dir"
        ] = f"{config.options['data_dir']}{config.options['restricted_list_dir']}"

    config.options[
        "wikipedia_file"
    ] = f"{config.options['data_dir']}{config.options['wikipedia_file']}"
    config.options[
        "alias_file"
    ] = f"{config.options['data_dir']}{config.options['alias_file']}"
    if config.options["meme_file"]:
        config.options[
            "meme_file"
        ] = f"{config.options['data_dir']}{config.options['meme_file']}"

    config.options["id_type"] = config.options["id_type"].lower()

    config.options["short_id_type"] = (
        config.options["short_id_type"] or config.options["id_type"][0]
    )


def start():
    import sciolyid.start_bot  # pylint: disable=unused-import
