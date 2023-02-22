from __future__ import annotations

import asyncio
import logging
import random

from fastapi import FastAPI

from standard_structlog import ExecutionLogContext, formatter, getLogger, output, setup

app = FastAPI()

setup(
    level=logging.INFO,
    outputs=(output.Stream(formatter=formatter.DATADOG_FORMATTER),),
)

logger = getLogger(__name__)


async def sub():
    logger.info("log from sub")
    await asyncio.sleep(0.1)


@app.get("/")
async def root():
    kwargs = {f"foo{random.randint(0, 1000000000)}": "x" * 100000}
    ExecutionLogContext.add(**kwargs)
    await sub()
    logger.info("log from root")
    return {"Hello": "World"}
