"""Integration tests for optimized dashboard endpoints.

This module tests the dashboard API endpoints with focus on:
- Optimized statistics endpoint
- Caching behavior
- Performance improvements
- Response format

Features:
    - Full stack testing (HTTP → Service → Repository → Database)
    - Cache behavior validation
    - Performance benchmarking
    - Authentication testing
"""

import time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories.user_factory import create_user_create_schema

pytestmark = pytest.mark.asyncio


class TestDashboardStatsEndpoint:
    """Tests for GET /api/v1/dashboard/stats endpoint."""

    async def test_get_stats_success(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
        test_superuser,
    ):
        """Test successful stats retrieval."""
        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_users" in data
        assert "active_users" in data
        assert "inactive_users" in data
        assert "superusers" in data
        assert "new_users_today" in data
        assert "new_users_week" in data
        assert "timestamp" in data

        # Verify data types
        assert isinstance(data["total_users"], int)
        assert isinstance(data["active_users"], int)
        assert isinstance(data["inactive_users"], int)
        assert isinstance(data["superusers"], int)
        assert isinstance(data["new_users_today"], int)
        assert isinstance(data["new_users_week"], int)
        assert isinstance(data["timestamp"], str)

    async def test_get_stats_requires_superuser(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test that regular users cannot access stats."""
        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_get_stats_requires_authentication(self, client: AsyncClient):
        """Test that unauthenticated users cannot access stats."""
        response = await client.get("/api/v1/dashboard/stats")

        assert response.status_code == 401

    async def test_get_stats_with_multiple_users(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test stats with multiple users."""
        from app.services.user import UserService

        user_service = UserService(db_session)

        # Create 5 active users
        for i in range(5):
            user_in = create_user_create_schema(
                email=f"user{i}@example.com",
                username=f"user{i}",
            )
            await user_service.create_user(user_in)

        # Create 2 inactive users
        for i in range(2):
            user_in = create_user_create_schema(
                email=f"inactive{i}@example.com",
                username=f"inactive{i}",
            )
            user = await user_service.create_user(user_in)
            user.is_active = False
            await db_session.commit()

        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify counts (including test_superuser from fixture)
        assert data["total_users"] >= 8
        assert data["active_users"] >= 6
        assert data["inactive_users"] >= 2

    async def test_get_stats_response_format(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
    ):
        """Test that response format matches specification."""
        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all required fields
        required_fields = [
            "total_users",
            "active_users",
            "inactive_users",
            "superusers",
            "new_users_today",
            "new_users_week",
            "timestamp",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

        # Verify no extra fields
        assert set(data.keys()) == set(required_fields)

    async def test_get_stats_performance(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that stats endpoint is fast."""
        from app.services.user import UserService

        user_service = UserService(db_session)

        # Create 50 users (scaled down for test speed)
        for i in range(50):
            user_in = create_user_create_schema(
                email=f"perf{i}@example.com",
                username=f"perf{i}",
            )
            await user_service.create_user(user_in)

        # Measure response time
        start_time = time.time()
        response = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )
        response_time = time.time() - start_time

        assert response.status_code == 200

        # Verify response time is reasonable
        # Should be < 1 second even with 50 users
        # With 10,000+ users, should be < 100ms
        assert response_time < 1.0, f"Response took {response_time}s"

    async def test_get_stats_caching_behavior(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that stats are cached properly."""
        # First request - should hit database
        response1 = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        timestamp1 = data1["timestamp"]

        # Second request immediately - should hit cache
        response2 = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        timestamp2 = data2["timestamp"]

        # Timestamps should be identical (cached response)
        assert timestamp1 == timestamp2
        assert data1 == data2

    async def test_get_stats_cache_performance(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
    ):
        """Test that cached responses are faster."""
        # First request - uncached
        start_time1 = time.time()
        response1 = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )
        time1 = time.time() - start_time1

        assert response1.status_code == 200

        # Second request - cached
        start_time2 = time.time()
        response2 = await client.get(
            "/api/v1/dashboard/stats",
            headers=superuser_auth_headers,
        )
        time2 = time.time() - start_time2

        assert response2.status_code == 200

        # Cached request should be faster (or at least not slower)
        # Note: In tests with in-memory cache, difference may be minimal
        assert time2 <= time1 * 2  # Allow some variance

    async def test_get_stats_consistency(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that stats are consistent across multiple calls."""
        from app.services.user import UserService

        user_service = UserService(db_session)

        # Create some users
        for i in range(10):
            user_in = create_user_create_schema(
                email=f"consistent{i}@example.com",
                username=f"consistent{i}",
            )
            await user_service.create_user(user_in)

        # Get stats multiple times
        responses = []
        for _ in range(3):
            response = await client.get(
                "/api/v1/dashboard/stats",
                headers=superuser_auth_headers,
            )
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should have same counts (cached)
        for i in range(1, len(responses)):
            assert responses[i]["total_users"] == responses[0]["total_users"]
            assert responses[i]["active_users"] == responses[0]["active_users"]
            assert responses[i]["inactive_users"] == responses[0]["inactive_users"]
            assert responses[i]["superusers"] == responses[0]["superusers"]


class TestDashboardMainEndpoint:
    """Tests for GET /api/v1/dashboard/ endpoint."""

    async def test_get_dashboard_success(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
    ):
        """Test successful dashboard page retrieval."""
        response = await client.get(
            "/api/v1/dashboard/",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        # Response should be HTML
        assert "text/html" in response.headers["content-type"]

    async def test_get_dashboard_requires_superuser(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test that regular users cannot access dashboard."""
        response = await client.get(
            "/api/v1/dashboard/",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_get_dashboard_requires_authentication(self, client: AsyncClient):
        """Test that unauthenticated users cannot access dashboard."""
        response = await client.get("/api/v1/dashboard/")

        assert response.status_code == 401

    async def test_get_dashboard_uses_optimized_service(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
        db_session: AsyncSession,
    ):
        """Test that dashboard page uses optimized service."""
        from app.services.user import UserService

        user_service = UserService(db_session)

        # Create multiple users
        for i in range(20):
            user_in = create_user_create_schema(
                email=f"dash{i}@example.com",
                username=f"dash{i}",
            )
            await user_service.create_user(user_in)

        # Measure response time
        start_time = time.time()
        response = await client.get(
            "/api/v1/dashboard/",
            headers=superuser_auth_headers,
        )
        response_time = time.time() - start_time

        assert response.status_code == 200

        # Should be fast even with multiple users
        assert response_time < 2.0, f"Dashboard took {response_time}s"


class TestDashboardDataEntryEndpoint:
    """Tests for GET /api/v1/dashboard/data-entry endpoint."""

    async def test_get_data_entry_success(
        self,
        client: AsyncClient,
        superuser_auth_headers: dict,
    ):
        """Test successful data entry form retrieval."""
        response = await client.get(
            "/api/v1/dashboard/data-entry",
            headers=superuser_auth_headers,
        )

        assert response.status_code == 200
        # Response should be HTML
        assert "text/html" in response.headers["content-type"]

    async def test_get_data_entry_requires_superuser(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test that regular users cannot access data entry."""
        response = await client.get(
            "/api/v1/dashboard/data-entry",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_get_data_entry_requires_authentication(self, client: AsyncClient):
        """Test that unauthenticated users cannot access data entry."""
        response = await client.get("/api/v1/dashboard/data-entry")

        assert response.status_code == 401


'''
============== 1 failed, 4 passed, 11 errors in 74.60s (0:01:14) ==============
ERROR [  6%][ERROR] Commit failed: IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: users.username
[SQL: INSERT INTO users (email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id]
[parameters: ('admin@example.com', 'admin', '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO', 'Admin User', 1, 0, '2025-11-24 05:04:22.241513', '2025-11-24 05:04:22.241513')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
Traceback (most recent call last):
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py", line 180, in execute
    self._adapt_connection._handle_exception(error)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py", line 340, in _handle_exception
    raise error
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py", line 162, in execute
    self.await_(_cursor.execute(operation, parameters))
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\cursor.py", line 40, in execute
    await self._execute(self._cursor.execute, sql, parameters)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\cursor.py", line 32, in _execute
    return await self._conn._execute(fn, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\core.py", line 122, in _execute
    return await future
           ^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\core.py", line 105, in run
    result = function()
             ^^^^^^^^^^
sqlite3.IntegrityError: UNIQUE constraint failed: users.username

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\app\services\base.py", line 45, in commit
    await self.db.commit()
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\ext\asyncio\session.py", line 1000, in commit
    await greenlet_spawn(self.sync_session.commit)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 203, in greenlet_spawn
    result = context.switch(value)
             ^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 2030, in commit
    trans.commit(_to_root=True)
  File "<string>", line 2, in commit
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 137, in _go
    ret_value = fn(self, *arg, **kw)
                ^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 1311, in commit
    self._prepare_impl()
  File "<string>", line 2, in _prepare_impl
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 137, in _go
    ret_value = fn(self, *arg, **kw)
                ^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 1286, in _prepare_impl
    self.session.flush()
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4331, in flush
    self._flush(objects)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4466, in _flush
    with util.safe_reraise():
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4427, in _flush
    flush_context.execute()
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py", line 466, in execute
    rec.execute(self)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py", line 642, in execute
    util.preloaded.orm_persistence.save_obj(
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\persistence.py", line 93, in save_obj
    _emit_insert_statements(
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\orm\persistence.py", line 1233, in _emit_insert_statements
    result = connection.execute(
             ^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1419, in execute
    return meth(
           ^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\sql\elements.py", line 526, in _execute_on_connection
    return connection._execute_clauseelement(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1641, in _execute_clauseelement
    ret = self._execute_context(
          ^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1846, in _execute_context
    return self._exec_single_context(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1986, in _exec_single_context
    self._handle_dbapi_exception(
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 2355, in _handle_dbapi_exception
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1967, in _exec_single_context
    self.dialect.do_execute(
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 951, in do_execute
    cursor.execute(statement, parameters)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py", line 180, in execute
    self._adapt_connection._handle_exception(error)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py", line 340, in _handle_exception
    raise error
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py", line 162, in execute
    self.await_(_cursor.execute(operation, parameters))
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\cursor.py", line 40, in execute
    await self._execute(self._cursor.execute, sql, parameters)
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\cursor.py", line 32, in _execute
    return await self._conn._execute(fn, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\core.py", line 122, in _execute
    return await future
           ^^^^^^^^^^^^
  File "F:\Projects\Languages\Python\WorkingOnIt\windx\.venv\Lib\site-packages\aiosqlite\core.py", line 105, in run
    result = function()
             ^^^^^^^^^^
sqlalchemy.exc.IntegrityError: (sqlite3.IntegrityError) UNIQUE constraint failed: users.username
[SQL: INSERT INTO users (email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id]
[parameters: ('admin@example.com', 'admin', '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO', 'Admin User', 1, 0, '2025-11-24 05:04:22.241513', '2025-11-24 05:04:22.241513')]
(Background on this error at: https://sqlalche.me/e/20/gkpj)

test setup failed
self = <sqlalchemy.engine.base.Connection object at 0x0000023D913277D0>
dialect = <sqlalchemy.dialects.sqlite.aiosqlite.SQLiteDialect_aiosqlite object at 0x0000023D91147650>
context = <sqlalchemy.dialects.sqlite.aiosqlite.SQLiteExecutionContext_aiosqlite object at 0x0000023D91391F10>
statement = <sqlalchemy.dialects.sqlite.base.SQLiteCompiler object at 0x0000023D91391F90>
parameters = [('admin@example.com', 'admin', '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO', 'Admin User', 1, 0, ...)]

    def _exec_single_context(
        self,
        dialect: Dialect,
        context: ExecutionContext,
        statement: Union[str, Compiled],
        parameters: Optional[_AnyMultiExecuteParams],
    ) -> CursorResult[Any]:
        """continue the _execute_context() method for a single DBAPI
        cursor.execute() or cursor.executemany() call.
    
        """
        if dialect.bind_typing is BindTyping.SETINPUTSIZES:
            generic_setinputsizes = context._prepare_set_input_sizes()
    
            if generic_setinputsizes:
                try:
                    dialect.do_set_input_sizes(
                        context.cursor, generic_setinputsizes, context
                    )
                except BaseException as e:
                    self._handle_dbapi_exception(
                        e, str(statement), parameters, None, context
                    )
    
        cursor, str_statement, parameters = (
            context.cursor,
            context.statement,
            context.parameters,
        )
    
        effective_parameters: Optional[_AnyExecuteParams]
    
        if not context.executemany:
            effective_parameters = parameters[0]
        else:
            effective_parameters = parameters
    
        if self._has_events or self.engine._has_events:
            for fn in self.dispatch.before_cursor_execute:
                str_statement, effective_parameters = fn(
                    self,
                    cursor,
                    str_statement,
                    effective_parameters,
                    context,
                    context.executemany,
                )
    
        if self._echo:
            self._log_info(str_statement)
    
            stats = context._get_cache_stats()
    
            if not self.engine.hide_parameters:
                self._log_info(
                    "[%s] %r",
                    stats,
                    sql_util._repr_params(
                        effective_parameters,
                        batches=10,
                        ismulti=context.executemany,
                    ),
                )
            else:
                self._log_info(
                    "[%s] [SQL parameters hidden due to hide_parameters=True]",
                    stats,
                )
    
        evt_handled: bool = False
        try:
            if context.execute_style is ExecuteStyle.EXECUTEMANY:
                effective_parameters = cast(
                    "_CoreMultiExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_executemany:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_executemany(
                        cursor,
                        str_statement,
                        effective_parameters,
                        context,
                    )
            elif not effective_parameters and context.no_parameters:
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute_no_params:
                        if fn(cursor, str_statement, context):
                            evt_handled = True
                            break
                if not evt_handled:
                    self.dialect.do_execute_no_params(
                        cursor, str_statement, context
                    )
            else:
                effective_parameters = cast(
                    "_CoreSingleExecuteParams", effective_parameters
                )
                if self.dialect._has_events:
                    for fn in self.dialect.dispatch.do_execute:
                        if fn(
                            cursor,
                            str_statement,
                            effective_parameters,
                            context,
                        ):
                            evt_handled = True
                            break
                if not evt_handled:
>                   self.dialect.do_execute(
                        cursor, str_statement, effective_parameters, context
                    )

context    = <sqlalchemy.dialects.sqlite.aiosqlite.SQLiteExecutionContext_aiosqlite object at 0x0000023D91391F10>
cursor     = <sqlalchemy.dialects.sqlite.aiosqlite.AsyncAdapt_aiosqlite_cursor object at 0x0000023D91322B60>
dialect    = <sqlalchemy.dialects.sqlite.aiosqlite.SQLiteDialect_aiosqlite object at 0x0000023D91147650>
effective_parameters = ('admin@example.com',
 'admin',
 '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
 'Admin User',
 1,
 0,
 '2025-11-24 05:04:22.241513',
 '2025-11-24 05:04:22.241513')
evt_handled = False
parameters = [('admin@example.com',
  'admin',
  '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
  'Admin User',
  1,
  0,
  '2025-11-24 05:04:22.241513',
  '2025-11-24 05:04:22.241513')]
self       = <sqlalchemy.engine.base.Connection object at 0x0000023D913277D0>
statement  = <sqlalchemy.dialects.sqlite.base.SQLiteCompiler object at 0x0000023D91391F90>
str_statement = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id')

..\..\.venv\Lib\site-packages\sqlalchemy\engine\base.py:1967: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
..\..\.venv\Lib\site-packages\sqlalchemy\engine\default.py:951: in do_execute
    cursor.execute(statement, parameters)
        context    = <sqlalchemy.dialects.sqlite.aiosqlite.SQLiteExecutionContext_aiosqlite object at 0x0000023D91391F10>
        cursor     = <sqlalchemy.dialects.sqlite.aiosqlite.AsyncAdapt_aiosqlite_cursor object at 0x0000023D91322B60>
        parameters = ('admin@example.com',
 'admin',
 '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
 'Admin User',
 1,
 0,
 '2025-11-24 05:04:22.241513',
 '2025-11-24 05:04:22.241513')
        self       = <sqlalchemy.dialects.sqlite.aiosqlite.SQLiteDialect_aiosqlite object at 0x0000023D91147650>
        statement  = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id')
..\..\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py:180: in execute
    self._adapt_connection._handle_exception(error)
        _cursor    = <aiosqlite.cursor.Cursor object at 0x0000023D913723D0>
        operation  = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id')
        parameters = ('admin@example.com',
 'admin',
 '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
 'Admin User',
 1,
 0,
 '2025-11-24 05:04:22.241513',
 '2025-11-24 05:04:22.241513')
        self       = <sqlalchemy.dialects.sqlite.aiosqlite.AsyncAdapt_aiosqlite_cursor object at 0x0000023D91322B60>
..\..\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py:340: in _handle_exception
    raise error
        error      = IntegrityError('UNIQUE constraint failed: users.username')
        self       = <AdaptedConnection <Connection(Thread-2, stopped daemon 16556)>>
..\..\.venv\Lib\site-packages\sqlalchemy\dialects\sqlite\aiosqlite.py:162: in execute
    self.await_(_cursor.execute(operation, parameters))
        _cursor    = <aiosqlite.cursor.Cursor object at 0x0000023D913723D0>
        operation  = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id')
        parameters = ('admin@example.com',
 'admin',
 '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
 'Admin User',
 1,
 0,
 '2025-11-24 05:04:22.241513',
 '2025-11-24 05:04:22.241513')
        self       = <sqlalchemy.dialects.sqlite.aiosqlite.AsyncAdapt_aiosqlite_cursor object at 0x0000023D91322B60>
..\..\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py:132: in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        awaitable  = <coroutine object Cursor.execute at 0x0000023D91342980>
        current    = <_AsyncIoGreenlet object at 0x0000023D910B88C0 (otid=0x0000023D8B955FB0) dead>
..\..\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py:196: in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
        _require_await = False
        args       = ()
        context    = <_AsyncIoGreenlet object at 0x0000023D910B88C0 (otid=0x0000023D8B955FB0) dead>
        fn         = <bound method Session.commit of <sqlalchemy.orm.session.Session object at 0x0000023D903917D0>>
        kwargs     = {}
        result     = <coroutine object Connection.rollback at 0x0000023D9134DD80>
        switch_occurred = True
        value      = None
..\..\.venv\Lib\site-packages\aiosqlite\cursor.py:40: in execute
    await self._execute(self._cursor.execute, sql, parameters)
        parameters = ('admin@example.com',
 'admin',
 '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
 'Admin User',
 1,
 0,
 '2025-11-24 05:04:22.241513',
 '2025-11-24 05:04:22.241513')
        self       = <aiosqlite.cursor.Cursor object at 0x0000023D913723D0>
        sql        = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id')
..\..\.venv\Lib\site-packages\aiosqlite\cursor.py:32: in _execute
    return await self._conn._execute(fn, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        args       = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id',
 ('admin@example.com',
  'admin',
  '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
  'Admin User',
  1,
  0,
  '2025-11-24 05:04:22.241513',
  '2025-11-24 05:04:22.241513'))
        fn         = <built-in method execute of sqlite3.Cursor object at 0x0000023D911FE340>
        kwargs     = {}
        self       = <aiosqlite.cursor.Cursor object at 0x0000023D913723D0>
..\..\.venv\Lib\site-packages\aiosqlite\core.py:122: in _execute
    return await future
           ^^^^^^^^^^^^
        args       = ('INSERT INTO users (email, username, hashed_password, full_name, is_active, '
 'is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) '
 'RETURNING id',
 ('admin@example.com',
  'admin',
  '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO',
  'Admin User',
  1,
  0,
  '2025-11-24 05:04:22.241513',
  '2025-11-24 05:04:22.241513'))
        fn         = <built-in method execute of sqlite3.Cursor object at 0x0000023D911FE340>
        function   = functools.partial(<built-in method execute of sqlite3.Cursor object at 0x0000023D911FE340>, 'INSERT INTO users (email, username, hashed_password, full_name, is_active, is_superuser, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id', ('admin@example.com', 'admin', '$2b$12$zP4vTT/TqH2HP7UUsY4M4OTcdxkt03/1fryLrdeSOlERlZ.bGuQRO', 'Admin User', 1, 0, '2025-11-24 05:04:22.241513', '2025-11-24 05:04:22.241513'))
        future     = <Future finished exception=IntegrityError('UNIQUE constraint failed: users.username')>
        kwargs     = {}
        self       = <Connection(Thread-2, stopped daemon 16556)>
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

'''