import json
import random
import time
from typing import Callable, Union

from celery.utils.log import get_task_logger

from sciolyid.web.git import verify_repo
from sciolyid.web.tasks import celery_app, database

logger = get_task_logger(__name__)

GIT_PUSHINFO_FLAGS = (
    "ERROR",  # 1024
    "UP_TO_DATE",  # 512
    "FAST_FORWARD",  # 256
    "FORCED_UPDATE",  # 128
    "DELETED",  # 64
    "REMOTE_FAILURE",  # 32
    "REMOTE_REJECTED",  # 16
    "REJECTED",  # 8
    "NO_MATCH",  # 4
    "NEW_HEAD",  # 2
    "NEW_TAG",  # 1
)
GIT_PUSH_OPCODES = (
    "CHECKING_OUT",  # 256
    "FINDING_SOURCES",  # 128
    "RESOLVING",  # 64
    "RECEIVING",  # 32
    "WRITING",  # 16
    "COMPRESSING",  # 8
    "COUNTING",  # 4
    "END",  # 2
    "BEGIN",  # 1
)


@celery_app.task
def push(commit_message: str, user_id: Union[int, str]):
    logger.info("pushing!")
    index = verify_repo.index
    index.add("*")
    index.commit(commit_message)
    push_result = verify_repo.remote("origin").push(progress=gen_progress(user_id))
    if len(push_result) == 0:
        database.hset(
            f"sciolyid.upload.status:{user_id}",
            mapping={"status": json.dumps(["FAIL"]), "end": int(time.time())},
        )
        logger.error("push operation failed completely!")
    else:
        set_flags = []
        for i, flag in enumerate(f"{push_result[0].flags:0>11b}"):
            if int(flag):
                set_flags.append(GIT_PUSHINFO_FLAGS[i])
        database.hset(
            f"sciolyid.upload.status:{user_id}",
            mapping={"status": json.dumps(set_flags), "end": int(time.time())},
        )
        logger.info(set_flags)
    database.delete(f"sciolyid.upload.save:{user_id}")
    database.expire(f"sciolyid.upload.status:{user_id}", 60)


def gen_progress(user_id: Union[int, str]) -> Callable:
    if isinstance(user_id, int):
        user_id = str(user_id)

    def wrapped_progress(op_code, cur_count, max_count=None, message=""):
        nonlocal user_id
        readable_opcode = {
            GIT_PUSH_OPCODES[i] if int(code) else None
            for i, code in enumerate(f"{op_code:0>9b}")
        }
        readable_opcode.discard(None)
        data = {
            "op_code": json.dumps(list(readable_opcode)),
            "cur_count": json.dumps(cur_count),
            "max_count": json.dumps(max_count),
            "message": json.dumps(message),
        }
        database.hset(f"sciolyid.upload.status:{user_id}", mapping=data)
        if (
            random.randint(1, 4) == 1  # 25%
            or "BEGIN" in readable_opcode
            or "END" in readable_opcode
        ):
            # only log occasionally
            logger.info(data)

    return wrapped_progress
