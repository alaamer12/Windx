# FastAPI And Starlette

---

### 🔹 `starlette.websockets`

- **`starlette.websockets.WebSocket`**
    
    Represents an incoming WebSocket connection.
    
    **`__init__` parameters**:
    
    - `scope: Scope`
    - `receive: Receive`
    - `send: Send`
- **`starlette.websockets.WebSocketDisconnect`**
    
    Exception raised when a WebSocket client disconnects.
    
    **`__init__` parameters**:
    
    - `code: int = 1000`
    - `reason: str | None = None`
- **`starlette.websockets.WebSocketState`**
    
    Enum indicating WebSocket connection state. Not instantiated directly.
    
    **Values**: `CONNECTING = 0`, `CONNECTED = 1`, `DISCONNECTED = 2`
    
    → No `__init__` parameters (inherits from `int`).
    
- **`starlette.websockets.WebSocketClose`**
    
    Internal class representing a WebSocket close message. Rarely used directly.
    
    **`__init__` parameters**:
    
    - `code: int = 1000`
    - `reason: str | None = None`

---

### 🔹 `starlette.testclient`

- **`starlette.testclient.TestClient`**
Test client for making requests to ASGI apps during testing (built on `httpx`).**`__init__` parameters**:
    - `app: ASGIApp`
    - `base_url: str = "http://testserver"`
    - `raise_server_exceptions: bool = True`
    - `root_path: str = ""`
    - `backend: str = "asyncio"`
    - `backend_options: dict[str, Any] | None = None`

---

### 🔹 `starlette.templating`

- **`starlette.templating.Jinja2Templates`**
Integrates Jinja2 templating engine with Starlette.**`__init__` parameters**:
    - `directory: str | Sequence[str] | None = None`
    - `context_processors: Sequence[Callable[[Request], dict[str, Any]]] | None = None`
    - `*env_options: Any` (passed to `jinja2.Environment`)

---

### 🔹 `starlette.staticfiles`

- **`starlette.staticfiles.StaticFiles`**
ASGI app for serving static files.**`__init__` parameters**:
    - `directory: str | os.PathLike[str] | None = None`
    - `packages: list[str | tuple[str, str]] | None = None`
    - `html: bool = False`
    - `check_dir: bool = True`

---

### 🔹 `starlette.responses`

- **`starlette.responses.Response`**
    
    Base response class.
    
    **`__init__` parameters**:
    
    - `content: Any = None`
    - `status_code: int = 200`
    - `headers: Mapping[str, str] | None = None`
    - `media_type: str | None = None`
    - `background: BackgroundTask | None = None`
- **`starlette.responses.HTMLResponse`**
    
    Response with `text/html` media type. Same params as `Response`.
    
- **`starlette.responses.PlainTextResponse`**
    
    Response with `text/plain` media type. Same params as `Response`.
    
- **`starlette.responses.JSONResponse`**
    
    Automatically serializes content to JSON.
    
    **`__init__` parameters**:
    
    - `content: Any`
    - `status_code: int = 200`
    - `headers: Mapping[str, str] | None = None`
    - `media_type: str = "application/json"`
    - `background: BackgroundTask | None = None`
    - `encoders: list[Callable[[Any], Any]] | None = None` *(deprecated, ignored in recent versions)*
- **`starlette.responses.RedirectResponse`**
    
    HTTP 302/303/307/308 redirect.
    
    **`__init__` parameters**:
    
    - `url: str | URL`
    - `status_code: int = 302`
    - `headers: Mapping[str, str] | None = None`
    - `background: BackgroundTask | None = None`
- **`starlette.responses.StreamingResponse`**
    
    Streams async generator content.
    
    **`__init__` parameters**:
    
    - `content: Any` *(async iterable)*
    - `status_code: int = 200`
    - `headers: Mapping[str, str] | None = None`
    - `media_type: str | None = None`
    - `background: BackgroundTask | None = None`
- **`starlette.responses.FileResponse`**
    
    Efficiently serves a file.
    
    **`__init__` parameters**:
    
    - `path: str | os.PathLike[str]`
    - `status_code: int = 200`
    - `headers: Mapping[str, str] | None = None`
    - `media_type: str | None = None`
    - `background: BackgroundTask | None = None`
    - `filename: str | None = None`
    - `stat_result: os.stat_result | None = None`
    - `method: str | None = None`
    - `content_disposition_type: str = "attachment"`

---

### 🔹 `starlette.requests`

- **`starlette.requests.Request`**
ASGI HTTP request wrapper.**`__init__` parameters**:
    - `scope: Scope`
    - `receive: Receive | None = None`
    - `send: Send | None = None`

---

### 🔹 `starlette.exceptions`

- **`starlette.exceptions.HTTPException`**
Generic HTTP error exception.**`__init__` parameters**:
    - `status_code: int`
    - `detail: Any = None`
    - `headers: Mapping[str, str] | None = None`
- **`starlette.exceptions.WebSocketException`**
Exception to close WebSocket with code/reason.**`__init__` parameters**:
    - `code: int = 1000`
    - `reason: str | None = None`

---

### 🔹 `starlette.datastructures`

- **`starlette.datastructures.UploadFile`**
Represents an uploaded file.**`__init__` parameters**:
    - `file: SpooledTemporaryFile[bytes]`
    - `filename: str | None = None`
    - `headers: Headers | None = None`
    - `size: int | None = None`
- **`starlette.datastructures.FormData`**
Multi-dict for form data (supports multiple values per key).**`__init__` parameters**:
    - `items: Sequence[tuple[str, str | UploadFile]] | None = None`
- **`starlette.datastructures.Headers`**
Case-insensitive, immutable HTTP headers.**`__init__` parameters**:
    - `raw: Sequence[tuple[bytes, bytes]] | None = None`
    - `scope: Scope | None = None`
- **`starlette.datastructures.URL`**
Immutable URL representation.**`__init__` parameters**:
    - `url: str = ""`
    - `scope: Scope | None = None`
    - `components: tuple[str, str, int, str, str, str, str] | None = None`
- **`starlette.datastructures.QueryParams`**
Immutable query string parser.**`__init__` parameters**:
    - `query_string: str | None = None`
    - `scope: Scope | None = None`
- **`starlette.datastructures.MutableHeaders`**
Mutable version of `Headers`.**`__init__` parameters**:
    - `raw: list[tuple[bytes, bytes]] | None = None`
    - `scope: Scope | None = None`
- **`starlette.datastructures.Address`**
Represents a client IP/port.**`__init__` parameters**:
    - `host: str`
    - `port: int`
- **`starlette.datastructures.State`**
Attribute-style access to request state (`request.state.x`).**`__init__` parameters**:
    - `state: dict[str, Any] | None = None`

---

### 🔹 `starlette.concurrency`

- **`starlette.concurrency.run_in_threadpool`**
Runs a sync function in a thread pool (for async/await compatibility).**Parameters**:
    - `func: Callable[..., T]`
    - `args: Any`
- **`starlette.concurrency.iterate_in_threadpool`**
Iterates over a sync iterator in a thread pool.**Parameters**:
    - `iterator: Iterable[T]`

---

### 🔹 `starlette.background`

- **`starlette.background.BackgroundTask`**
Single background task to run after response.**`__init__` parameters**:
    - `func: Callable[..., Any]`
    - `args: Any`
- **`starlette.background.BackgroundTasks`**
Container for multiple background tasks.**`__init__` parameters**:
    - `tasks: Sequence[BackgroundTask] | None = None`

---

### 🔹 Middleware Modules

- **`starlette.middleware.wsgi.WSGIMiddleware`**
Wraps a WSGI app in an ASGI interface.**`__init__` parameters**:
    - `app: Callable[..., Any]`
- **`starlette.middleware.trusthost.TrustedHostMiddleware`**
Enforces allowed host headers.**`__init__` parameters**:
    - `app: ASGIApp`
    - `allowed_hosts: Sequence[str] | None = None`
    - `www_redirect: bool = True`
- **`starlette.middleware.httpsredirect.HTTPSRedirectMiddleware`**
Redirects HTTP requests to HTTPS.**`__init__` parameters**:
    - `app: ASGIApp`
- **`starlette.middleware.gzip.GZipMiddleware`**
Compresses responses with gzip.**`__init__` parameters**:
    - `app: ASGIApp`
    - `minimum_size: int = 500`
    - `compresslevel: int = 9`
- **`starlette.middleware.cors.CORSMiddleware`**
Adds CORS headers to responses.**`__init__` parameters**:
    - `app: ASGIApp`
    - `allow_origins: Sequence[str] = ()`
    - `allow_methods: Sequence[str] = ("GET",)`
    - `allow_headers: Sequence[str] = ()`
    - `allow_credentials: bool = False`
    - `allow_origin_regex: str | None = None`
    - `expose_headers: Sequence[str] = ()`
    - `max_age: int = 600`

---

---

## FastApi core

## Fastapi

### app

```python
Query(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
          
  
  Header(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        convert_underscores=convert_underscores,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
 Cookie(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
 
 Body(
        default=default,
        default_factory=default_factory,
        embed=embed,
        media_type=media_type,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
        
  Form(
        default=default,
        default_factory=default_factory,
        media_type=media_type,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
        
  File(
        default=default,
        default_factory=default_factory,
        media_type=media_type,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
  Depends(  # noqa: N802
    dependency: Annotated[
        Optional[Callable[..., Any]],
        Doc(
            """
            A "dependable" callable (like a function).

            Don't call it directly, FastAPI will call it for you, just pass the object
            directly.
            """
        ),
    ] = None,
    *,
    use_cache: Annotated[
        bool,
        Doc(
            """
            By default, after a dependency is called the first time in a request, if
            the dependency is declared again for the rest of the request (for example
            if the dependency is needed by several dependencies), the value will be
            re-used for the rest of the request.

            Set `use_cache` to `False` to disable this behavior and ensure the
            dependency is called again (if declared more than once) in the same request.
            """
        ),
    ] = True,      
        
               
        
        
        
 Path(
        default=default,
        default_factory=default_factory,
        alias=alias,
        alias_priority=alias_priority,
        validation_alias=validation_alias,
        serialization_alias=serialization_alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        regex=regex,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=example,
        examples=examples,
        openapi_examples=openapi_examples,
        deprecated=deprecated,
        include_in_schema=include_in_schema,
        json_schema_extra=json_schema_extra,
        
        
        
```

### router

```python
class APIRoute(routing.Route):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = Default(None),
        status_code: Optional[int] = None,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        response_description: str = "Successful Response",
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        deprecated: Optional[bool] = None,
        name: Optional[str] = None,
        methods: Optional[Union[Set[str], List[str]]] = None,
        operation_id: Optional[str] = None,
        response_model_include: Optional[IncEx] = None,
        response_model_exclude: Optional[IncEx] = None,
        response_model_by_alias: bool = True,
        response_model_exclude_unset: bool = False,
        response_model_exclude_defaults: bool = False,
        response_model_exclude_none: bool = False,
        include_in_schema: bool = True,
        response_class: Union[Type[Response], DefaultPlaceholder] = Default(
            JSONResponse
        ),
        dependency_overrides_provider: Optional[Any] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        openapi_extra: Optional[Dict[str, Any]] = None,
        generate_unique_id_function: Union[
            Callable[["APIRoute"], str], DefaultPlaceholder
        ] = Default(generate_unique_id),
        

 def include_router(
        self,
        router: Annotated["APIRouter", Doc("The `APIRouter` to include.")],
        *,
        prefix: Annotated[str, Doc("An optional path prefix for the router.")] = "",
        tags: Annotated[
            Optional[List[Union[str, Enum]]],
            Doc(
                """
                A list of tags to be applied to all the *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
            ),
        ] = None,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to all the
                *path operations* in this router.

                Read more about it in the
                [FastAPI docs for Bigger Applications - Multiple Files](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).
                """
            ),
        ] = None,
        default_response_class: Annotated[
            Type[Response],
            Doc(
                """
                The default response class to be used.

                Read more in the
                [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/#default-response-class).
                """
            ),
        ] = Default(JSONResponse),
        responses: Annotated[
            Optional[Dict[Union[int, str], Dict[str, Any]]],
            Doc(
                """
                Additional responses to be shown in OpenAPI.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Additional Responses in OpenAPI](https://fastapi.tiangolo.com/advanced/additional-responses/).

                And in the
                [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/#include-an-apirouter-with-a-custom-prefix-tags-responses-and-dependencies).
                """
            ),
        ] = None,
        callbacks: Annotated[
            Optional[List[BaseRoute]],
            Doc(
                """
                OpenAPI callbacks that should apply to all *path operations* in this
                router.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for OpenAPI Callbacks](https://fastapi.tiangolo.com/advanced/openapi-callbacks/).
                """
            ),
        ] = None,
        deprecated: Annotated[
            Optional[bool],
            Doc(
                """
                Mark all *path operations* in this router as deprecated.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
            ),
        ] = None,
        include_in_schema: Annotated[
            bool,
            Doc(
                """
                Include (or not) all the *path operations* in this router in the
                generated OpenAPI schema.

                This affects the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = True,
        generate_unique_id_function: Annotated[
            Callable[[APIRoute], str],
            Doc(
                """
                Customize the function used to generate unique IDs for the *path
                operations* shown in the generated OpenAPI.

                This is particularly useful when automatically generating clients or
                SDKs for your API.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
                """
            ),
        ] = Default(generate_unique_id),
    ) -> None:
        """
        Include another `APIRouter` in the same current `APIRouter`.

        Read more about it in the
        [FastAPI docs for Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

        ## Example

        ```python
        from fastapi import APIRouter, FastAPI

        app = FastAPI()
        internal_router = APIRouter()
        users_router = APIRouter()

        @users_router.get("/users/")
        def read_users():
            return [{"name": "Rick"}, {"name": "Morty"}]

        internal_router.include_router(users_router)
        app.include_router(internal_router)
        ```
        """
```