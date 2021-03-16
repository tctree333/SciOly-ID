# __init__.py | package functions
# Copyright (C) 2019-2021  EraserBird, person_v1.32, hmmm

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
    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]

    for option in config.required:
        try:
            config.options[option] = kwargs[option]
        except KeyError as e:
            raise config.BotConfigError(f"Required setup argument {option}") from e

    for option in tuple(config.optional.keys()) + tuple(config.web_optional.keys()):
        try:
            config.options[option] = kwargs[option]
        except KeyError:
            continue

    if config.options["download_func"] is None:
        for option in config.default_image_required:
            try:
                config.options[option] = kwargs[option]
            except KeyError as e:
                raise config.BotConfigError(f"Required argument {option} if no download function provided") from e

    if kwargs.get("web", None):
        if config.options["download_func"] is not None:
            raise config.BotConfigError("Web cannot be set if a custom download function is set")
        for option in config.web_required:
            try:
                config.options[option] = kwargs[option]
            except KeyError as e:
                raise config.BotConfigError(f"Required web setup argument {option}") from e

    if config.options["category_name"]:
        config.options["id_groups"] = True
        config.options["category_name"] = config.options["category_name"].title()
    else:
        config.options["id_groups"] = False

    directory_config_items = (
        "backups_dir",
        "base_image_url",
        "bot_files_dir",
        "data_dir",
        "download_dir",
        "group_dir",
        "log_dir",
        "state_dir",
        "tmp_upload_dir",
        "validation_local_dir",
        "validation_repo_dir",
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
        "group_dir",
        "meme_file",
        "state_dir",
        "wikipedia_file",
    )
    for item in data_subdirs:
        if config.options[item]:
            config.options[item] = f"{config.options['data_dir']}{config.options[item]}"

    config.options["id_type"] = config.options["id_type"].lower()
    config.options["short_id_type"] = (
        config.options["short_id_type"] or config.options["id_type"][0]
    )

    if kwargs.get("web", None):
        config.options["hashes_url"] = config.options["hashes_url"] or [
            "https://raw.githubusercontent.com/"
            + "/".join(url.split("/")[-2:]).split(".")[0]
            + f"/master/{path}hashes.csv"
            for url, path in (
                (config.options["github_image_repo_url"], ""),
                (
                    config.options["validation_repo_url"],
                    config.options["validation_repo_dir"],
                ),
            )
        ]  # default hashes_url is https://raw.githubusercontent.com/{user}/{repo}/master/hashes.csv

        config.options["ids_url"] = config.options["ids_url"] or [
            "https://raw.githubusercontent.com/"
            + "/".join(url.split("/")[-2:]).split(".")[0]
            + f"/master/{path}ids.csv"
            for url, path in (
                (config.options["github_image_repo_url"], ""),
                (
                    config.options["validation_repo_url"],
                    config.options["validation_repo_dir"],
                ),
            )
        ]  # default ids_url is https://raw.githubusercontent.com/{user}/{repo}/master/{path}ids.csv

        config.options["commit_url_format"] = config.options["commit_url_format"] or [
            "https://github.com/"
            + "/".join(url.split("/")[-2:]).split(".")[0]
            + "/commit/{id}"
            for url in (
                config.options["github_image_repo_url"],
                config.options["validation_repo_url"],
            )
        ]  # default commit_url_format is https://github.com/{user}/{repo}/commit/{id}

        config.options["verification_server"] = (
            config.options["verification_server"] or config.options["support_server"]
        )


def start():
    import sciolyid.start_bot  # pylint: disable=unused-import,import-outside-toplevel
