# core.py | functions for getting media
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

import asyncio
import io
import os
from functools import partial
from typing import Union

import discord

import sciolyid.config as config
import sciolyid.data
from sciolyid.data import GenericError, database, get_category, logger
from sciolyid.util import black_and_white

# Valid file types
valid_image_extensions = {"jpg", "png", "jpeg", "gif"}


async def send_image(ctx, item: str, on_error=None, message=None, bw=False):
    """Gets a picture and sends it to the user.

    `ctx` - Discord context object\n
    `item` (str) - picture to send\n
    `on_error` (function) - async function to run when an error occurs, passes error as argument\n
    `message` (str) - text message to send before picture\n
    """
    if item == "":
        logger.error(f"error - {config.options['id_type'][:-1]} is blank")
        await ctx.send(f"**There was an error fetching {config.options['id_type']}.**")
        if on_error is not None:
            await on_error(GenericError("item is blank", code=100))
        else:
            await ctx.send("*Please try again.*")
        return

    delete = await ctx.send("**Fetching.** This may take a while.")
    # trigger "typing" discord message
    await ctx.trigger_typing()

    try:
        response = await get_image(ctx, item)
    except GenericError as e:
        await delete.delete()
        if e.code == 100:
            await ctx.send("**No images were found.**")
        else:
            await ctx.send(
                f"**An error has occurred while fetching images.**\n**Reason:** {e}"
            )
        logger.exception(e)
        if on_error is not None:
            await on_error(e)
        else:
            await ctx.send("*Please try again.*")
        return

    filename = str(response[0])
    extension = str(response[1])
    stat_info = os.stat(filename)
    if stat_info.st_size > 4000000:  # another filesize check (4mb)
        await delete.delete()
        await ctx.send("**Oops! File too large :(**\n*Please try again.*")
    else:
        file_stream: Union[str, io.BufferedIOBase]
        if bw:
            # prevent the black and white conversion from blocking
            loop = asyncio.get_running_loop()
            fn = partial(black_and_white, filename)
            file_stream = await loop.run_in_executor(None, fn)
        else:
            file_stream = filename

        if message is not None:
            await ctx.send(message)

        # change filename to avoid spoilers
        file_obj = discord.File(file_stream, filename=f"image.{extension}")
        await ctx.send(file=file_obj)
        await delete.delete()


async def get_image(ctx, item):
    """Chooses an image from a list of images.

    This function chooses a valid image to pass to send_image().
    Valid images are based on file extension and size. (8mb discord limit)

    Returns a list containing the file path and extension type.

    `ctx` - Discord context object\n
    `item` (str) - item to get image of\n
    """

    images = await get_files(item)
    logger.info("images: " + str(images))
    prevJ = int(database.hget(f"channel:{ctx.channel.id}", "prevJ").decode("utf-8"))
    # Randomize start (choose beginning 4/5ths in case it fails checks)
    if images:
        j = (prevJ + 1) % len(images)
        logger.info("prevJ: " + str(prevJ))
        logger.info("j: " + str(j))

        for x in range(0, len(images)):  # check file type and size
            y = (x + j) % len(images)
            image_link = images[y]
            extension = image_link.split(".")[-1]
            logger.info("extension: " + str(extension))
            stat_info = os.stat(image_link)
            logger.info("size: " + str(stat_info.st_size))
            if (
                extension.lower() in valid_image_extensions
                and stat_info.st_size < 4000000  # keep files less than 4mb
            ):
                logger.info("found one!")
                break
            if y == prevJ:
                raise GenericError("No Valid Images Found", code=999)

        database.hset(f"channel:{ctx.channel.id}", "prevJ", str(j))
    else:
        raise GenericError("No Images Found", code=100)

    return [image_link, extension]


async def get_files(item, retries=0):
    """Returns a list of image/song filenames.

    This function also does cache management,
    looking for files in the cache for media and
    downloading images to the cache if not found.

    `item` (str) - item to get image of\n
    `retries` (int) - number of attempts completed\n
    """
    logger.info(f"get_files retries: {retries}")
    item = str(item).lower()
    category = get_category(item)
    directory = f"{config.options['download_dir']}{category}/{item}/"
    try:
        logger.info("trying")
        logger.info(f"looking in: {directory}")
        files_dir = os.listdir(directory)
        if not files_dir:
            logger.info("no files in directory")
            raise GenericError("No Files", code=100)
        logger.info("files found!")
        return [f"{directory}{path}" for path in files_dir]
    except (FileNotFoundError, GenericError):
        # if not found, fetch images
        logger.info("fetching files")
        logger.info("item: " + str(item))
        if retries < 3:
            await config.options["download_func"](sciolyid.data, category, item)
            retries += 1
            return await get_files(item, retries)
        logger.info("More than 3 retries")
        return []
