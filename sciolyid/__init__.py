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
    id_required = config.id_required.keys()
    web_required = config.web_required.keys()
    optional = tuple(config.optional.keys()) + tuple(config.web_optional.keys())

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

    if kwargs.get("web", None):
        for option in web_required:
            try:
                config.options[option] = kwargs[option]
            except KeyError:
                raise config.BotConfigError(f"Required web setup argument {option}")

    if config.options["id_groups"]:
        for option in id_required:
            try:
                config.options[option] = kwargs[option]
            except KeyError:
                raise config.BotConfigError(
                    f"Required setup argument {option} when id_groups is True"
                )
        config.options["category_name"] = config.options["category_name"].title()

    directory_config_items = (
        "backups_dir",
        "base_image_url",
        "bot_files_dir",
        "data_dir",
        "download_dir",
        "list_dir",
        "log_dir",
        "restricted_list_dir",
        "tmp_upload_dir",
        "validation_local_dir",
        "validation_repo_dir",
        "website",
    )
    for item in directory_config_items:
        if config.options[item] and not config.options[item].endswith("/"):
            config.options[item] += "/"

    bot_files_subdirs = (
        "backups_dir",
        "download_dir",
        "log_dir",
        "tmp_upload_dir",
        "validation_local_dir",
    )
    for item in bot_files_subdirs:
        if config.options[item]:
            config.options[
                item
            ] = f"{config.options['bot_files_dir']}{config.options[item]}"

    data_subdirs = (
        "alias_file",
        "list_dir",
        "meme_file",
        "restricted_list_dir",
        "wikipedia_file",
    )
    for item in data_subdirs:
        if config.options[item]:
            config.options[item] = f"{config.options['data_dir']}{config.options[item]}"

    config.options["id_type"] = config.options["id_type"].lower()
    config.options["short_id_type"] = (
        config.options["short_id_type"] or config.options["id_type"][0]
    )

    config.options["hashes_url"] = (
        config.options["hashes_url"]
        or "https://raw.githubusercontent.com/"
        + "/".join(config.options["github_image_repo_url"].split("/")[-2:]).split(".")[
            0
        ]
        + "/master/hashes.csv"
    )  # default hashes_url is https://raw.githubusercontent.com/{user}/{repo}/master/hashes.csv


def start():
    import sciolyid.start_bot  # pylint: disable=unused-import
