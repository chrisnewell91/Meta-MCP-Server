import asyncio
from datetime import datetime, timedelta

from meta_mcp_server.pooling import ServerPool


def test_reuses_idle_server():
    async def run_scenario():
        pool = ServerPool()
        pool.idle_threshold_seconds = 5
        created_ids = []

        async def create_server():
            server_id = f"srv-{len(created_ids)}"
            created_ids.append(server_id)
            return {"server_id": server_id, "status": "created and running"}

        first = await pool.get_or_create_server(
            template="basic", create_server=create_server
        )

        assert first["reused"] is False
        pool.mark_server_idle(first["server_id"])

        second = await pool.get_or_create_server(
            template="basic", create_server=create_server
        )

        assert second["reused"] is True
        assert second["server_id"] == first["server_id"]

    asyncio.run(run_scenario())


def test_cleanup_idle_servers_removes_expired():
    async def run_scenario():
        pool = ServerPool()
        pool.idle_threshold_seconds = 0.1
        stopped = []

        async def create_server():
            return {"server_id": "srv-cleanup", "status": "created and running"}

        async def stop_callback(server_id: str):
            stopped.append(server_id)

        created = await pool.get_or_create_server(
            template="basic", create_server=create_server
        )
        pool.mark_server_idle(created["server_id"])

        pool.pool["basic"][0]["last_used"] = datetime.utcnow() - timedelta(seconds=0.2)

        removed = await pool.cleanup_idle_servers(stop_callback=stop_callback)

        assert removed == 1
        assert stopped == [created["server_id"]]
        assert pool.pool == {}
        assert pool.server_metadata == {}

    asyncio.run(run_scenario())
