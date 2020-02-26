import sciolyid.config as config

def setup(**kwargs):
    required = config.required.keys()
    optional = config.optional.keys()
    id_required = config.id_required.keys()

    for option in required:
        try:
            config.options[option] = kwargs[option]
        except KeyError:
            raise config.BotConfigError(f"Error: Required setup argument {option}")

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
                raise config.BotConfigError(f"Error: Required setup argument {option} when ID_GROUPS is True")

    if config.options['file_folder'] and config.options['file_folder'][-1] != "/":
        config.options['file_folder'] += "/"

    if config.options['data_dir'] and config.options['data_dir'][-1] != "/":
        config.options['data_dir'] += "/"

    config.options["log_dir"] = f"{config.options['file_folder']}{config.options['log_dir']}"
    config.options["download_dir"] = f"{config.options['file_folder']}{config.options['download_dir']}"

    config.options["list_dir"] = f"{config.options['data_dir']}{config.options['list_dir']}"
    config.options["wikipedia_file"] = f"{config.options['data_dir']}{config.options['wikipedia_file']}"
    config.options["alias_file"] = f"{config.options['data_dir']}{config.options['alias_file']}"

def start():
    import sciolyid.start_bot  # pylint: disable=unused-import
