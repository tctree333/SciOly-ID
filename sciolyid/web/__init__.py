# __init__.py | pubic module methods
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

from sciolyid import setup as _setup


def setup(*args, **kwargs):
    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]
    kwargs["web"] = True
    _setup(kwargs)


def get_app():
    from sciolyid.web.main import app  # pylint: disable=import-outside-toplevel

    return app
