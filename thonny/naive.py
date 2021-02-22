from hashlib import sha256
from thonny import SOFTWARE_NAME, SOFTWARE_UPPERCASE_NAME, SOFTWARE_LOWERCASE_NAME
from typing import List, Optional
import asyncio
import httpx
import uuid
import wmi
import time
import json
import urllib

MatomoOrigin = "http://localhost"
wmic = wmi.WMI()


def StandardizeStringIDList(OriginalList: List[Optional[str]]):
    return sorted(set(map(lambda s: s.upper().strip(), filter(lambda o: o, OriginalList))))


def IntToMACAddress(IntMACAddress: int):
    return ":".join("{:012X}".format(IntMACAddress)[i : i + 2] for i in range(0, 12, 2))


DeviceUIDData = {
    "MACAddress": StandardizeStringIDList([IntToMACAddress(uuid.getnode())]),
    "Processor": StandardizeStringIDList(map(lambda o: o.ProcessorId, wmic.Win32_Processor())),
    "BaseBoard": StandardizeStringIDList(map(lambda o: o.SerialNumber, wmic.Win32_BaseBoard())),
    "BIOS": StandardizeStringIDList(map(lambda o: o.SerialNumber, wmic.Win32_BIOS())),
    "DiskDrive": StandardizeStringIDList(map(lambda o: o.SerialNumber, wmic.Win32_DiskDrive())),
    "NetworkAdapter": StandardizeStringIDList(
        map(lambda o: o.MACAddress, wmic.Win32_NetworkAdapter())
    ),
}
DeviceUIDSeed: str = (
    "".join(
        [
            "".join(sorted(DeviceUIDData["MACAddress"])),
            "".join(sorted(DeviceUIDData["Processor"])),
            "".join(sorted(DeviceUIDData["BaseBoard"])),
            "".join(sorted(DeviceUIDData["BIOS"])),
            "".join(sorted(DeviceUIDData["DiskDrive"])),
            "".join(sorted(DeviceUIDData["NetworkAdapter"])),
        ]
    )
    .replace(" ", "")
    .replace(":", "")
    .upper()
    .strip()
)
NaiveMatomoUID: str = sha256(DeviceUIDSeed.encode("utf-8")).hexdigest()[-16:]


async def AsyncSendToMatomo(retry="always"):
    print("Device UID Data: ", json.dumps(DeviceUIDData, indent=2))
    print("Device UID Seed: ", DeviceUIDSeed)
    print("NaiveMatomoUID: ", NaiveMatomoUID)
    DeviceUIDDataInMatomoFormat = [
        ["MACAddress", DeviceUIDData["MACAddress"]],
        ["Processor", DeviceUIDData["Processor"]],
        ["BaseBoard", DeviceUIDData["BaseBoard"]],
        ["BIOS", DeviceUIDData["BIOS"]],
    ]
    DeviceUIDDataInMatomoFormat = {
        "1": ["MACAddress", DeviceUIDData["MACAddress"][0]],
    }
    print("DeviceUIDDataInMatomoFormat: ", json.dumps(DeviceUIDDataInMatomoFormat, indent=2))
    success: bool = False
    while not success:
        async with httpx.AsyncClient() as HttpXClient:
            MatomoEndpoint = MatomoOrigin + "/matomo.php"
            MatomoData = dict(
                {
                    "idsite": "1",
                    "rec": "1",
                    "action_name": "OpenThonny",
                    "_id": NaiveMatomoUID,
                    "apiv": "1",
                    "url": "device-uid://"
                    + NaiveMatomoUID
                    + "/?data="
                    + json.dumps(DeviceUIDData, separators=(",", ":")),
                    "_cvar": json.dumps(
                        DeviceUIDDataInMatomoFormat, separators=(",", ":")
                    ),  # doesn't work
                    "dimension1": DeviceUIDData["MACAddress"][0],  # doesn't work either
                },
            )
            print("MatomoEndpoint: ", MatomoEndpoint)
            print("MatomoData: ", MatomoData)
            print("urlencode: ", urllib.parse.urlencode(MatomoData))
            Response = await HttpXClient.post(MatomoEndpoint, data=MatomoData)
            print("Response: ", Response)
            if Response.status_code == httpx.codes.OK:
                success = True
        if success:
            break
        if retry != "always":
            break
        time.sleep(300)  # 5 minutes


def SendToMatomo(retry="always"):
    asyncio.run(AsyncSendToMatomo(retry))
