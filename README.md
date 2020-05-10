# SciOly-ID-Discord-Bots

A template for creating Discord Bots to study for Science Olympiad ID events.

## Usage

_Note: Some steps in this tutorial assume a Linux/Mac environment._

To setup your own bot, follow these steps:

1. Create a new folder and install SciOly-ID.

    SciOly-ID can be installed with pip:

    `pip install -U sciolyid`

    Or you can install the latest version of the code from git:
    `pip install -U git+git://github.com/tctree333/SciOly-ID.git`

2. Setup your bot by calling `sciolyid.setup` and passing in your config options as arguments:

    ```python
    import sciolyid
    sciolyid.setup(...)
    ```

    For examples of configs, see the [examples section](#examples). Here is a list of config options:

    #### Required

    - `bot_description` - This is a description of the Discord bot.
    - `bot_signature` - This is what is displayed at the top of an embed. This is also a short description of the bot.
    - `prefixes` - This is what is used to call your bot. The first item of the list will be used when giving example commands. Having different cased versions of your prefix may be helpful to mobile users, along with having a prefix with only letters and periods.
    - `id_type` - This is a plural noun that describes what you are IDing.
    - `github_image_repo_url` - This is a link to the GitHub repo hosting your images, which we will create later.
    - `support_server` - This is the link to the Discord server that will act as a support server.
    - `source_link` - This is the link to the GitHub repo hosting your code.

    #### Optional

    - `name` - It doesn't really matter what this is, basically an id for your bot.
    - `invite` - This is a Discord link that lets people invite your bot to a server.
    - `authors` - Put your name/username here. Credit people for their part in the bot's creation.
    - `id_groups` - Set this to `True` if you want to categorize the items. Possible categories include taxons for birds/fossils, muscle groups for anatomy, or categories of space objects for astronomy.
    - `category_name` - This is what you are splitting your categories by. _This is required if `id_groups` is `True`._
    - `category_aliases` - This is a dict of different aliases your categories may go by for ease of use. You do not need to put all your categories here, only if it has an alias.

3. Create a new file called `setup.sh`:

```sh
#!/bin/sh
export token=
```

This will be used to store environment variables. We will fill these in later. **Put this in `.gitignore` if you have a public github repo.**

4. Now we need to add the lists. Create a new directory(pass this in to the setup function as `data_dir`) and create a new file called whatever you're IDing. For example, a fossils bot would have a list called `fossils.txt`. If you have categories, create a file for each category. Fill in these files with the lists, one per line.
5. If some items in the list can go by a different name, you can create a new file called `aliases.txt`. Input your aliases one per line, with the name in the other list as the first item.
6. Now, input the links to the wikipedia pages for each item in a new file called `wikipedia.txt`. You can manually enter them in, making sure the name matches the items in the other list. You can also run `python -m sciolyid.scripts.generate_wiki` a few times to generate the list for you. You will still have to manually go through to ensure the correct link was found.
7. Register a bot account on the [Discord Developers Portal](https://discord.com/developers/applications/). To do so, create a new application. Name your application, then navigate to the `Bot` section, and add a bot. Change your application name if necessary. Update `setup.sh` with your bot token (`Bot` section), and Discord user id. You can also generate your bot invite link. Go to the `OAuth2` section and check `bot` in the `Scopes` section. In the `Bot Permissions` secion, check `Send Messages`, `Embed Links`, and `Attach Files`. Copy the URL generated and update your config options.
8. Great! Now we will need to add images. Create a new GitHub repository to host your images [here](https://github.com/new).

This next step will be the most difficult to do online, though it is possible. See the [Adding Pictures](#adding-pictures) section below for more info.

9. You will need to upload at least one picture of each item on the list, but more is definitely reccomended. These will be the pictures you see when using the bot, so more variety and more pictures is better. Get some friends to help out. The repository structure should be `category_name/item_name/image_name`. Images should be smaller than 8MB and in a `.png`, `.jpg`, or `.jpeg` format. You can see examples in the [example section](#examples). To quickly create the directory structure, run`python -m sciolyid.scripts.generate_file_structure`.

Once you have all of this set up, it's now time to run your bot.

10. Install a local Redis server by running [install-redis.sh](https://github.com/tctree333/Fossil-ID/blob/master/install-redis.sh). Start your Redis server with `python -m sciolyid.scripts.install_redis`. [Source](https://redis.io/topics/quickstart)
11. You are now ready to run the application! Setup the environment with `source setup.sh`. Start the bot by calling the python file.

**Congrats! You just created your own ID Discord bot.** Add your bot to the Discord server of your choice using the invite link generated in step 6.

If there are any issues or you have any questions, let us know in the Bird-ID [Discord support server.](https://discord.gg/xDqYddK)

## Examples

-   **Reach for the Stars ID Bot** - [https://github.com/tctree333/Reach-For-The-Stars-Bot]
-   **Reach for the Stars ID Bot Images** - [https://github.com/tctree333/Reach-For-The-Stars-Images]
-   **Fossils ID Bot** - [https://github.com/tctree333/Fossil-ID]
-   **Fossils ID Images** - [https://github.com/tctree333/Fossil-Bot-Images]
-   **Bird-ID** - [https://github.com/tctree333/Bird-ID] (doesn't use this template, more advanced)

## Hosting

There are many options for hosting a bot, you can run it on your own computer, run it on a Raspberry Pi, or find cloud hosting options. This repo is setup to use Heroku like Bird-ID, but there are drawbacks as Heroku is fairly underpowered and will restart your bot once a day. If you are planning to use Heroku, you will want to use their cloud Redis databases. See Bird-ID for the code.

## Adding Pictures

If you're new to Git and GitHub, an easy way to get started is with GitHub Desktop.

1. Create a GitHub account if you haven't already.
2. Install GitHub Desktop [here](https://desktop.github.com/). Open it.
3. Log in with your GitHub account. Follow the tutorial [here](https://help.github.com/en/desktop/contributing-to-projects/cloning-and-forking-repositories-from-github-desktop) to clone and fork this repository. When you get to step 2, use `"URL"` instad of `GitHub.com` with the url `https://github.com/tctree333/Fossil-Bot-Images.git`. Note the generated `Local Path`. Continue as normal.
4. In your file explorer on your computer, navigate to the generated path. Now you are ready to add images! Drag and drop downloaded images to the appropriate folder, ensuring that images meet the requirements above and deleting `"image.placeholder"` if the folder is not empty. However, if the folder does _not_ have images, **do not delete** `"image.placeholder"`.
5. Once you are done adding as many pictures as you want, go back to GitHub Desktop and click `"create a fork"` in the bottom left corner. Fork the repository, and hit `"Commit to master"` in the bottom left corner. Then, hit `"Push Origin"`.
6. Finally, hit `"View on GitHub"` and click `"Pull Request"` near the middle right. Click `"Create Pull Request"`, give it a name and description if you want, and then `"Create Pull Request"`.

Congrats! You just helped add images to the bot! Give me a few days to approve your pull request, and the bot will be using your new images. You don't have to stop here, though. Add more pictures by repeating steps 4-6, though you may have to click `"Fetch Origin"` occasionally to make sure your copy is up to date.

**Thanks for helping out!**

## Contributing

Run the following commands to install a development version:

```sh
git clone https://github.com/tctree333/SciOly-ID.git
cd SciOly-ID
pip install -U .
```
