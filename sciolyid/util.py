# util.py | assorted utility functions that are standalone
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

import difflib
import functools
import math
import random
from io import BytesIO
from typing import Iterable, Optional

import discord
from PIL import Image


def cache(func=None):
    """Cache decorator based on functools.lru_cache.
    This does not have a max_size and does not evict items.
    In addition, results are only cached by the first provided argument.
    """

    def wrapper(func):
        sentinel = object()

        cache_ = {}
        hits = misses = 0
        cache_get = cache_.get
        cache_len = cache_.__len__

        def _evict():
            """Evicts a random item from the local cache."""
            if len(cache_) > 0:
                cache_.pop(random.choice(tuple(cache_)), 0)

        async def wrapped(*args, **kwds):
            # Simple caching without ordering or size limit
            nonlocal hits, misses
            key = hash(args[0])
            result = cache_get(key, sentinel)
            if result is not sentinel:
                hits += 1
                return result
            misses += 1
            result = await func(*args, **kwds)
            cache_[key] = result
            return result

        def cache_info():
            """Report cache statistics"""
            return functools._CacheInfo(hits, misses, None, cache_len())

        wrapped.cache_info = cache_info
        wrapped.evict = _evict
        return functools.update_wrapper(wrapped, func)

    if func:
        return wrapper(func)
    return wrapper


def black_and_white(input_image_path) -> BytesIO:
    """Returns a black and white version of an image.

    Output type is a file object (BytesIO).

    `input_image_path` - path to image (string) or file object
    """
    with Image.open(input_image_path) as color_image:
        bw = color_image.convert("L")
        final_buffer = BytesIO()
        bw.save(final_buffer, "png")
    final_buffer.seek(0)
    return final_buffer


async def fetch_get_user(user_id: int, ctx=None, bot=None, member: bool = False):
    if (ctx is None and bot is None) or (ctx is not None and bot is not None):
        raise ValueError("Only one of ctx or bot must be passed")
    if ctx:
        bot = ctx.bot
    elif member:
        raise ValueError("ctx must be passed for member lookup")
    if not member:
        return await _fetch_cached_user(user_id, bot)
    if bot.intents.members:
        return ctx.guild.get_member(user_id)
    try:
        return await ctx.guild.fetch_member(user_id)
    except discord.HTTPException:
        return None


@cache()
async def _fetch_cached_user(user_id: int, bot):
    if bot.intents.members:
        return bot.get_user(user_id)
    try:
        return await bot.fetch_user(user_id)
    except discord.HTTPException:
        return None


def prune_user_cache(count: int = 5):
    """Evicts `count` items from the user cache."""
    for _ in range(count):
        _fetch_cached_user.evict()


def spellcheck_list(
    word_to_check: str, correct_list: Iterable[str], abs_cutoff: Optional[int] = None
):
    for correct_word in correct_list:
        if abs_cutoff is None:
            relative_cutoff = math.floor(len(correct_word) / 3)
        else:
            relative_cutoff = abs_cutoff
        if spellcheck(word_to_check, correct_word, relative_cutoff):
            return True
    return False


def spellcheck(worda: str, wordb: str, cutoff: int = 3) -> bool:
    """Checks if two words are close to each other.
    `worda` (str) - first word to compare
    `wordb` (str) - second word to compare
    `cutoff` (int) - allowed difference amount
    """
    worda = worda.lower().replace("-", " ").replace("'", "")
    wordb = wordb.lower().replace("-", " ").replace("'", "")
    shorterword = min(worda, wordb, key=len)
    if worda != wordb:
        if (
            len(list(difflib.Differ().compare(worda, wordb))) - len(shorterword)
            > cutoff
        ):
            return False
    return True


def better_spellcheck(word: str, correct: Iterable[str], options: Iterable[str]) -> bool:
    """Allow lenient spelling unless another answer is closer."""
    matches = difflib.get_close_matches(
        word.lower(), map(str.lower, options), n=1, cutoff=(2 / 3)
    )
    if not matches:
        return False
    if matches[0] in map(str.lower, correct):
        return True
    return False
