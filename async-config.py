#!/usr/bin/env python3
import asyncio
from getpass import getpass
from pathlib import Path
from typing import Any, Dict, List, Tuple

from scrapli import AsyncScrapli
from scrapli.exceptions import ScrapliAuthenticationFailed
from scrapli.logging import enable_basic_logging

enable_basic_logging(file=True, level="debug")

MAX_CONNECTIONS = 10
LOCAL_USER = input("enter local username: ")
LOCAL_PASS = getpass("enter local password: ")
AD_USER = input("enter ad username: ")
AD_PASS = getpass("enter ad password: ")
ENABLE_PASS = getpass("enter enable password: ")
INV_FILE = input("enter name of inventory file: ")
CONFIG_FILE = input("enter name of configuration file: ")

def load_devices() -> List[Dict[str, Any]]:
    with open(INV_FILE, "r") as f:
        devices = f.read().splitlines()

    return [
        {
            "host": device,
            "auth_strict_key": False,
            "platform": "cisco_iosxe",
            "transport": "asyncssh",
            "transport_options": {
                "open_cmd": ["-o", "KexAlgorithms=+diffie-hellman-group14-sha1"]
            },
            # ignore this, for local test setup
            "port": 22,
        }
        for device in devices
    ]


async def device_deploy(conn: AsyncScrapli) -> Tuple[str, str, str]:
    host = conn.host
    log_file = f"./logs/skipped_{host}.log"
    log_msg = "skipping due to auth failure"
    stdout_msg = f"Auth failure on {host}, it's possible this is already configure for AAA...skipping device"

    try:
        await conn.open()
        print("Connection succeeded.")
    except ScrapliAuthenticationFailed as exc:
        pass
    else:
        multi_response = await conn.send_configs_from_file(
            file=CONFIG_FILE, stop_on_failed=True
        )
        log_msg = multi_response.result

        if multi_response.failed is True:
            log_file = f"./logs/failed_{host}.log"
            stdout_msg = f"Config failed on {host}. Please check logs file."
        else:
            log_file = f"./logs/success_{host}.log"
            stdout_msg = f"Config succeeded on {host}"

        await conn.close()

    return stdout_msg, log_file, log_msg


async def device_validate(conn: AsyncScrapli) -> Tuple[str, str, str]:
    host = conn.host
    log_file = f"./logs/validate_success_{host}.log"
    stdout_msg = f"validation succeeded on {host}"
    log_msg = stdout_msg

    try:
        await conn.open()
        print("Connection succeeded.")
    except ScrapliAuthenticationFailed as exc:
        log_file = f"./logs/validate_failed_{host}.log"
        stdout_msg = f"failed logging back into host, aaa must have failed?"
        log_msg = stdout_msg
    else:
        response = await conn.send_command(command="show version")
        log_msg = response.result

        if response.failed is True:
            log_file = f"./logs/validate_failed_{host}.log"
            stdout_msg = f"failed exucting show command on host, aaa must have failed?"

        await conn.close()

    return stdout_msg, log_file, log_msg


async def device_interaction(
    device: Dict[str, Any], semaphore: asyncio.Semaphore, deploy: bool = True
) -> None:
    auth_username = LOCAL_USER if deploy is True else AD_USER
    auth_password = LOCAL_PASS if deploy is True else AD_PASS
    interaction_coro = device_deploy if deploy is True else device_validate

    async with semaphore:
        print(f'CONFIGURING HOST {device["host"]} ...')
        conn = AsyncScrapli(
            **device, auth_username=auth_username, auth_password=auth_password,auth_secondary=ENABLE_PASS
        )
        stdout_msg, log_file, log_msg = await interaction_coro(conn=conn)

    print(stdout_msg)
    with open(log_file, "w+") as f:
        f.write(log_msg)


async def main() -> None:
    Path("./logs").mkdir(exist_ok=True)

    devices = load_devices()
    semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

    print("First we are going to deploy stuff.")
    await asyncio.gather(
        *[
            device_interaction(device=device, semaphore=semaphore, deploy=True)
            for device in devices
        ]
    )
    print("Next we are going to validate login with AD credentials.")
    await asyncio.gather(
        *[
            device_interaction(device=device, semaphore=semaphore, deploy=False)
            for device in devices
        ]
    )
    print("All done!")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
