# tasks/__init__.py | Celery config and module methods
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

import os

import celery.bin.beat
import celery.bin.worker
import redis
from celery import Celery

import sciolyid.config as config

database = redis.from_url(os.environ[config.options["celery_broker_env"]])

celery_app = Celery(
    "sciolyid.web.tasks",
    broker=os.environ[config.options["celery_broker_env"]],
    # backend=os.environ[config.options["celery_broker_env"]],
    include=("sciolyid.web.tasks.git_tasks"),
)

CHECK_INTERVAL = 60 * 15
celery_app.conf.beat_schedule = {
    "update_repos": {
        "task": "sciolyid.web.tasks.git_tasks.move_images",
        "schedule": CHECK_INTERVAL,
        "args": tuple(),
    },
}


worker = celery.bin.worker.worker(app=celery_app)
beat = celery.bin.beat.beat(app=celery_app)


def run_worker(args: list):
    worker.run_from_argv("celery", args, "worker")


def run_beat(args: list):
    beat.run_from_argv(
        "celery",
        args
        + [
            f"--schedule={config.options['bot_files_dir']}celerybeat-schedule",
            f"--max-interval={CHECK_INTERVAL + 10}",
        ],
        "beat",
    )


### Database communication definitions ###

# sciolyid.upload.save:{user_id} = 1  # set if save in progress
# sciolyid.upload.status:{user_id} = {
#     start:  # start time
#     end:  # end time, 0 if in progress
#     opcode: op_code  # human readable
#     cur_count: cur_count
#     max_count: max_count
#     message: message
#     status:  # "IN_PROGRESS" during, push result flags after
# }


# sciolyid.verify.images:valid = {  # sorted set
#     image_id: num of times
# }
# sciolyid.verify.images:invalid = {  # sorted set
#     image_id: num of times
# }
# sciolyid.verify.images:duplicate = {  # sorted set
#     image_id: num of times
# }

# sciolyid.verify.user:{user_id} = [  # set
#     image_id...
# ]
