from fastapi import Request

from pipeline.lake.client import LakeClient


def get_lake(request: Request) -> LakeClient:
    lake_client: LakeClient = request.app.state.lake_client
    return lake_client
