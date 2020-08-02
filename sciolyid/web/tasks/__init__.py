import os

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

worker = celery.bin.worker.worker(app=celery_app)

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
