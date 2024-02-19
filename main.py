import asyncio
from dataclasses import dataclass

import aiohttp
from enum import Enum
from typing import Optional
from datetime import datetime, timedelta

timeout_seconds = timedelta(seconds=15).total_seconds()

'''basic code snippet import'''

class Response(Enum):
    Success = 1
    RetryAfter = 2
    Failure = 3

class ApplicationStatusResponse(Enum):
    Success = 1
    Failure = 2

@dataclass
class ApplicationResponse:

    application_id: str
    status: ApplicationStatusResponse
    description: str
    last_request_time: datetime
    retriesCount: Optional[int]

async def get_application_status1(identifier: str) -> Response:
    async with aiohttp.ClientSession() as session:
        '''exception manage'''
        try:
            '''there is URLs for example, so try to change it to appropriates one in order to test'''
            async with session.get(f'http://service1.com/status/{identifier}', timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as resp:
                if resp.status != 200:
                    raise Exception(f'Unexpected status code: {resp.status}')
                response = await resp.json()
                if response['status'] == 'success':
                    return Response.Success
                elif response['status'] == 'retry':
                    return Response.RetryAfter
                else:
                    raise Exception(f'Unexpected status: {response["status"]}')
        except asyncio.CancelledError:
            raise

        except asyncio.TimeoutError as e:
            print(f'TimeoutError in get_application_status1: {e}')
            return Response.Failure
        except Exception as e:
            print(f'Error in get_application_status1: {e}')
            return Response.Failure

async def get_application_status2(identifier: str) -> Response:
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f'http://service2.com/status/{identifier}', timeout=aiohttp.ClientTimeout(total=timeout_seconds)) as resp:
                if resp.status != 200:
                    raise Exception(f'Unexpected status code: {resp.status}')
                response = await resp.json()
                if response['status'] == 'success':
                    return Response.Success
                elif response['status'] == 'retry':
                    return Response.RetryAfter
                else:
                    raise Exception(f'Unexpected status: {response["status"]}')
        except asyncio.CancelledError:
            raise
        except asyncio.TimeoutError as e:
            print(f'TimeoutError in get_application_status2: {e}')
            return Response.Failure
        except Exception as e:
            print(f'Error in get_application_status2: {e}')
            return Response.Failure

async def perform_operation() -> ApplicationResponse:
    application_id = '123'
    start_time = datetime.now()
    retriesCount = 0

    tasks = [get_application_status1(application_id), get_application_status2(application_id)]
    responses = await asyncio.gather(*tasks)

    status1, status2 = responses
    if status1 == Response.Success and status2 == Response.Success:
        return ApplicationResponse(application_id, ApplicationStatusResponse.Success, "Both services are successful", start_time)
    elif status1 == Response.RetryAfter or status2 == Response.RetryAfter:
        '''as was mentioned, there is asyncio.sleep for waiting before trying again'''
        await asyncio.sleep(5)
        retriesCount += 1
        if retriesCount < 3:
            return await perform_operation()
        else:
            return ApplicationResponse(application_id, ApplicationStatusResponse.Failure, "Retry limit reached", start_time, retriesCount)
    else:
        return ApplicationResponse(application_id, ApplicationStatusResponse.Failure, "One or both services are failed", start_time, retriesCount)

if __name__ == "__main__":
    try:
        asyncio.run(perform_operation())
    except asyncio.CancelledError:
        print('Operation was cancelled')