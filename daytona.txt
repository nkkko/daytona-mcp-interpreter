└── docs
    └── python-sdk
        ├── daytona.mdx
        ├── errors.mdx
        ├── file-system.mdx
        ├── git.mdx
        ├── lsp-server.mdx
        ├── process.mdx
        └── sandbox.mdx


/docs/python-sdk/daytona.mdx:
--------------------------------------------------------------------------------
  1 | ---
  2 | title: Sandbox Management
  3 | ---
  4 |
  5 | Sandboxes are isolated development environments managed by Daytona.
  6 | This guide covers how to create, manage, and remove Sandboxes using the SDK.
  7 |
  8 | **Examples**:
  9 |
 10 |   Basic usage with environment variables:
 11 | ```python
 12 | from daytona_sdk import Daytona
 13 | # Initialize using environment variables
 14 | daytona = Daytona()  # Uses env vars DAYTONA_API_KEY, DAYTONA_SERVER_URL, DAYTONA_TARGET
 15 |
 16 | # Create a default Python workspace with custom environment variables
 17 | workspace = daytona.create(CreateWorkspaceParams(
 18 |     language="python",
 19 |     env_vars={"PYTHON_ENV": "development"}
 20 | ))
 21 |
 22 | # Execute commands in the workspace
 23 | response = workspace.process.execute_command('echo "Hello, World!"')
 24 | print(response.result)
 25 |
 26 | # Run Python code securely inside the workspace
 27 | response = workspace.process.code_run('print("Hello from Python!")')
 28 | print(response.result)
 29 |
 30 | # Remove the workspace after use
 31 | daytona.remove(workspace)
 32 | ```
 33 |
 34 |   Usage with explicit configuration:
 35 | ```python
 36 | from daytona_sdk import Daytona, DaytonaConfig, CreateWorkspaceParams, WorkspaceResources
 37 |
 38 | # Initialize with explicit configuration
 39 | config = DaytonaConfig(
 40 |     api_key="your-api-key",
 41 |     server_url="https://your-server.com",
 42 |     target="us"
 43 | )
 44 | daytona = Daytona(config)
 45 |
 46 | # Create a custom workspace with specific resources and settings
 47 | workspace = daytona.create(CreateWorkspaceParams(
 48 |     language="python",
 49 |     image="python:3.11",
 50 |     resources=WorkspaceResources(
 51 |         cpu=2,
 52 |         memory=4,  # 4GB RAM
 53 |         disk=20    # 20GB disk
 54 |     ),
 55 |     env_vars={"PYTHON_ENV": "development"},
 56 |     auto_stop_interval=60  # Auto-stop after 1 hour of inactivity
 57 | ))
 58 |
 59 | # Use workspace features
 60 | workspace.git.clone("https://github.com/user/repo.git")
 61 | workspace.process.execute_command("python -m pytest")
 62 | ```
 63 |
 64 | <a id="daytona_sdk.daytona.Daytona"></a>
 65 | ## Daytona
 66 |
 67 | ```python
 68 | class Daytona()
 69 | ```
 70 |
 71 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L198)
 72 |
 73 | Main class for interacting with Daytona Server API.
 74 |
 75 | This class provides methods to create, manage, and interact with Daytona Sandboxes.
 76 | It can be initialized either with explicit configuration or using environment variables.
 77 |
 78 | **Attributes**:
 79 |
 80 | - `api_key` _str_ - API key for authentication.
 81 | - `server_url` _str_ - URL of the Daytona server.
 82 | - `target` _str_ - Default target location for Sandboxes.
 83 |
 84 |
 85 | **Example**:
 86 |
 87 |   Using environment variables:
 88 | ```python
 89 | daytona = Daytona()  # Uses DAYTONA_API_KEY, DAYTONA_SERVER_URL
 90 | ```
 91 |
 92 |   Using explicit configuration:
 93 | ```python
 94 | config = DaytonaConfig(
 95 |     api_key="your-api-key",
 96 |     server_url="https://your-server.com",
 97 |     target="us"
 98 | )
 99 | daytona = Daytona(config)
100 | ```
101 |
102 |
103 | #### Daytona.\_\_init\_\_
104 |
105 | ```python
106 | def __init__(config: Optional[DaytonaConfig] = None)
107 | ```
108 |
109 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L226)
110 |
111 | Initializes Daytona instance with optional configuration.
112 |
113 | If no config is provided, reads from environment variables:
114 | - `DAYTONA_API_KEY`: Required API key for authentication
115 | - `DAYTONA_SERVER_URL`: Required server URL
116 | - `DAYTONA_TARGET`: Optional target environment (defaults to WorkspaceTargetRegion.US)
117 |
118 | **Arguments**:
119 |
120 | - `config` _Optional[DaytonaConfig]_ - Object containing api_key, server_url, and target.
121 |
122 |
123 | **Raises**:
124 |
125 | - `DaytonaError` - If API key or Server URL is not provided either through config or environment variables
126 |
127 |
128 | **Example**:
129 |
130 | ```python
131 | from daytona_sdk import Daytona, DaytonaConfig
132 | # Using environment variables
133 | daytona1 = Daytona()
134 | # Using explicit configuration
135 | config = DaytonaConfig(
136 |     api_key="your-api-key",
137 |     server_url="https://your-server.com",
138 |     target="us"
139 | )
140 | daytona2 = Daytona(config)
141 | ```
142 |
143 |
144 | #### Daytona.create
145 |
146 | ```python
147 | @intercept_errors(message_prefix="Failed to create workspace: ")
148 | def create(params: Optional[CreateWorkspaceParams] = None,
149 |            timeout: Optional[float] = 60) -> Workspace
150 | ```
151 |
152 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L285)
153 |
154 | Creates Sandboxes with default or custom configurations. You can specify various parameters,
155 | including language, image, resources, environment variables, and volumes for the Sandbox.
156 |
157 | **Arguments**:
158 |
159 | - `params` _Optional[CreateWorkspaceParams]_ - Parameters for Sandbox creation. If not provided,
160 |   defaults to Python language.
161 | - `timeout` _Optional[float]_ - Timeout (in seconds) for workspace creation. 0 means no timeout. Default is 60 seconds.
162 |
163 |
164 | **Returns**:
165 |
166 | - `Workspace` - The created Sandbox instance.
167 |
168 |
169 | **Raises**:
170 |
171 | - `DaytonaError` - If timeout or auto_stop_interval is negative; If workspace fails to start or times out
172 |
173 |
174 | **Example**:
175 |
176 |   Create a default Python Sandbox:
177 | ```python
178 | workspace = daytona.create()
179 | ```
180 |
181 |   Create a custom Sandbox:
182 | ```python
183 | params = CreateWorkspaceParams(
184 |     language="python",
185 |     name="my-workspace",
186 |     image="debian:12.9",
187 |     env_vars={"DEBUG": "true"},
188 |     resources=WorkspaceResources(cpu=2, memory=4096),
189 |     auto_stop_interval=0
190 | )
191 | workspace = daytona.create(params, 40)
192 | ```
193 |
194 |
195 | #### Daytona.remove
196 |
197 | ```python
198 | @intercept_errors(message_prefix="Failed to remove workspace: ")
199 | def remove(workspace: Workspace, timeout: Optional[float] = 60) -> None
200 | ```
201 |
202 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L432)
203 |
204 | Removes a Sandbox.
205 |
206 | **Arguments**:
207 |
208 | - `workspace` _Workspace_ - The Sandbox instance to remove.
209 | - `timeout` _Optional[float]_ - Timeout (in seconds) for workspace removal. 0 means no timeout. Default is 60 seconds.
210 |
211 |
212 | **Raises**:
213 |
214 | - `DaytonaError` - If workspace fails to remove or times out
215 |
216 |
217 | **Example**:
218 |
219 | ```python
220 | workspace = daytona.create()
221 | # ... use workspace ...
222 | daytona.remove(workspace)  # Clean up when done
223 | ```
224 |
225 |
226 | #### Daytona.get\_current\_workspace
227 |
228 | ```python
229 | @intercept_errors(message_prefix="Failed to get workspace: ")
230 | def get_current_workspace(workspace_id: str) -> Workspace
231 | ```
232 |
233 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L452)
234 |
235 | Get a Sandbox by its ID.
236 |
237 | **Arguments**:
238 |
239 | - `workspace_id` _str_ - The ID of the Sandbox to retrieve.
240 |
241 |
242 | **Returns**:
243 |
244 | - `Workspace` - The Sandbox instance.
245 |
246 |
247 | **Raises**:
248 |
249 | - `DaytonaError` - If workspace_id is not provided.
250 |
251 |
252 | **Example**:
253 |
254 | ```python
255 | workspace = daytona.get_current_workspace("my-workspace-id")
256 | print(workspace.status)
257 | ```
258 |
259 |
260 | #### Daytona.list
261 |
262 | ```python
263 | @intercept_errors(message_prefix="Failed to list workspaces: ")
264 | def list() -> List[Workspace]
265 | ```
266 |
267 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L490)
268 |
269 | Lists all Sandboxes.
270 |
271 | **Returns**:
272 |
273 | - `List[Workspace]` - List of all available Sandbox instances.
274 |
275 |
276 | **Example**:
277 |
278 | ```python
279 | workspaces = daytona.list()
280 | for workspace in workspaces:
281 |     print(f"{workspace.id}: {workspace.status}")
282 | ```
283 |
284 |
285 | #### Daytona.start
286 |
287 | ```python
288 | def start(workspace: Workspace, timeout: Optional[float] = 60) -> None
289 | ```
290 |
291 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L555)
292 |
293 | Starts a Sandbox and waits for it to be ready.
294 |
295 | **Arguments**:
296 |
297 | - `workspace` _Workspace_ - The Sandbox to start.
298 | - `timeout` _Optional[float]_ - Optional timeout in seconds to wait for the Sandbox to start. 0 means no timeout. Default is 60 seconds.
299 |
300 |
301 | **Raises**:
302 |
303 | - `DaytonaError` - If timeout is negative; If Sandbox fails to start or times out
304 |
305 |
306 | #### Daytona.stop
307 |
308 | ```python
309 | def stop(workspace: Workspace, timeout: Optional[float] = 60) -> None
310 | ```
311 |
312 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L567)
313 |
314 | Stops a Sandbox and waits for it to be stopped.
315 |
316 | **Arguments**:
317 |
318 | - `workspace` _Workspace_ - The workspace to stop
319 | - `timeout` _Optional[float]_ - Optional timeout (in seconds) for workspace stop. 0 means no timeout. Default is 60 seconds.
320 |
321 |
322 | **Raises**:
323 |
324 | - `DaytonaError` - If timeout is negative; If Sandbox fails to stop or times out
325 |
326 |
327 | Sandboxes are isolated development environments managed by Daytona.
328 | This guide covers how to create, manage, and remove Sandboxes using the SDK.
329 |
330 | **Examples**:
331 |
332 |   Basic usage with environment variables:
333 | ```python
334 | from daytona_sdk import Daytona
335 | # Initialize using environment variables
336 | daytona = Daytona()  # Uses env vars DAYTONA_API_KEY, DAYTONA_SERVER_URL, DAYTONA_TARGET
337 |
338 | # Create a default Python workspace with custom environment variables
339 | workspace = daytona.create(CreateWorkspaceParams(
340 |     language="python",
341 |     env_vars={"PYTHON_ENV": "development"}
342 | ))
343 |
344 | # Execute commands in the workspace
345 | response = workspace.process.execute_command('echo "Hello, World!"')
346 | print(response.result)
347 |
348 | # Run Python code securely inside the workspace
349 | response = workspace.process.code_run('print("Hello from Python!")')
350 | print(response.result)
351 |
352 | # Remove the workspace after use
353 | daytona.remove(workspace)
354 | ```
355 |
356 |   Usage with explicit configuration:
357 | ```python
358 | from daytona_sdk import Daytona, DaytonaConfig, CreateWorkspaceParams, WorkspaceResources
359 |
360 | # Initialize with explicit configuration
361 | config = DaytonaConfig(
362 |     api_key="your-api-key",
363 |     server_url="https://your-server.com",
364 |     target="us"
365 | )
366 | daytona = Daytona(config)
367 |
368 | # Create a custom workspace with specific resources and settings
369 | workspace = daytona.create(CreateWorkspaceParams(
370 |     language="python",
371 |     image="python:3.11",
372 |     resources=WorkspaceResources(
373 |         cpu=2,
374 |         memory=4,  # 4GB RAM
375 |         disk=20    # 20GB disk
376 |     ),
377 |     env_vars={"PYTHON_ENV": "development"},
378 |     auto_stop_interval=60  # Auto-stop after 1 hour of inactivity
379 | ))
380 |
381 | # Use workspace features
382 | workspace.git.clone("https://github.com/user/repo.git")
383 | workspace.process.execute_command("python -m pytest")
384 | ```
385 |
386 |
387 | <a id="daytona_sdk.daytona.CodeLanguage"></a>
388 | ## CodeLanguage
389 |
390 | ```python
391 | @dataclass
392 | class CodeLanguage(Enum)
393 | ```
394 |
395 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L85)
396 |
397 | Programming languages supported by Daytona
398 |
399 |
400 | <a id="daytona_sdk.daytona.DaytonaConfig"></a>
401 | ## DaytonaConfig
402 |
403 | ```python
404 | @dataclass
405 | class DaytonaConfig()
406 | ```
407 |
408 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L101)
409 |
410 | Configuration options for initializing the Daytona client.
411 |
412 | **Attributes**:
413 |
414 | - `api_key` _str_ - API key for authentication with Daytona server.
415 | - `server_url` _str_ - URL of the Daytona server.
416 | - `target` _str_ - Target environment for Sandbox.
417 |
418 |
419 | **Example**:
420 |
421 | ```python
422 | config = DaytonaConfig(
423 |     api_key="your-api-key",
424 |     server_url="https://your-server.com",
425 |     target="us"
426 | )
427 | daytona = Daytona(config)
428 | ```
429 |
430 |
431 | <a id="daytona_sdk.daytona.WorkspaceResources"></a>
432 | ## WorkspaceResources
433 |
434 | ```python
435 | @dataclass
436 | class WorkspaceResources()
437 | ```
438 |
439 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L125)
440 |
441 | Resources configuration for Sandbox.
442 |
443 | **Attributes**:
444 |
445 | - `cpu` _Optional[int]_ - Number of CPU cores to allocate.
446 | - `memory` _Optional[int]_ - Amount of memory in GB to allocate.
447 | - `disk` _Optional[int]_ - Amount of disk space in GB to allocate.
448 | - `gpu` _Optional[int]_ - Number of GPUs to allocate.
449 |
450 |
451 | **Example**:
452 |
453 | ```python
454 | resources = WorkspaceResources(
455 |     cpu=2,
456 |     memory=4,  # 4GB RAM
457 |     disk=20,   # 20GB disk
458 |     gpu=1
459 | )
460 | params = CreateWorkspaceParams(
461 |     language="python",
462 |     resources=resources
463 | )
464 | ```
465 |
466 |
467 | <a id="daytona_sdk.daytona.CreateWorkspaceParams"></a>
468 | ## CreateWorkspaceParams
469 |
470 | ```python
471 | class CreateWorkspaceParams(BaseModel)
472 | ```
473 |
474 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/daytona.py#L154)
475 |
476 | Parameters for creating a new Sandbox.
477 |
478 | **Attributes**:
479 |
480 | - `language` _CodeLanguage_ - Programming language for the Sandbox ("python", "javascript", "typescript").
481 | - `id` _Optional[str]_ - Custom identifier for the Sandbox. If not provided, a random ID will be generated.
482 | - `name` _Optional[str]_ - Display name for the Sandbox. Defaults to Sandbox ID if not provided.
483 | - `image` _Optional[str]_ - Custom Docker image to use for the Sandbox.
484 | - `os_user` _Optional[str]_ - OS user for the Sandbox. Defaults to "daytona".
485 | - `env_vars` _Optional[Dict[str, str]]_ - Environment variables to set in the Sandbox.
486 | - `labels` _Optional[Dict[str, str]]_ - Custom labels for the Sandbox.
487 | - `public` _Optional[bool]_ - Whether the Sandbox should be public.
488 | - `target` _Optional[str]_ - Target location for the Sandbox. Can be "us", "eu", or "asia".
489 | - `resources` _Optional[WorkspaceResources]_ - Resource configuration for the Sandbox.
490 | - `timeout` _Optional[float]_ - Timeout in seconds for Sandbox to be created and started.
491 | - `auto_stop_interval` _Optional[int]_ - Interval in minutes after which Sandbox will automatically stop if no Sandbox event occurs during that time. Default is 15 minutes. 0 means no auto-stop.
492 |
493 |
494 | **Example**:
495 |
496 | ```python
497 | params = CreateWorkspaceParams(
498 |     language="python",
499 |     name="my-workspace",
500 |     env_vars={"DEBUG": "true"},
501 |     resources=WorkspaceResources(cpu=2, memory=4),
502 |     auto_stop_interval=20
503 | )
504 | workspace = daytona.create(params, 50)
505 | ```
506 |
507 |
508 |


--------------------------------------------------------------------------------
/docs/python-sdk/errors.mdx:
--------------------------------------------------------------------------------
 1 | ---
 2 | title: Errors
 3 | ---
 4 |
 5 | <a id="daytona_sdk.common.errors.DaytonaError"></a>
 6 | ## DaytonaError
 7 |
 8 | ```python
 9 | class DaytonaError(Exception)
10 | ```
11 |
12 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/common/errors.py#L1)
13 |
14 | Base error for Daytona SDK.
15 |
16 |
17 |
18 |


--------------------------------------------------------------------------------
/docs/python-sdk/file-system.mdx:
--------------------------------------------------------------------------------
  1 | ---
  2 | title: File System Operations
  3 | ---
  4 |
  5 | The Daytona SDK provides comprehensive file system operations through the `fs` module in Sandboxes.
  6 | You can perform various operations like listing files, creating directories, reading and writing files, and more.
  7 | This guide covers all available file system operations and best practices.
  8 |
  9 | **Examples**:
 10 |
 11 |   Basic file operations:
 12 | ```python
 13 |     workspace = daytona.create()
 14 |
 15 |     # Create a directory
 16 |     workspace.fs.create_folder("/workspace/data", "755")
 17 |
 18 |     # Upload a file
 19 |     with open("local_file.txt", "rb") as f:
 20 |         content = f.read()
 21 |     workspace.fs.upload_file("/workspace/data/file.txt", content)
 22 |
 23 |     # List directory contents
 24 |     files = workspace.fs.list_files("/workspace")
 25 |     for file in files:
 26 |         print(f"Name: {file.name}")
 27 |         print(f"Is directory: {file.is_dir}")
 28 |         print(f"Size: {file.size}")
 29 |         print(f"Modified: {file.mod_time}")
 30 |
 31 |     # Search file contents
 32 |     matches = workspace.fs.find_files(
 33 |         path="/workspace/src",
 34 |         pattern="text-of-interest"
 35 |     )
 36 |     for match in matches:
 37 |         print(f"Absolute file path: {match.file}")
 38 |         print(f"Line number: {match.line}")
 39 |         print(f"Line content: {match.content}")
 40 |         print("
 41 | ")
 42 | ```
 43 |
 44 |   File manipulation:
 45 | ```python
 46 | # Move files
 47 | workspace.fs.move_files(
 48 |     "/workspace/data/old.txt",
 49 |     "/workspace/data/new.txt"
 50 | )
 51 |
 52 | # Replace text in files
 53 | results = workspace.fs.replace_in_files(
 54 |     files=["/workspace/data/new.txt"],
 55 |     pattern="old_version",
 56 |     new_value="new_version"
 57 | )
 58 |
 59 | # Set permissions
 60 | workspace.fs.set_file_permissions(
 61 |     path="/workspace/data/script.sh",
 62 |     mode="755",
 63 |     owner="daytona"
 64 | )
 65 | ```
 66 |
 67 |
 68 | **Notes**:
 69 |
 70 |   All paths should be absolute paths within the Sandbox if not explicitly
 71 |   stated otherwise.
 72 |
 73 | <a id="daytona_sdk.filesystem.FileSystem"></a>
 74 | ## FileSystem
 75 |
 76 | ```python
 77 | class FileSystem()
 78 | ```
 79 |
 80 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L80)
 81 |
 82 | Provides file system operations within a Sandbox.
 83 |
 84 | This class implements a high-level interface to file system operations that can
 85 | be performed within a Daytona Sandbox. It supports common operations like
 86 | creating, deleting, and moving files, as well as searching file contents and
 87 | managing permissions.
 88 |
 89 | **Attributes**:
 90 |
 91 | - `instance` _WorkspaceInstance_ - The Sandbox instance this file system belongs to.
 92 |
 93 |
 94 | #### FileSystem.\_\_init\_\_
 95 |
 96 | ```python
 97 | def __init__(instance: WorkspaceInstance, toolbox_api: ToolboxApi)
 98 | ```
 99 |
100 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L92)
101 |
102 | Initializes a new FileSystem instance.
103 |
104 | **Arguments**:
105 |
106 | - `instance` _WorkspaceInstance_ - The Sandbox instance this file system belongs to.
107 | - `toolbox_api` _ToolboxApi_ - API client for Sandbox operations.
108 |
109 |
110 | #### FileSystem.create\_folder
111 |
112 | ```python
113 | @intercept_errors(message_prefix="Failed to create folder: ")
114 | def create_folder(path: str, mode: str) -> None
115 | ```
116 |
117 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L103)
118 |
119 | Creates a new directory in the Sandbox.
120 |
121 | This method creates a new directory at the specified path with the given
122 | permissions.
123 |
124 | **Arguments**:
125 |
126 | - `path` _str_ - Absolute path where the folder should be created.
127 | - `mode` _str_ - Folder permissions in octal format (e.g., "755" for rwxr-xr-x).
128 |
129 |
130 | **Example**:
131 |
132 | ```python
133 | # Create a directory with standard permissions
134 | workspace.fs.create_folder("/workspace/data", "755")
135 |
136 | # Create a private directory
137 | workspace.fs.create_folder("/workspace/secrets", "700")
138 | ```
139 |
140 |
141 | #### FileSystem.delete\_file
142 |
143 | ```python
144 | @intercept_errors(message_prefix="Failed to delete file: ")
145 | def delete_file(path: str) -> None
146 | ```
147 |
148 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L127)
149 |
150 | Deletes a file from the Sandbox.
151 |
152 | This method permanently deletes a file from the Sandbox.
153 |
154 | **Arguments**:
155 |
156 | - `path` _str_ - Absolute path to the file to delete.
157 |
158 |
159 | **Example**:
160 |
161 | ```python
162 | # Delete a file
163 | workspace.fs.delete_file("/workspace/data/old_file.txt")
164 | ```
165 |
166 |
167 | #### FileSystem.download\_file
168 |
169 | ```python
170 | @intercept_errors(message_prefix="Failed to download file: ")
171 | def download_file(path: str) -> bytes
172 | ```
173 |
174 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L146)
175 |
176 | Downloads a file from the Sandbox.
177 |
178 | This method retrieves the contents of a file from the Sandbox.
179 |
180 | **Arguments**:
181 |
182 | - `path` _str_ - Absolute path to the file to download.
183 |
184 |
185 | **Returns**:
186 |
187 | - `bytes` - The file contents as a bytes object.
188 |
189 |
190 | **Example**:
191 |
192 | ```python
193 | # Download and save a file locally
194 | content = workspace.fs.download_file("/workspace/data/file.txt")
195 | with open("local_copy.txt", "wb") as f:
196 |     f.write(content)
197 |
198 | # Download and process text content
199 | content = workspace.fs.download_file("/workspace/data/config.json")
200 | config = json.loads(content.decode('utf-8'))
201 | ```
202 |
203 |
204 | #### FileSystem.find\_files
205 |
206 | ```python
207 | @intercept_errors(message_prefix="Failed to find files: ")
208 | def find_files(path: str, pattern: str) -> List[Match]
209 | ```
210 |
211 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L174)
212 |
213 | Searches for files containing a pattern.
214 |
215 | This method searches file contents for a specified pattern, similar to
216 | the grep command.
217 |
218 | **Arguments**:
219 |
220 | - `path` _str_ - Absolute path to the file or directory to search. If the path is a directory, the search will be performed recursively.
221 | - `pattern` _str_ - Search pattern to match against file contents.
222 |
223 |
224 | **Returns**:
225 |
226 | - `List[Match]` - List of matches found in files. Each Match object includes:
227 |   - file: Path to the file containing the match
228 |   - line: The line number where the match was found
229 |   - content: The matching line content
230 |
231 |
232 | **Example**:
233 |
234 | ```python
235 | # Search for TODOs in Python files
236 | matches = workspace.fs.find_files("/workspace/src", "TODO:")
237 | for match in matches:
238 |     print(f"{match.file}:{match.line}: {match.content.strip()}")
239 | ```
240 |
241 |
242 | #### FileSystem.get\_file\_info
243 |
244 | ```python
245 | @intercept_errors(message_prefix="Failed to get file info: ")
246 | def get_file_info(path: str) -> FileInfo
247 | ```
248 |
249 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L203)
250 |
251 | Gets detailed information about a file.
252 |
253 | This method retrieves metadata about a file or directory, including its
254 | size, permissions, and timestamps.
255 |
256 | **Arguments**:
257 |
258 | - `path` _str_ - Absolute path to the file or directory.
259 |
260 |
261 | **Returns**:
262 |
263 | - `FileInfo` - Detailed file information including:
264 |   - name: File name
265 |   - is_dir: Whether the path is a directory
266 |   - size: File size in bytes
267 |   - mode: File permissions
268 |   - mod_time: Last modification timestamp
269 |   - permissions: File permissions in octal format
270 |   - owner: File owner
271 |   - group: File group
272 |
273 |
274 | **Example**:
275 |
276 | ```python
277 | # Get file metadata
278 | info = workspace.fs.get_file_info("/workspace/data/file.txt")
279 | print(f"Size: {info.size} bytes")
280 | print(f"Modified: {info.mod_time}")
281 | print(f"Mode: {info.mode}")
282 |
283 | # Check if path is a directory
284 | info = workspace.fs.get_file_info("/workspace/data")
285 | if info.is_dir:
286 |     print("Path is a directory")
287 | ```
288 |
289 |
290 | #### FileSystem.list\_files
291 |
292 | ```python
293 | @intercept_errors(message_prefix="Failed to list files: ")
294 | def list_files(path: str) -> List[FileInfo]
295 | ```
296 |
297 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L242)
298 |
299 | Lists files and directories in a given path.
300 |
301 | This method returns information about all files and directories in the
302 | specified directory, similar to the ls -l command.
303 |
304 | **Arguments**:
305 |
306 | - `path` _str_ - Absolute path to the directory to list contents from.
307 |
308 |
309 | **Returns**:
310 |
311 | - `List[FileInfo]` - List of file and directory information. Each FileInfo
312 |   object includes the same fields as described in get_file_info().
313 |
314 |
315 | **Example**:
316 |
317 | ```python
318 | # List directory contents
319 | files = workspace.fs.list_files("/workspace/data")
320 |
321 | # Print files and their sizes
322 | for file in files:
323 |     if not file.is_dir:
324 |         print(f"{file.name}: {file.size} bytes")
325 |
326 | # List only directories
327 | dirs = [f for f in files if f.is_dir]
328 | print("Subdirectories:", ", ".join(d.name for d in dirs))
329 | ```
330 |
331 |
332 | #### FileSystem.move\_files
333 |
334 | ```python
335 | @intercept_errors(message_prefix="Failed to move files: ")
336 | def move_files(source: str, destination: str) -> None
337 | ```
338 |
339 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L275)
340 |
341 | Moves files from one location to another.
342 |
343 | This method moves or renames a file or directory. The parent directory
344 | of the destination must exist.
345 |
346 | **Arguments**:
347 |
348 | - `source` _str_ - Absolute path to the source file or directory.
349 | - `destination` _str_ - Absolute path to the destination.
350 |
351 |
352 | **Example**:
353 |
354 | ```python
355 | # Rename a file
356 | workspace.fs.move_files(
357 |     "/workspace/data/old_name.txt",
358 |     "/workspace/data/new_name.txt"
359 | )
360 |
361 | # Move a file to a different directory
362 | workspace.fs.move_files(
363 |     "/workspace/data/file.txt",
364 |     "/workspace/archive/file.txt"
365 | )
366 |
367 | # Move a directory
368 | workspace.fs.move_files(
369 |     "/workspace/old_dir",
370 |     "/workspace/new_dir"
371 | )
372 | ```
373 |
374 |
375 | #### FileSystem.replace\_in\_files
376 |
377 | ```python
378 | @intercept_errors(message_prefix="Failed to replace in files: ")
379 | def replace_in_files(files: List[str], pattern: str,
380 |                      new_value: str) -> List[ReplaceResult]
381 | ```
382 |
383 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L313)
384 |
385 | Replaces text in multiple files.
386 |
387 | This method performs search and replace operations across multiple files.
388 |
389 | **Arguments**:
390 |
391 | - `files` _List[str]_ - List of absolute file paths to perform replacements in.
392 | - `pattern` _str_ - Pattern to search for.
393 | - `new_value` _str_ - Text to replace matches with.
394 |
395 |
396 | **Returns**:
397 |
398 | - `List[ReplaceResult]` - List of results indicating replacements made in
399 |   each file. Each ReplaceResult includes:
400 |   - file: Path to the modified file
401 |   - success: Whether the operation was successful
402 |   - error: Error message if the operation failed
403 |
404 |
405 | **Example**:
406 |
407 | ```python
408 | # Replace in specific files
409 | results = workspace.fs.replace_in_files(
410 |     files=["/workspace/src/file1.py", "/workspace/src/file2.py"],
411 |     pattern="old_function",
412 |     new_value="new_function"
413 | )
414 |
415 | # Print results
416 | for result in results:
417 |     if result.success:
418 |         print(f"{result.file}: {result.success}")
419 |     else:
420 |         print(f"{result.file}: {result.error}")
421 | ```
422 |
423 |
424 | #### FileSystem.search\_files
425 |
426 | ```python
427 | @intercept_errors(message_prefix="Failed to search files: ")
428 | def search_files(path: str, pattern: str) -> SearchFilesResponse
429 | ```
430 |
431 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L358)
432 |
433 | Searches for files and directories matching a pattern in their names.
434 |
435 | This method searches for files and directories whose names match the
436 | specified pattern. The pattern can be a simple string or a glob pattern.
437 |
438 | **Arguments**:
439 |
440 | - `path` _str_ - Absolute path to the root directory to start search from.
441 | - `pattern` _str_ - Pattern to match against file names. Supports glob
442 |   patterns (e.g., "*.py" for Python files).
443 |
444 |
445 | **Returns**:
446 |
447 | - `SearchFilesResponse` - Search results containing:
448 |   - files: List of matching file and directory paths
449 |
450 |
451 | **Example**:
452 |
453 | ```python
454 | # Find all Python files
455 | result = workspace.fs.search_files("/workspace", "*.py")
456 | for file in result.files:
457 |     print(file)
458 |
459 | # Find files with specific prefix
460 | result = workspace.fs.search_files("/workspace/data", "test_*")
461 | print(f"Found {len(result.files)} test files")
462 | ```
463 |
464 |
465 | #### FileSystem.set\_file\_permissions
466 |
467 | ```python
468 | @intercept_errors(message_prefix="Failed to set file permissions: ")
469 | def set_file_permissions(path: str,
470 |                          mode: str = None,
471 |                          owner: str = None,
472 |                          group: str = None) -> None
473 | ```
474 |
475 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L390)
476 |
477 | Sets permissions and ownership for a file or directory.
478 |
479 | This method allows changing the permissions and ownership of a file or
480 | directory. Any of the parameters can be None to leave that attribute
481 | unchanged.
482 |
483 | **Arguments**:
484 |
485 | - `path` _str_ - Absolute path to the file or directory.
486 | - `mode` _Optional[str]_ - File mode/permissions in octal format
487 |   (e.g., "644" for rw-r--r--).
488 | - `owner` _Optional[str]_ - User owner of the file.
489 | - `group` _Optional[str]_ - Group owner of the file.
490 |
491 |
492 | **Example**:
493 |
494 | ```python
495 | # Make a file executable
496 | workspace.fs.set_file_permissions(
497 |     path="/workspace/scripts/run.sh",
498 |     mode="755"  # rwxr-xr-x
499 | )
500 |
501 | # Change file owner
502 | workspace.fs.set_file_permissions(
503 |     path="/workspace/data/file.txt",
504 |     owner="daytona",
505 |     group="daytona"
506 | )
507 | ```
508 |
509 |
510 | #### FileSystem.upload\_file
511 |
512 | ```python
513 | @intercept_errors(message_prefix="Failed to upload file: ")
514 | def upload_file(path: str, file: bytes) -> None
515 | ```
516 |
517 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/filesystem.py#L431)
518 |
519 | Uploads a file to the Sandbox.
520 |
521 | This method uploads a file to the specified path in the Sandbox. The
522 | parent directory must exist. If a file already exists at the destination
523 | path, it will be overwritten.
524 |
525 | **Arguments**:
526 |
527 | - `path` _str_ - Absolute destination path in the Sandbox.
528 | - `file` _bytes_ - File contents as a bytes object.
529 |
530 |
531 | **Example**:
532 |
533 | ```python
534 | # Upload a text file
535 | content = b"Hello, World!"
536 | workspace.fs.upload_file("/workspace/data/hello.txt", content)
537 |
538 | # Upload a local file
539 | with open("local_file.txt", "rb") as f:
540 |     content = f.read()
541 | workspace.fs.upload_file("/workspace/data/file.txt", content)
542 |
543 | # Upload binary data
544 | import json
545 | data = {"key": "value"}
546 | content = json.dumps(data).encode('utf-8')
547 | workspace.fs.upload_file("/workspace/data/config.json", content)
548 | ```
549 |
550 |
551 | The Daytona SDK provides comprehensive file system operations through the `fs` module in Sandboxes.
552 | You can perform various operations like listing files, creating directories, reading and writing files, and more.
553 | This guide covers all available file system operations and best practices.
554 |
555 | **Examples**:
556 |
557 |   Basic file operations:
558 | ```python
559 |     workspace = daytona.create()
560 |
561 |     # Create a directory
562 |     workspace.fs.create_folder("/workspace/data", "755")
563 |
564 |     # Upload a file
565 |     with open("local_file.txt", "rb") as f:
566 |         content = f.read()
567 |     workspace.fs.upload_file("/workspace/data/file.txt", content)
568 |
569 |     # List directory contents
570 |     files = workspace.fs.list_files("/workspace")
571 |     for file in files:
572 |         print(f"Name: {file.name}")
573 |         print(f"Is directory: {file.is_dir}")
574 |         print(f"Size: {file.size}")
575 |         print(f"Modified: {file.mod_time}")
576 |
577 |     # Search file contents
578 |     matches = workspace.fs.find_files(
579 |         path="/workspace/src",
580 |         pattern="text-of-interest"
581 |     )
582 |     for match in matches:
583 |         print(f"Absolute file path: {match.file}")
584 |         print(f"Line number: {match.line}")
585 |         print(f"Line content: {match.content}")
586 |         print("
587 | ")
588 | ```
589 |
590 |   File manipulation:
591 | ```python
592 | # Move files
593 | workspace.fs.move_files(
594 |     "/workspace/data/old.txt",
595 |     "/workspace/data/new.txt"
596 | )
597 |
598 | # Replace text in files
599 | results = workspace.fs.replace_in_files(
600 |     files=["/workspace/data/new.txt"],
601 |     pattern="old_version",
602 |     new_value="new_version"
603 | )
604 |
605 | # Set permissions
606 | workspace.fs.set_file_permissions(
607 |     path="/workspace/data/script.sh",
608 |     mode="755",
609 |     owner="daytona"
610 | )
611 | ```
612 |
613 |
614 | **Notes**:
615 |
616 |   All paths should be absolute paths within the Sandbox if not explicitly
617 |   stated otherwise.
618 |
619 |
620 |


--------------------------------------------------------------------------------
/docs/python-sdk/git.mdx:
--------------------------------------------------------------------------------
  1 | ---
  2 | title: Git Operations
  3 | ---
  4 |
  5 | The Daytona SDK provides built-in Git support. This guide covers all available Git
  6 | operations and best practices. Daytona SDK provides an option to clone, check status,
  7 | and manage Git repositories in Sandboxes. You can interact with Git repositories using
  8 | the `git` module.
  9 |
 10 | **Example**:
 11 |
 12 |   Basic Git workflow:
 13 | ```python
 14 | workspace = daytona.create()
 15 |
 16 | # Clone a repository
 17 | workspace.git.clone(
 18 |     url="https://github.com/user/repo.git",
 19 |     path="/workspace/repo"
 20 | )
 21 |
 22 | # Make some changes
 23 | workspace.fs.upload_file("/workspace/repo/test.txt", "Hello, World!")
 24 |
 25 | # Stage and commit changes
 26 | workspace.git.add("/workspace/repo", ["test.txt"])
 27 | workspace.git.commit(
 28 |     path="/workspace/repo",
 29 |     message="Add test file",
 30 |     author="John Doe",
 31 |     email="john@example.com"
 32 | )
 33 |
 34 | # Push changes (with authentication)
 35 | workspace.git.push(
 36 |     path="/workspace/repo",
 37 |     username="user",
 38 |     password="token"
 39 | )
 40 | ```
 41 |
 42 |
 43 | **Notes**:
 44 |
 45 |   All paths should be absolute paths within the Sandbox if not explicitly
 46 |   stated otherwise.
 47 |
 48 | <a id="daytona_sdk.git.Git"></a>
 49 | ## Git
 50 |
 51 | ```python
 52 | class Git()
 53 | ```
 54 |
 55 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L60)
 56 |
 57 | Provides Git operations within a Sandbox.
 58 |
 59 | This class implements a high-level interface to Git operations that can be
 60 | performed within a Daytona Sandbox. It supports common Git operations like
 61 | cloning repositories, staging and committing changes, pushing and pulling
 62 | changes, and checking repository status.
 63 |
 64 | **Attributes**:
 65 |
 66 | - `workspace` _Workspace_ - The parent Sandbox instance.
 67 | - `instance` _WorkspaceInstance_ - The Sandbox instance this Git handler belongs to.
 68 |
 69 |
 70 | **Example**:
 71 |
 72 | ```python
 73 | # Clone a repository
 74 | workspace.git.clone(
 75 |     url="https://github.com/user/repo.git",
 76 |     path="/workspace/repo"
 77 | )
 78 |
 79 | # Check repository status
 80 | status = workspace.git.status("/workspace/repo")
 81 | print(f"Modified files: {status.modified}")
 82 |
 83 | # Stage and commit changes
 84 | workspace.git.add("/workspace/repo", ["file.txt"])
 85 | workspace.git.commit(
 86 |     path="/workspace/repo",
 87 |     message="Update file",
 88 |     author="John Doe",
 89 |     email="john@example.com"
 90 | )
 91 | ```
 92 |
 93 |
 94 | #### Git.\_\_init\_\_
 95 |
 96 | ```python
 97 | def __init__(workspace: "Workspace", toolbox_api: ToolboxApi,
 98 |              instance: WorkspaceInstance)
 99 | ```
100 |
101 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L95)
102 |
103 | Initializes a new Git handler instance.
104 |
105 | **Arguments**:
106 |
107 | - `workspace` _Workspace_ - The parent Sandbox instance.
108 | - `toolbox_api` _ToolboxApi_ - API client for Sandbox operations.
109 | - `instance` _WorkspaceInstance_ - The Sandbox instance this Git handler belongs to.
110 |
111 |
112 | #### Git.add
113 |
114 | ```python
115 | @intercept_errors(message_prefix="Failed to add files: ")
116 | def add(path: str, files: List[str]) -> None
117 | ```
118 |
119 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L113)
120 |
121 | Stages files for commit.
122 |
123 | This method stages the specified files for the next commit, similar to
124 | running 'git add' on the command line.
125 |
126 | **Arguments**:
127 |
128 | - `path` _str_ - Absolute path to the Git repository root.
129 | - `files` _List[str]_ - List of file paths or directories to stage, relative to the repository root.
130 |
131 |
132 | **Example**:
133 |
134 | ```python
135 | # Stage a single file
136 | workspace.git.add("/workspace/repo", ["file.txt"])
137 |
138 | # Stage multiple files
139 | workspace.git.add("/workspace/repo", [
140 |     "src/main.py",
141 |     "tests/test_main.py",
142 |     "README.md"
143 | ])
144 | ```
145 |
146 |
147 | #### Git.branches
148 |
149 | ```python
150 | @intercept_errors(message_prefix="Failed to list branches: ")
151 | def branches(path: str) -> ListBranchResponse
152 | ```
153 |
154 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L145)
155 |
156 | Lists branches in the repository.
157 |
158 | This method returns information about all branches in the repository.
159 |
160 | **Arguments**:
161 |
162 | - `path` _str_ - Absolute path to the Git repository root.
163 |
164 |
165 | **Returns**:
166 |
167 | - `ListBranchResponse` - List of branches in the repository.
168 |
169 |
170 | **Example**:
171 |
172 | ```python
173 | response = workspace.git.branches("/workspace/repo")
174 | print(f"Branches: {response.branches}")
175 | ```
176 |
177 |
178 | #### Git.clone
179 |
180 | ```python
181 | @intercept_errors(message_prefix="Failed to clone repository: ")
182 | def clone(url: str,
183 |           path: str,
184 |           branch: Optional[str] = None,
185 |           commit_id: Optional[str] = None,
186 |           username: Optional[str] = None,
187 |           password: Optional[str] = None) -> None
188 | ```
189 |
190 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L168)
191 |
192 | Clones a Git repository.
193 |
194 | This method clones a Git repository into the specified path. It supports
195 | cloning specific branches or commits, and can authenticate with the remote
196 | repository if credentials are provided.
197 |
198 | **Arguments**:
199 |
200 | - `url` _str_ - Repository URL to clone from.
201 | - `path` _str_ - Absolute path where the repository should be cloned.
202 | - `branch` _Optional[str]_ - Specific branch to clone. If not specified,
203 |   clones the default branch.
204 | - `commit_id` _Optional[str]_ - Specific commit to clone. If specified,
205 |   the repository will be left in a detached HEAD state at this commit.
206 | - `username` _Optional[str]_ - Git username for authentication.
207 | - `password` _Optional[str]_ - Git password or token for authentication.
208 |
209 |
210 | **Example**:
211 |
212 | ```python
213 | # Clone the default branch
214 | workspace.git.clone(
215 |     url="https://github.com/user/repo.git",
216 |     path="/workspace/repo"
217 | )
218 |
219 | # Clone a specific branch with authentication
220 | workspace.git.clone(
221 |     url="https://github.com/user/private-repo.git",
222 |     path="/workspace/private",
223 |     branch="develop",
224 |     username="user",
225 |     password="token"
226 | )
227 |
228 | # Clone a specific commit
229 | workspace.git.clone(
230 |     url="https://github.com/user/repo.git",
231 |     path="/workspace/repo-old",
232 |     commit_id="abc123"
233 | )
234 | ```
235 |
236 |
237 | #### Git.commit
238 |
239 | ```python
240 | @intercept_errors(message_prefix="Failed to commit changes: ")
241 | def commit(path: str, message: str, author: str, email: str) -> None
242 | ```
243 |
244 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L231)
245 |
246 | Commits staged changes.
247 |
248 | This method creates a new commit with the staged changes. Make sure to stage
249 | changes using the add() method before committing.
250 |
251 | **Arguments**:
252 |
253 | - `path` _str_ - Absolute path to the Git repository root.
254 | - `message` _str_ - Commit message describing the changes.
255 | - `author` _str_ - Name of the commit author.
256 | - `email` _str_ - Email address of the commit author.
257 |
258 |
259 | **Example**:
260 |
261 | ```python
262 | # Stage and commit changes
263 | workspace.git.add("/workspace/repo", ["README.md"])
264 | workspace.git.commit(
265 |     path="/workspace/repo",
266 |     message="Update documentation",
267 |     author="John Doe",
268 |     email="john@example.com"
269 | )
270 | ```
271 |
272 |
273 | #### Git.push
274 |
275 | ```python
276 | @intercept_errors(message_prefix="Failed to push changes: ")
277 | def push(path: str,
278 |          username: Optional[str] = None,
279 |          password: Optional[str] = None) -> None
280 | ```
281 |
282 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L266)
283 |
284 | Pushes local commits to the remote repository.
285 |
286 | This method pushes all local commits on the current branch to the remote
287 | repository. If the remote repository requires authentication, provide
288 | username and password/token.
289 |
290 | **Arguments**:
291 |
292 | - `path` _str_ - Absolute path to the Git repository root.
293 | - `username` _Optional[str]_ - Git username for authentication.
294 | - `password` _Optional[str]_ - Git password or token for authentication.
295 |
296 |
297 | **Example**:
298 |
299 | ```python
300 | # Push without authentication (for public repos or SSH)
301 | workspace.git.push("/workspace/repo")
302 |
303 | # Push with authentication
304 | workspace.git.push(
305 |     path="/workspace/repo",
306 |     username="user",
307 |     password="github_token"
308 | )
309 | ```
310 |
311 |
312 | #### Git.pull
313 |
314 | ```python
315 | @intercept_errors(message_prefix="Failed to pull changes: ")
316 | def pull(path: str,
317 |          username: Optional[str] = None,
318 |          password: Optional[str] = None) -> None
319 | ```
320 |
321 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L303)
322 |
323 | Pulls changes from the remote repository.
324 |
325 | This method fetches and merges changes from the remote repository into
326 | the current branch. If the remote repository requires authentication,
327 | provide username and password/token.
328 |
329 | **Arguments**:
330 |
331 | - `path` _str_ - Absolute path to the Git repository root.
332 | - `username` _Optional[str]_ - Git username for authentication.
333 | - `password` _Optional[str]_ - Git password or token for authentication.
334 |
335 |
336 | **Example**:
337 |
338 | ```python
339 | # Pull without authentication
340 | workspace.git.pull("/workspace/repo")
341 |
342 | # Pull with authentication
343 | workspace.git.pull(
344 |     path="/workspace/repo",
345 |     username="user",
346 |     password="github_token"
347 | )
348 | ```
349 |
350 |
351 | #### Git.status
352 |
353 | ```python
354 | @intercept_errors(message_prefix="Failed to get status: ")
355 | def status(path: str) -> GitStatus
356 | ```
357 |
358 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/git.py#L340)
359 |
360 | Gets the current Git repository status.
361 |
362 | This method returns detailed information about the current state of the
363 | repository, including staged, unstaged, and untracked files.
364 |
365 | **Arguments**:
366 |
367 | - `path` _str_ - Absolute path to the Git repository root.
368 |
369 |
370 | **Returns**:
371 |
372 | - `GitStatus` - Repository status information including:
373 |   - current_branch: Current branch name
374 |   - file_status: List of file statuses
375 |   - ahead: Number of local commits not pushed to remote
376 |   - behind: Number of remote commits not pulled locally
377 |   - branch_published: Whether the branch has been published to the remote repository
378 |
379 |
380 | **Example**:
381 |
382 | ```python
383 | status = workspace.git.status("/workspace/repo")
384 | print(f"On branch: {status.current_branch}")
385 | print(f"Commits ahead: {status.ahead}")
386 | print(f"Commits behind: {status.behind}")
387 | ```
388 |
389 |
390 | The Daytona SDK provides built-in Git support. This guide covers all available Git
391 | operations and best practices. Daytona SDK provides an option to clone, check status,
392 | and manage Git repositories in Sandboxes. You can interact with Git repositories using
393 | the `git` module.
394 |
395 | **Example**:
396 |
397 |   Basic Git workflow:
398 | ```python
399 | workspace = daytona.create()
400 |
401 | # Clone a repository
402 | workspace.git.clone(
403 |     url="https://github.com/user/repo.git",
404 |     path="/workspace/repo"
405 | )
406 |
407 | # Make some changes
408 | workspace.fs.upload_file("/workspace/repo/test.txt", "Hello, World!")
409 |
410 | # Stage and commit changes
411 | workspace.git.add("/workspace/repo", ["test.txt"])
412 | workspace.git.commit(
413 |     path="/workspace/repo",
414 |     message="Add test file",
415 |     author="John Doe",
416 |     email="john@example.com"
417 | )
418 |
419 | # Push changes (with authentication)
420 | workspace.git.push(
421 |     path="/workspace/repo",
422 |     username="user",
423 |     password="token"
424 | )
425 | ```
426 |
427 |
428 | **Notes**:
429 |
430 |   All paths should be absolute paths within the Sandbox if not explicitly
431 |   stated otherwise.
432 |
433 |
434 |


--------------------------------------------------------------------------------
/docs/python-sdk/lsp-server.mdx:
--------------------------------------------------------------------------------
  1 | ---
  2 | title: Language Server Protocol
  3 | ---
  4 |
  5 | The Daytona SDK provides Language Server Protocol (LSP) support through Sandbox instances.
  6 | This enables advanced language features like code completion, diagnostics, and more.
  7 |
  8 | **Example**:
  9 |
 10 |   Basic LSP server usage:
 11 | ```python
 12 | workspace = daytona.create()
 13 |
 14 | # Create and start LSP server
 15 | lsp = workspace.create_lsp_server("typescript", "/workspace/project")
 16 | lsp.start()
 17 |
 18 | # Open a file for editing
 19 | lsp.did_open("/workspace/project/src/index.ts")
 20 |
 21 | # Get completions at a position
 22 | pos = Position(line=10, character=15)
 23 | completions = lsp.completions("/workspace/project/src/index.ts", pos)
 24 | print(f"Completions: {completions}")
 25 |
 26 | # Get document symbols
 27 | symbols = lsp.document_symbols("/workspace/project/src/index.ts")
 28 | for symbol in symbols:
 29 |     print(f"{symbol.name}: {symbol.kind}")
 30 |
 31 | # Clean up
 32 | lsp.did_close("/workspace/project/src/index.ts")
 33 | lsp.stop()
 34 | ```
 35 |
 36 |
 37 | **Notes**:
 38 |
 39 |   The LSP server must be started with start() before using any other methods,
 40 |   and should be stopped with stop() when no longer needed to free resources.
 41 |
 42 | <a id="daytona_sdk.lsp_server.LspServer"></a>
 43 | ## LspServer
 44 |
 45 | ```python
 46 | class LspServer()
 47 | ```
 48 |
 49 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L86)
 50 |
 51 | Provides Language Server Protocol functionality for code intelligence.
 52 |
 53 | This class implements a subset of the Language Server Protocol (LSP) to provide
 54 | IDE-like features such as code completion, symbol search, and more.
 55 |
 56 | **Attributes**:
 57 |
 58 | - `language_id` _LspLanguageId_ - The language server type (e.g., "python", "typescript").
 59 | - `path_to_project` _str_ - Absolute path to the project root directory.
 60 | - `instance` _WorkspaceInstance_ - The Sandbox instance this server belongs to.
 61 |
 62 |
 63 | #### LspServer.\_\_init\_\_
 64 |
 65 | ```python
 66 | def __init__(language_id: LspLanguageId, path_to_project: str,
 67 |              toolbox_api: ToolboxApi, instance: WorkspaceInstance)
 68 | ```
 69 |
 70 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L98)
 71 |
 72 | Initializes a new LSP server instance.
 73 |
 74 | **Arguments**:
 75 |
 76 | - `language_id` _LspLanguageId_ - The language server type (e.g., LspLanguageId.TYPESCRIPT).
 77 | - `path_to_project` _str_ - Absolute path to the project root directory.
 78 | - `toolbox_api` _ToolboxApi_ - API client for Sandbox operations.
 79 | - `instance` _WorkspaceInstance_ - The Sandbox instance this server belongs to.
 80 |
 81 |
 82 | #### LspServer.start
 83 |
 84 | ```python
 85 | @intercept_errors(message_prefix="Failed to start LSP server: ")
 86 | def start() -> None
 87 | ```
 88 |
 89 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L119)
 90 |
 91 | Starts the language server.
 92 |
 93 | This method must be called before using any other LSP functionality.
 94 | It initializes the language server for the specified language and project.
 95 |
 96 | **Example**:
 97 |
 98 | ```python
 99 | lsp = workspace.create_lsp_server("typescript", "/workspace/project")
100 | lsp.start()  # Initialize the server
101 | # Now ready for LSP operations
102 | ```
103 |
104 |
105 | #### LspServer.stop
106 |
107 | ```python
108 | @intercept_errors(message_prefix="Failed to stop LSP server: ")
109 | def stop() -> None
110 | ```
111 |
112 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L141)
113 |
114 | Stops the language server.
115 |
116 | This method should be called when the LSP server is no longer needed to
117 | free up system resources.
118 |
119 | **Example**:
120 |
121 | ```python
122 | # When done with LSP features
123 | lsp.stop()  # Clean up resources
124 | ```
125 |
126 |
127 | #### LspServer.did\_open
128 |
129 | ```python
130 | @intercept_errors(message_prefix="Failed to open file: ")
131 | def did_open(path: str) -> None
132 | ```
133 |
134 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L162)
135 |
136 | Notifies the language server that a file has been opened.
137 |
138 | This method should be called when a file is opened in the editor to enable
139 | language features like diagnostics and completions for that file. The server
140 | will begin tracking the file's contents and providing language features.
141 |
142 | **Arguments**:
143 |
144 | - `path` _str_ - Absolute path to the opened file.
145 |
146 |
147 | **Example**:
148 |
149 | ```python
150 | # When opening a file for editing
151 | lsp.did_open("/workspace/project/src/index.ts")
152 | # Now can get completions, symbols, etc. for this file
153 | ```
154 |
155 |
156 | #### LspServer.did\_close
157 |
158 | ```python
159 | @intercept_errors(message_prefix="Failed to close file: ")
160 | def did_close(path: str) -> None
161 | ```
162 |
163 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L189)
164 |
165 | Notify the language server that a file has been closed.
166 |
167 | This method should be called when a file is closed in the editor to allow
168 | the language server to clean up any resources associated with that file.
169 |
170 | **Arguments**:
171 |
172 | - `path` _str_ - Absolute path to the closed file.
173 |
174 |
175 | **Example**:
176 |
177 | ```python
178 | # When done editing a file
179 | lsp.did_close("/workspace/project/src/index.ts")
180 | ```
181 |
182 |
183 | #### LspServer.document\_symbols
184 |
185 | ```python
186 | @intercept_errors(message_prefix="Failed to get symbols from document: ")
187 | def document_symbols(path: str) -> List[LspSymbol]
188 | ```
189 |
190 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L213)
191 |
192 | Gets symbol information from a document.
193 |
194 | This method returns information about all symbols (functions, classes,
195 | variables, etc.) defined in the specified document.
196 |
197 | **Arguments**:
198 |
199 | - `path` _str_ - Absolute path to the file to get symbols from.
200 |
201 |
202 | **Returns**:
203 |
204 | - `List[LspSymbol]` - List of symbols in the document. Each symbol includes:
205 |   - name: The symbol's name
206 |   - kind: The symbol's kind (function, class, variable, etc.)
207 |   - location: The location of the symbol in the file
208 |
209 |
210 | **Example**:
211 |
212 | ```python
213 | # Get all symbols in a file
214 | symbols = lsp.document_symbols("/workspace/project/src/index.ts")
215 | for symbol in symbols:
216 |     print(f"{symbol.kind} {symbol.name}: {symbol.location}")
217 | ```
218 |
219 |
220 | #### LspServer.workspace\_symbols
221 |
222 | ```python
223 | @intercept_errors(message_prefix="Failed to get symbols from workspace: ")
224 | def workspace_symbols(query: str) -> List[LspSymbol]
225 | ```
226 |
227 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L244)
228 |
229 | Searches for symbols across the entire Sandbox.
230 |
231 | This method searches for symbols matching the query string across all files
232 | in the Sandbox. It's useful for finding declarations and definitions
233 | without knowing which file they're in.
234 |
235 | **Arguments**:
236 |
237 | - `query` _str_ - Search query to match against symbol names.
238 |
239 |
240 | **Returns**:
241 |
242 | - `List[LspSymbol]` - List of matching symbols from all files. Each symbol
243 |   includes:
244 |   - name: The symbol's name
245 |   - kind: The symbol's kind (function, class, variable, etc.)
246 |   - location: The location of the symbol in the file
247 |
248 |
249 | **Example**:
250 |
251 | ```python
252 | # Search for all symbols containing "User"
253 | symbols = lsp.workspace_symbols("User")
254 | for symbol in symbols:
255 |     print(f"{symbol.name} in {symbol.location}")
256 | ```
257 |
258 |
259 | #### LspServer.completions
260 |
261 | ```python
262 | @intercept_errors(message_prefix="Failed to get completions: ")
263 | def completions(path: str, position: Position) -> CompletionList
264 | ```
265 |
266 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L277)
267 |
268 | Gets completion suggestions at a position in a file.
269 |
270 | **Arguments**:
271 |
272 | - `path` _str_ - Absolute path to the file.
273 | - `position` _Position_ - Cursor position to get completions for.
274 |
275 |
276 | **Returns**:
277 |
278 | - `CompletionList` - List of completion suggestions. The list includes:
279 |   - isIncomplete: Whether more items might be available
280 |   - items: List of completion items, each containing:
281 |   - label: The text to insert
282 |   - kind: The kind of completion
283 |   - detail: Additional details about the item
284 |   - documentation: Documentation for the item
285 |   - sortText: Text used to sort the item in the list
286 |   - filterText: Text used to filter the item
287 |   - insertText: The actual text to insert (if different from label)
288 |
289 |
290 | **Example**:
291 |
292 | ```python
293 | # Get completions at a specific position
294 | pos = Position(line=10, character=15)
295 | completions = lsp.completions("/workspace/project/src/index.ts", pos)
296 | for item in completions.items:
297 |     print(f"{item.label} ({item.kind}): {item.detail}")
298 | ```
299 |
300 |
301 | The Daytona SDK provides Language Server Protocol (LSP) support through Sandbox instances.
302 | This enables advanced language features like code completion, diagnostics, and more.
303 |
304 | **Example**:
305 |
306 |   Basic LSP server usage:
307 | ```python
308 | workspace = daytona.create()
309 |
310 | # Create and start LSP server
311 | lsp = workspace.create_lsp_server("typescript", "/workspace/project")
312 | lsp.start()
313 |
314 | # Open a file for editing
315 | lsp.did_open("/workspace/project/src/index.ts")
316 |
317 | # Get completions at a position
318 | pos = Position(line=10, character=15)
319 | completions = lsp.completions("/workspace/project/src/index.ts", pos)
320 | print(f"Completions: {completions}")
321 |
322 | # Get document symbols
323 | symbols = lsp.document_symbols("/workspace/project/src/index.ts")
324 | for symbol in symbols:
325 |     print(f"{symbol.name}: {symbol.kind}")
326 |
327 | # Clean up
328 | lsp.did_close("/workspace/project/src/index.ts")
329 | lsp.stop()
330 | ```
331 |
332 |
333 | **Notes**:
334 |
335 |   The LSP server must be started with start() before using any other methods,
336 |   and should be stopped with stop() when no longer needed to free resources.
337 |
338 |
339 | <a id="daytona_sdk.lsp_server.Position"></a>
340 | ## Position
341 |
342 | ```python
343 | class Position()
344 | ```
345 |
346 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L64)
347 |
348 | Represents a position in a text document.
349 |
350 | This class represents a zero-based position within a text document,
351 | specified by line number and character offset.
352 |
353 | **Attributes**:
354 |
355 | - `line` _int_ - Zero-based line number in the document.
356 | - `character` _int_ - Zero-based character offset on the line.
357 |
358 |
359 | #### Position.\_\_init\_\_
360 |
361 | ```python
362 | def __init__(line: int, character: int)
363 | ```
364 |
365 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/lsp_server.py#L75)
366 |
367 | Initialize a new Position instance.
368 |
369 | **Arguments**:
370 |
371 | - `line` _int_ - Zero-based line number in the document.
372 | - `character` _int_ - Zero-based character offset on the line.
373 |
374 |
375 |


--------------------------------------------------------------------------------
/docs/python-sdk/process.mdx:
--------------------------------------------------------------------------------
  1 | ---
  2 | title: Process and Code Execution
  3 | ---
  4 |
  5 | <a id="daytona_sdk.process.Process"></a>
  6 | ## Process
  7 |
  8 | ```python
  9 | class Process()
 10 | ```
 11 |
 12 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L57)
 13 |
 14 | Handles process and code execution within a Sandbox.
 15 |
 16 | This class provides methods for executing shell commands and running code in
 17 | the Sandbox environment.
 18 |
 19 | **Attributes**:
 20 |
 21 | - `code_toolbox` _WorkspacePythonCodeToolbox_ - Language-specific code execution toolbox.
 22 | - `toolbox_api` _ToolboxApi_ - API client for Sandbox operations.
 23 | - `instance` _WorkspaceInstance_ - The Sandbox instance this process belongs to.
 24 |
 25 |
 26 | #### Process.\_\_init\_\_
 27 |
 28 | ```python
 29 | def __init__(code_toolbox: WorkspacePythonCodeToolbox, toolbox_api: ToolboxApi,
 30 |              instance: WorkspaceInstance)
 31 | ```
 32 |
 33 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L69)
 34 |
 35 | Initialize a new Process instance.
 36 |
 37 | **Arguments**:
 38 |
 39 | - `code_toolbox` _WorkspacePythonCodeToolbox_ - Language-specific code execution toolbox.
 40 | - `toolbox_api` _ToolboxApi_ - API client for Sandbox operations.
 41 | - `instance` _WorkspaceInstance_ - The Sandbox instance this process belongs to.
 42 |
 43 |
 44 | #### Process.exec
 45 |
 46 | ```python
 47 | @intercept_errors(message_prefix="Failed to execute command: ")
 48 | def exec(command: str,
 49 |          cwd: Optional[str] = None,
 50 |          timeout: Optional[int] = None) -> ExecuteResponse
 51 | ```
 52 |
 53 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L87)
 54 |
 55 | Execute a shell command in the Sandbox.
 56 |
 57 | **Arguments**:
 58 |
 59 | - `command` _str_ - Shell command to execute.
 60 | - `cwd` _Optional[str]_ - Working directory for command execution. If not
 61 |   specified, uses the Sandbox root directory.
 62 | - `timeout` _Optional[int]_ - Maximum time in seconds to wait for the command
 63 |   to complete. 0 means wait indefinitely.
 64 |
 65 |
 66 | **Returns**:
 67 |
 68 | - `ExecuteResponse` - Command execution results containing:
 69 |   - exit_code: The command's exit status
 70 |   - result: Standard output from the command
 71 |
 72 |
 73 | **Example**:
 74 |
 75 | ```python
 76 | # Simple command
 77 | response = workspace.process.exec("echo 'Hello'")
 78 | print(response.result)  # Prints: Hello
 79 |
 80 | # Command with working directory
 81 | result = workspace.process.exec("ls", cwd="/workspace/src")
 82 |
 83 | # Command with timeout
 84 | result = workspace.process.exec("sleep 10", timeout=5)
 85 | ```
 86 |
 87 |
 88 | #### Process.code\_run
 89 |
 90 | ```python
 91 | def code_run(code: str,
 92 |              params: Optional[CodeRunParams] = None,
 93 |              timeout: Optional[int] = None) -> ExecuteResponse
 94 | ```
 95 |
 96 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L126)
 97 |
 98 | Executes code in the Sandbox using the appropriate language runtime.
 99 |
100 | **Arguments**:
101 |
102 | - `code` _str_ - Code to execute.
103 | - `params` _Optional[CodeRunParams]_ - Parameters for code execution.
104 | - `timeout` _Optional[int]_ - Maximum time in seconds to wait for the code
105 |   to complete. 0 means wait indefinitely.
106 |
107 |
108 | **Returns**:
109 |
110 | - `ExecuteResponse` - Code execution result containing:
111 |   - exit_code: The execution's exit status
112 |   - result: Standard output from the code
113 |
114 |
115 | **Example**:
116 |
117 | ```python
118 | # Run Python code
119 | response = workspace.process.code_run('''
120 |     x = 10
121 |     y = 20
122 |     print(f"Sum: {x + y}")
123 | ''')
124 | print(response.result)  # Prints: Sum: 30
125 | ```
126 |
127 |
128 | #### Process.create\_session
129 |
130 | ```python
131 | @intercept_errors(message_prefix="Failed to create session: ")
132 | def create_session(session_id: str) -> None
133 | ```
134 |
135 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L155)
136 |
137 | Create a new long-running background session in the Sandbox.
138 |
139 | Sessions are background processes that maintain state between commands, making them ideal for
140 | scenarios requiring multiple related commands or persistent environment setup. You can run
141 | long-running commands and monitor process status.
142 |
143 | **Arguments**:
144 |
145 | - `session_id` _str_ - Unique identifier for the new session.
146 |
147 |
148 | **Example**:
149 |
150 | ```python
151 | # Create a new session
152 | session_id = "my-session"
153 | workspace.process.create_session(session_id)
154 | session = workspace.process.get_session(session_id)
155 | # Do work...
156 | workspace.process.delete_session(session_id)
157 | ```
158 |
159 |
160 | #### Process.get\_session
161 |
162 | ```python
163 | @intercept_errors(message_prefix="Failed to get session: ")
164 | def get_session(session_id: str) -> Session
165 | ```
166 |
167 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L182)
168 |
169 | Get a session in the Sandbox.
170 |
171 | **Arguments**:
172 |
173 | - `session_id` _str_ - Unique identifier of the session to retrieve.
174 |
175 |
176 | **Returns**:
177 |
178 | - `Session` - Session information including:
179 |   - session_id: The session's unique identifier
180 |   - commands: List of commands executed in the session
181 |
182 |
183 | **Example**:
184 |
185 | ```python
186 | session = workspace.process.get_session("my-session")
187 | for cmd in session.commands:
188 |     print(f"Command: {cmd.command}")
189 | ```
190 |
191 |
192 | #### Process.get\_session\_command
193 |
194 | ```python
195 | @intercept_errors(message_prefix="Failed to get session command: ")
196 | def get_session_command(session_id: str, command_id: str) -> Command
197 | ```
198 |
199 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L206)
200 |
201 | Get information about a specific command executed in a session.
202 |
203 | **Arguments**:
204 |
205 | - `session_id` _str_ - Unique identifier of the session.
206 | - `command_id` _str_ - Unique identifier of the command.
207 |
208 |
209 | **Returns**:
210 |
211 | - `Command` - Command information including:
212 |   - id: The command's unique identifier
213 |   - command: The executed command string
214 |   - exit_code: Command's exit status (if completed)
215 |
216 |
217 | **Example**:
218 |
219 | ```python
220 | cmd = workspace.process.get_session_command("my-session", "cmd-123")
221 | if cmd.exit_code == 0:
222 |     print(f"Command {cmd.command} completed successfully")
223 | ```
224 |
225 |
226 | #### Process.execute\_session\_command
227 |
228 | ```python
229 | @intercept_errors(message_prefix="Failed to execute session command: ")
230 | def execute_session_command(
231 |         session_id: str,
232 |         req: SessionExecuteRequest,
233 |         timeout: Optional[int] = None) -> SessionExecuteResponse
234 | ```
235 |
236 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L233)
237 |
238 | Executes a command in the session.
239 |
240 | **Arguments**:
241 |
242 | - `session_id` _str_ - Unique identifier of the session to use.
243 | - `req` _SessionExecuteRequest_ - Command execution request containing:
244 |   - command: The command to execute
245 |   - var_async: Whether to execute asynchronously
246 |
247 |
248 | **Returns**:
249 |
250 | - `SessionExecuteResponse` - Command execution results containing:
251 |   - cmd_id: Unique identifier for the executed command
252 |   - output: Command output (if synchronous execution)
253 |   - exit_code: Command exit status (if synchronous execution)
254 |
255 |
256 | **Example**:
257 |
258 | ```python
259 | # Execute commands in sequence, maintaining state
260 | session_id = "my-session"
261 |
262 | # Change directory
263 | req = SessionExecuteRequest(command="cd /workspace")
264 | workspace.process.execute_session_command(session_id, req)
265 |
266 | # Create a file
267 | req = SessionExecuteRequest(command="echo 'Hello' > test.txt")
268 | workspace.process.execute_session_command(session_id, req)
269 |
270 | # Read the file
271 | req = SessionExecuteRequest(command="cat test.txt")
272 | result = workspace.process.execute_session_command(session_id, req)
273 | print(result.output)  # Prints: Hello
274 | ```
275 |
276 |
277 | #### Process.get\_session\_command\_logs
278 |
279 | ```python
280 | @intercept_errors(message_prefix="Failed to get session command logs: ")
281 | def get_session_command_logs(session_id: str, command_id: str) -> str
282 | ```
283 |
284 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L275)
285 |
286 | Get the logs for a command executed in a session.
287 |
288 | This method retrieves the complete output (stdout and stderr) from a
289 | command executed in a session. It's particularly useful for checking
290 | the output of asynchronous commands.
291 |
292 | **Arguments**:
293 |
294 | - `session_id` _str_ - Unique identifier of the session.
295 | - `command_id` _str_ - Unique identifier of the command.
296 |
297 |
298 | **Returns**:
299 |
300 | - `str` - Complete command output including both stdout and stderr.
301 |
302 |
303 | **Example**:
304 |
305 | ```python
306 | # Execute a long-running command asynchronously
307 | req = SessionExecuteRequest(
308 |     command="sleep 5; echo 'Done'",
309 |     var_async=True
310 | )
311 | response = workspace.process.execute_session_command("my-session", req)
312 |
313 | # Wait a bit, then get the logs
314 | import time
315 | time.sleep(6)
316 | logs = workspace.process.get_session_command_logs(
317 |     "my-session",
318 |     response.command_id
319 | )
320 | print(logs)  # Prints: Done
321 | ```
322 |
323 |
324 | #### Process.list\_sessions
325 |
326 | ```python
327 | @intercept_errors(message_prefix="Failed to list sessions: ")
328 | def list_sessions() -> List[Session]
329 | ```
330 |
331 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L315)
332 |
333 | List all sessions in the Sandbox.
334 |
335 | **Returns**:
336 |
337 | - `List[Session]` - List of all sessions in the Sandbox.
338 |
339 |
340 | **Example**:
341 |
342 | ```python
343 | sessions = workspace.process.list_sessions()
344 | for session in sessions:
345 |     print(f"Session {session.session_id}:")
346 |     print(f"  Commands: {len(session.commands)}")
347 | ```
348 |
349 |
350 | #### Process.delete\_session
351 |
352 | ```python
353 | @intercept_errors(message_prefix="Failed to delete session: ")
354 | def delete_session(session_id: str) -> None
355 | ```
356 |
357 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/process.py#L334)
358 |
359 | Delete an interactive session from the Sandbox.
360 |
361 | This method terminates and removes a session, cleaning up any resources
362 | associated with it.
363 |
364 | **Arguments**:
365 |
366 | - `session_id` _str_ - Unique identifier of the session to delete.
367 |
368 |
369 | **Example**:
370 |
371 | ```python
372 | # Create and use a session
373 | workspace.process.create_session("temp-session")
374 | # ... use the session ...
375 |
376 | # Clean up when done
377 | workspace.process.delete_session("temp-session")
378 | ```
379 |
380 |
381 |
382 | <a id="daytona_sdk.common.code_run_params.CodeRunParams"></a>
383 | ## CodeRunParams
384 |
385 | ```python
386 | @dataclass
387 | class CodeRunParams()
388 | ```
389 |
390 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/common/code_run_params.py#L5)
391 |
392 | Parameters for code execution.
393 |
394 | The Daytona SDK provides powerful process and code execution capabilities through
395 | the `process` module in Sandboxes. This guide covers all available process operations
396 | and best practices.
397 |
398 | **Example**:
399 |
400 |   Basic command execution:
401 | ```python
402 | workspace = daytona.create()
403 |
404 | # Execute a shell command
405 | response = workspace.process.exec("ls -la")
406 | print(response.result)
407 |
408 | # Run Python code
409 | response = workspace.process.code_run("print('Hello, World!')")
410 | print(response.result)
411 | ```
412 |
413 |   Using interactive sessions:
414 | ```python
415 | # Create a new session
416 | session_id = "my-session"
417 | workspace.process.create_session(session_id)
418 |
419 | # Execute commands in the session
420 | req = SessionExecuteRequest(command="cd /workspace", var_async=False)
421 | workspace.process.execute_session_command(session_id, req)
422 |
423 | req = SessionExecuteRequest(command="pwd", var_async=False)
424 | response = workspace.process.execute_session_command(session_id, req)
425 | print(response.result)  # Should print "/workspace"
426 |
427 | # Clean up
428 | workspace.process.delete_session(session_id)
429 | ```
430 |
431 |
432 |


--------------------------------------------------------------------------------
/docs/python-sdk/sandbox.mdx:
--------------------------------------------------------------------------------
  1 | ---
  2 | title: Sandbox
  3 | ---
  4 |
  5 | The Daytona SDK core Sandbox functionality.
  6 |
  7 | Provides the main Workspace class representing a Daytona Sandbox that coordinates file system,
  8 | Git, process execution, and LSP functionality. It serves as the central point
  9 | for interacting with Daytona Sandboxes.
 10 |
 11 | **Example**:
 12 |
 13 |   Basic Sandbox operations:
 14 | ```python
 15 | from daytona_sdk import Daytona
 16 | daytona = Daytona()
 17 | workspace = daytona.create()
 18 |
 19 | # File operations
 20 | workspace.fs.upload_file("/workspace/test.txt", b"Hello, World!")
 21 | content = workspace.fs.download_file("/workspace/test.txt")
 22 |
 23 | # Git operations
 24 | workspace.git.clone("https://github.com/user/repo.git")
 25 |
 26 | # Process execution
 27 | response = workspace.process.exec("ls -la")
 28 | print(response.result)
 29 |
 30 | # LSP functionality
 31 | lsp = workspace.create_lsp_server("python", "/workspace/project")
 32 | lsp.did_open("/workspace/project/src/index.ts")
 33 | completions = lsp.completions("/workspace/project/src/index.ts", Position(line=10, character=15))
 34 | print(completions)
 35 | ```
 36 |
 37 |
 38 | **Notes**:
 39 |
 40 |   The Sandbox must be in a 'started' state before performing operations.
 41 |
 42 | <a id="daytona_sdk.workspace.Workspace"></a>
 43 | ## Workspace
 44 |
 45 | ```python
 46 | class Workspace()
 47 | ```
 48 |
 49 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L181)
 50 |
 51 | Represents a Daytona Sandbox.
 52 |
 53 | A Sandbox provides file system operations, Git operations, process execution,
 54 | and LSP functionality. It serves as the main interface for interacting with
 55 | a Daytona Sandbox.
 56 |
 57 | **Attributes**:
 58 |
 59 | - `id` _str_ - Unique identifier for the Sandbox.
 60 | - `instance` _WorkspaceInstance_ - The underlying Sandbox instance.
 61 | - `code_toolbox` _WorkspaceCodeToolbox_ - Language-specific toolbox implementation.
 62 | - `fs` _FileSystem_ - File system operations interface.
 63 | - `git` _Git_ - Git operations interface.
 64 | - `process` _Process_ - Process execution interface.
 65 |
 66 |
 67 | #### Workspace.\_\_init\_\_
 68 |
 69 | ```python
 70 | def __init__(id: str, instance: WorkspaceInstance, workspace_api: WorkspaceApi,
 71 |              toolbox_api: ToolboxApi, code_toolbox: WorkspaceCodeToolbox)
 72 | ```
 73 |
 74 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L197)
 75 |
 76 | Initialize a new Workspace instance.
 77 |
 78 | **Arguments**:
 79 |
 80 | - `id` _str_ - Unique identifier for the Sandbox.
 81 | - `instance` _WorkspaceInstance_ - The underlying Sandbox instance.
 82 | - `workspace_api` _WorkspaceApi_ - API client for Sandbox operations.
 83 | - `toolbox_api` _ToolboxApi_ - API client for toolbox operations.
 84 | - `code_toolbox` _WorkspaceCodeToolbox_ - Language-specific toolbox implementation.
 85 |
 86 |
 87 | #### Workspace.info
 88 |
 89 | ```python
 90 | def info() -> WorkspaceInfo
 91 | ```
 92 |
 93 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L227)
 94 |
 95 | Gets structured information about the Sandbox.
 96 |
 97 | **Returns**:
 98 |
 99 | - `WorkspaceInfo` - Detailed information about the Sandbox including its
100 |   configuration, resources, and current state.
101 |
102 |
103 | **Example**:
104 |
105 | ```python
106 | info = workspace.info()
107 | print(f"Workspace {info.name}:")
108 | print(f"State: {info.state}")
109 | print(f"Resources: {info.resources.cpu} CPU, {info.resources.memory} RAM")
110 | ```
111 |
112 |
113 | #### Workspace.get\_workspace\_root\_dir
114 |
115 | ```python
116 | @intercept_errors(message_prefix="Failed to get workspace root directory: ")
117 | def get_workspace_root_dir() -> str
118 | ```
119 |
120 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L246)
121 |
122 | Gets the root directory path of the Sandbox.
123 |
124 | **Returns**:
125 |
126 | - `str` - The absolute path to the Sandbox root directory.
127 |
128 |
129 | **Example**:
130 |
131 | ```python
132 | root_dir = workspace.get_workspace_root_dir()
133 | print(f"Workspace root: {root_dir}")
134 | ```
135 |
136 |
137 | #### Workspace.create\_lsp\_server
138 |
139 | ```python
140 | def create_lsp_server(language_id: LspLanguageId,
141 |                       path_to_project: str) -> LspServer
142 | ```
143 |
144 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L263)
145 |
146 | Creates a new Language Server Protocol (LSP) server instance.
147 |
148 | The LSP server provides language-specific features like code completion,
149 | diagnostics, and more.
150 |
151 | **Arguments**:
152 |
153 | - `language_id` _LspLanguageId_ - The language server type (e.g., LspLanguageId.PYTHON).
154 | - `path_to_project` _str_ - Absolute path to the project root directory.
155 |
156 |
157 | **Returns**:
158 |
159 | - `LspServer` - A new LSP server instance configured for the specified language.
160 |
161 |
162 | **Example**:
163 |
164 | ```python
165 | lsp = workspace.create_lsp_server("python", "/workspace/project")
166 | ```
167 |
168 |
169 | #### Workspace.set\_labels
170 |
171 | ```python
172 | @intercept_errors(message_prefix="Failed to set labels: ")
173 | def set_labels(labels: Dict[str, str]) -> Dict[str, str]
174 | ```
175 |
176 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L286)
177 |
178 | Sets labels for the Sandbox.
179 |
180 | Labels are key-value pairs that can be used to organize and identify Sandboxes.
181 |
182 | **Arguments**:
183 |
184 | - `labels` _Dict[str, str]_ - Dictionary of key-value pairs representing Sandbox labels.
185 |
186 |
187 | **Returns**:
188 |
189 |   Dict[str, str]: Dictionary containing the updated Sandbox labels.
190 |
191 |
192 | **Example**:
193 |
194 | ```python
195 | new_labels = workspace.set_labels({
196 |     "project": "my-project",
197 |     "environment": "development",
198 |     "team": "backend"
199 | })
200 | print(f"Updated labels: {new_labels}")
201 | ```
202 |
203 |
204 | #### Workspace.start
205 |
206 | ```python
207 | @intercept_errors(message_prefix="Failed to start workspace: ")
208 | @with_timeout(
209 |     error_message=lambda self, timeout:
210 |     f"Workspace {self.id} failed to start within the {timeout} seconds timeout period"
211 | )
212 | def start(timeout: Optional[float] = 60)
213 | ```
214 |
215 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L315)
216 |
217 | Starts the Sandbox.
218 |
219 | This method starts the Sandbox and waits for it to be ready.
220 |
221 | **Arguments**:
222 |
223 | - `timeout` _Optional[float]_ - Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
224 |
225 |
226 | **Raises**:
227 |
228 | - `DaytonaError` - If timeout is negative. If workspace fails to start or times out.
229 |
230 |
231 | **Example**:
232 |
233 | ```python
234 | workspace = daytona.get_current_workspace("my-workspace")
235 | workspace.start(timeout=40)  # Wait up to 40 seconds
236 | print("Workspace started successfully")
237 | ```
238 |
239 |
240 | #### Workspace.stop
241 |
242 | ```python
243 | @intercept_errors(message_prefix="Failed to stop workspace: ")
244 | @with_timeout(
245 |     error_message=lambda self, timeout:
246 |     f"Workspace {self.id} failed to stop within the {timeout} seconds timeout period"
247 | )
248 | def stop(timeout: Optional[float] = 60)
249 | ```
250 |
251 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L338)
252 |
253 | Stops the Sandbox.
254 |
255 | This method stops the Sandbox and waits for it to be fully stopped.
256 |
257 | **Arguments**:
258 |
259 | - `timeout` _Optional[float]_ - Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
260 |
261 |
262 | **Raises**:
263 |
264 | - `DaytonaError` - If timeout is negative; If workspace fails to stop or times out
265 |
266 |
267 | **Example**:
268 |
269 | ```python
270 | workspace = daytona.get_current_workspace("my-workspace")
271 | workspace.stop()
272 | print("Workspace stopped successfully")
273 | ```
274 |
275 |
276 | #### Workspace.wait\_for\_workspace\_start
277 |
278 | ```python
279 | @intercept_errors(
280 |     message_prefix="Failure during waiting for workspace to start: ")
281 | @with_timeout(
282 |     error_message=lambda self, timeout:
283 |     f"Workspace {self.id} failed to become ready within the {timeout} seconds timeout period"
284 | )
285 | def wait_for_workspace_start(timeout: Optional[float] = 60) -> None
286 | ```
287 |
288 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L361)
289 |
290 | Waits for the Sandbox to reach the 'started' state.
291 |
292 | This method polls the Sandbox status until it reaches the 'started' state
293 | or encounters an error.
294 |
295 | **Arguments**:
296 |
297 | - `timeout` _Optional[float]_ - Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
298 |
299 |
300 | **Raises**:
301 |
302 | - `DaytonaError` - If timeout is negative; If workspace fails to start or times out
303 |
304 |
305 | #### Workspace.wait\_for\_workspace\_stop
306 |
307 | ```python
308 | @intercept_errors(
309 |     message_prefix="Failure during waiting for workspace to stop: ")
310 | @with_timeout(
311 |     error_message=lambda self, timeout:
312 |     f"Workspace {self.id} failed to become stopped within the {timeout} seconds timeout period"
313 | )
314 | def wait_for_workspace_stop(timeout: Optional[float] = 60) -> None
315 | ```
316 |
317 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L387)
318 |
319 | Waits for the Sandbox to reach the 'stopped' state.
320 |
321 | This method polls the Sandbox status until it reaches the 'stopped' state
322 | or encounters an error. It will wait up to 60 seconds for the Sandbox to stop.
323 |
324 | **Arguments**:
325 |
326 | - `timeout` _Optional[float]_ - Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
327 |
328 |
329 | **Raises**:
330 |
331 | - `DaytonaError` - If timeout is negative. If Sandbox fails to stop or times out.
332 |
333 |
334 | #### Workspace.set\_autostop\_interval
335 |
336 | ```python
337 | @intercept_errors(message_prefix="Failed to set auto-stop interval: ")
338 | def set_autostop_interval(interval: int) -> None
339 | ```
340 |
341 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L418)
342 |
343 | Sets the auto-stop interval for the Sandbox.
344 |
345 | The Sandbox will automatically stop after being idle (no new events) for the specified interval.
346 | Events include any state changes or interactions with the Sandbox through the SDK.
347 | Interactions using Sandbox Previews are not included.
348 |
349 | **Arguments**:
350 |
351 | - `interval` _int_ - Number of minutes of inactivity before auto-stopping.
352 |   Set to 0 to disable auto-stop. Defaults to 15.
353 |
354 |
355 | **Raises**:
356 |
357 | - `DaytonaError` - If interval is negative
358 |
359 |
360 | **Example**:
361 |
362 | ```python
363 | # Auto-stop after 1 hour
364 | workspace.set_autostop_interval(60)
365 | # Or disable auto-stop
366 | workspace.set_autostop_interval(0)
367 | ```
368 |
369 |
370 | #### Workspace.get\_preview\_link
371 |
372 | ```python
373 | @intercept_errors(message_prefix="Failed to get preview link: ")
374 | def get_preview_link(port: int) -> str
375 | ```
376 |
377 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L448)
378 |
379 | Gets the preview link for the workspace at a specific port. If the port is not open, it will open it and return the link.
380 |
381 | **Arguments**:
382 |
383 | - `port` _int_ - The port to open the preview link on
384 |
385 |
386 | **Returns**:
387 |
388 |   The preview link for the workspace at the specified port
389 |
390 |
391 | #### Workspace.archive
392 |
393 | ```python
394 | @intercept_errors(message_prefix="Failed to archive workspace: ")
395 | def archive() -> None
396 | ```
397 |
398 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L466)
399 |
400 | Archives the workspace, making it inactive and preserving its state. When sandboxes are archived, the entire filesystem
401 | state is moved to cost-effective object storage, making it possible to keep sandboxes available for an extended period.
402 | The tradeoff between archived and stopped states is that starting an archived sandbox takes more time, depending on its size.
403 | Workspace must be stopped before archiving.
404 |
405 |
406 | The Daytona SDK core Sandbox functionality.
407 |
408 | Provides the main Workspace class representing a Daytona Sandbox that coordinates file system,
409 | Git, process execution, and LSP functionality. It serves as the central point
410 | for interacting with Daytona Sandboxes.
411 |
412 | **Example**:
413 |
414 |   Basic Sandbox operations:
415 | ```python
416 | from daytona_sdk import Daytona
417 | daytona = Daytona()
418 | workspace = daytona.create()
419 |
420 | # File operations
421 | workspace.fs.upload_file("/workspace/test.txt", b"Hello, World!")
422 | content = workspace.fs.download_file("/workspace/test.txt")
423 |
424 | # Git operations
425 | workspace.git.clone("https://github.com/user/repo.git")
426 |
427 | # Process execution
428 | response = workspace.process.exec("ls -la")
429 | print(response.result)
430 |
431 | # LSP functionality
432 | lsp = workspace.create_lsp_server("python", "/workspace/project")
433 | lsp.did_open("/workspace/project/src/index.ts")
434 | completions = lsp.completions("/workspace/project/src/index.ts", Position(line=10, character=15))
435 | print(completions)
436 | ```
437 |
438 |
439 | **Notes**:
440 |
441 |   The Sandbox must be in a 'started' state before performing operations.
442 |
443 |
444 | <a id="daytona_sdk.workspace.WorkspaceTargetRegion"></a>
445 | ## WorkspaceTargetRegion
446 |
447 | ```python
448 | @dataclass
449 | class WorkspaceTargetRegion(Enum)
450 | ```
451 |
452 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L58)
453 |
454 | Target regions for workspaces
455 |
456 |
457 | <a id="daytona_sdk.workspace.WorkspaceResources"></a>
458 | ## WorkspaceResources
459 |
460 | ```python
461 | @dataclass
462 | class WorkspaceResources()
463 | ```
464 |
465 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L74)
466 |
467 | Resources allocated to a Sandbox.
468 |
469 | **Attributes**:
470 |
471 | - `cpu` _str_ - Number of CPU cores allocated (e.g., "1", "2").
472 | - `gpu` _Optional[str]_ - Number of GPUs allocated (e.g., "1") or None if no GPU.
473 | - `memory` _str_ - Amount of memory allocated with unit (e.g., "2Gi", "4Gi").
474 | - `disk` _str_ - Amount of disk space allocated with unit (e.g., "10Gi", "20Gi").
475 |
476 |
477 | **Example**:
478 |
479 | ```python
480 | resources = WorkspaceResources(
481 |     cpu="2",
482 |     gpu="1",
483 |     memory="4Gi",
484 |     disk="20Gi"
485 | )
486 | ```
487 |
488 |
489 | <a id="daytona_sdk.workspace.WorkspaceState"></a>
490 | ## WorkspaceState
491 |
492 | ```python
493 | @dataclass
494 | class WorkspaceState(Enum)
495 | ```
496 |
497 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L100)
498 |
499 | States of a Sandbox.
500 |
501 |
502 | <a id="daytona_sdk.workspace.WorkspaceInfo"></a>
503 | ## WorkspaceInfo
504 |
505 | ```python
506 | class WorkspaceInfo(ApiWorkspaceInfo)
507 | ```
508 |
509 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L124)
510 |
511 | Structured information about a Sandbox.
512 |
513 | This class provides detailed information about a Sandbox's configuration,
514 | resources, and current state.
515 |
516 | **Attributes**:
517 |
518 | - `id` _str_ - Unique identifier for the Sandbox.
519 | - `name` _str_ - Display name of the Sandbox.
520 | - `image` _str_ - Docker image used for the Sandbox.
521 | - `user` _str_ - OS user running in the Sandbox.
522 | - `env` _Dict[str, str]_ - Environment variables set in the Sandbox.
523 | - `labels` _Dict[str, str]_ - Custom labels attached to the Sandbox.
524 | - `public` _bool_ - Whether the Sandbox is publicly accessible.
525 | - `target` _str_ - Target environment where the Sandbox runs.
526 | - `resources` _WorkspaceResources_ - Resource allocations for the Sandbox.
527 | - `state` _str_ - Current state of the Sandbox (e.g., "started", "stopped").
528 | - `error_reason` _Optional[str]_ - Error message if Sandbox is in error state.
529 | - `snapshot_state` _Optional[str]_ - Current state of Sandbox snapshot.
530 | - `snapshot_state_created_at` _Optional[datetime]_ - When the snapshot state was created.
531 |
532 |
533 | **Example**:
534 |
535 | ```python
536 | workspace = daytona.create()
537 | info = workspace.info()
538 | print(f"Workspace {info.name} is {info.state}")
539 | print(f"Resources: {info.resources.cpu} CPU, {info.resources.memory} RAM")
540 | ```
541 |
542 |
543 | <a id="daytona_sdk.workspace.WorkspaceInstance"></a>
544 | ## WorkspaceInstance
545 |
546 | ```python
547 | class WorkspaceInstance(ApiWorkspace)
548 | ```
549 |
550 | [[view_source]](https://github.com/daytonaio/sdk/blob/e2c391f367e740a14945617b9e5c7b965ba4d7d9/packages/python/src/daytona_sdk/workspace.py#L176)
551 |
552 | Represents a Daytona workspace instance.
553 |
554 |
555 |


--------------------------------------------------------------------------------

├── examples
    └── python
    │   ├── exec-command
    │       ├── exec-session.py
    │       └── exec.py
    │   ├── file-operations
    │       └── main.py
    │   ├── git-lsp
    │       └── main.py
    │   └── lifecycle
    │       └── lifecycle.py
└── packages
    └── python
        ├── setup.py
        └── src
            └── daytona_sdk
                ├── __init__.py
                ├── _utils
                    ├── __init__.py
                    ├── enum.py
                    ├── errors.py
                    └── timeout.py
                ├── code_toolbox
                    ├── __init__.py
                    ├── workspace_python_code_toolbox.py
                    └── workspace_ts_code_toolbox.py
                ├── common
                    ├── __init__.py
                    ├── code_run_params.py
                    └── errors.py
                ├── daytona.py
                ├── filesystem.py
                ├── git.py
                ├── lsp_server.py
                ├── process.py
                ├── protocols.py
                └── workspace.py


/examples/python/exec-command/exec-session.py:
--------------------------------------------------------------------------------
 1 | from daytona_sdk import Daytona, CreateWorkspaceParams, SessionExecuteRequest
 2 |
 3 | daytona = Daytona()
 4 | workspace = daytona.create()
 5 |
 6 | exec_session_id = "exec-session-1"
 7 | workspace.process.create_session(exec_session_id)
 8 |
 9 | # Get the session details any time
10 | session = workspace.process.get_session(exec_session_id)
11 | print(session)
12 |
13 | # Execute a first command in the session
14 | execCommand1 = workspace.process.execute_session_command(exec_session_id, SessionExecuteRequest(
15 |     command="export FOO=BAR"
16 | ))
17 | if execCommand1.exit_code != 0:
18 |     print(f"Error: {execCommand1.exit_code} {execCommand1.output}")
19 |
20 | # Get the session details again to see the command has been executed
21 | session = workspace.process.get_session(exec_session_id)
22 | print(session)
23 |
24 | # Get the command details
25 | session_command = workspace.process.get_session_command(exec_session_id, execCommand1.cmd_id)
26 | print(session_command)
27 |
28 | # Execute a second command in the session and see that the environment variable is set
29 | execCommand2 = workspace.process.execute_session_command(exec_session_id, SessionExecuteRequest(
30 |     command="echo $FOO"
31 | ))
32 | if execCommand2.exit_code != 0:
33 |     print(f"Error: {execCommand2.exit_code} {execCommand2.output}")
34 | else:
35 |     print(execCommand2.output)
36 |
37 | print("Now getting logs for the second command")
38 | logs = workspace.process.get_session_command_logs(exec_session_id, execCommand2.cmd_id)
39 | print(logs)
40 |
41 | # You can also list all active sessions
42 | sessions = workspace.process.list_sessions()
43 | print(sessions)
44 |
45 | # And of course you can delete the session at any time
46 | workspace.process.delete_session(exec_session_id)
47 |
48 | daytona.remove(workspace)
49 |


--------------------------------------------------------------------------------
/examples/python/exec-command/exec.py:
--------------------------------------------------------------------------------
 1 | from daytona_sdk import Daytona, CreateWorkspaceParams
 2 |
 3 | daytona = Daytona()
 4 |
 5 | params = CreateWorkspaceParams(
 6 |     language="python",
 7 | )
 8 | workspace = daytona.create(params)
 9 |
10 | # Run the code securely inside the workspace
11 | response = workspace.process.code_run('print("Hello World!")')
12 | if response.exit_code != 0:
13 |     print(f"Error: {response.exit_code} {response.result}")
14 | else:
15 |     print(response.result)
16 |
17 | # Execute an os command in the workspace
18 | response = workspace.process.exec('echo "Hello World from exec!"', cwd="/home/daytona", timeout=10)
19 | if response.exit_code != 0:
20 |     print(f"Error: {response.exit_code} {response.result}")
21 | else:
22 |     print(response.result)
23 |
24 | daytona.remove(workspace)
25 |


--------------------------------------------------------------------------------
/examples/python/file-operations/main.py:
--------------------------------------------------------------------------------
 1 | import os
 2 | from daytona_sdk import Daytona, CreateWorkspaceParams
 3 |
 4 | daytona = Daytona()
 5 | params = CreateWorkspaceParams(
 6 |   language="python",
 7 | )
 8 |
 9 | # First, create a workspace
10 | workspace = daytona.create(params)
11 |
12 | # Get workspace root directory
13 | root_dir = workspace.get_workspace_root_dir()
14 |
15 | # List files in the workspace
16 | files = workspace.fs.list_files(root_dir)
17 | print("Files:", files)
18 |
19 | # Create a new directory in the workspace
20 | new_dir = os.path.join(root_dir, "new-dir")
21 | workspace.fs.create_folder(new_dir, "755")
22 |
23 | file_path = os.path.join(new_dir, "data.txt")
24 |
25 | # Add a new file to the workspace
26 | file_content = b"Hello, World!"
27 | workspace.fs.upload_file(file_path, file_content)
28 |
29 | # Search for the file we just added
30 | matches = workspace.fs.find_files(root_dir, "World!")
31 | print("Matches:", matches)
32 |
33 | # Replace the contents of the file
34 | workspace.fs.replace_in_files([file_path], "Hello, World!", "Goodbye, World!")
35 |
36 | # Read the file
37 | downloaded_file = workspace.fs.download_file(file_path)
38 | print("File content:", downloaded_file.decode("utf-8"))
39 |
40 | # Change the file permissions
41 | workspace.fs.set_file_permissions(file_path, mode="777")
42 |
43 | # Get file info
44 | file_info = workspace.fs.get_file_info(file_path)
45 | print("File info:", file_info)  # Should show the new permissions
46 |
47 | # Move the file to the new location
48 | new_file_path = os.path.join(root_dir, "moved-data.txt")
49 | workspace.fs.move_files(file_path, new_file_path)
50 |
51 | # Find the file in the new location
52 | search_results = workspace.fs.search_files(root_dir, "moved-data.txt")
53 | print("Search results:", search_results)
54 |
55 | # Delete the file
56 | workspace.fs.delete_file(new_file_path)
57 |
58 | # daytona.remove(workspace)
59 |


--------------------------------------------------------------------------------
/examples/python/git-lsp/main.py:
--------------------------------------------------------------------------------
 1 | from daytona_sdk import Daytona
 2 | import os
 3 |
 4 |
 5 | def main():
 6 |     daytona = Daytona()
 7 |
 8 |     workspace = daytona.create()
 9 |
10 |     try:
11 |         root_dir = workspace.get_workspace_root_dir()
12 |         project_dir = os.path.join(root_dir, "learn-typescript")
13 |
14 |         # Clone the repository
15 |         workspace.git.clone(
16 |             "https://github.com/panaverse/learn-typescript", project_dir, "master"
17 |         )
18 |
19 |         workspace.git.pull(project_dir)
20 |
21 |         # Search for the file we want to work on
22 |         matches = workspace.fs.find_files(project_dir, "var obj1 = new Base();")
23 |         print("Matches:", matches)
24 |
25 |         # Start the language server
26 |         lsp = workspace.create_lsp_server("typescript", project_dir)
27 |         lsp.start()
28 |
29 |         # Notify the language server of the document we want to work on
30 |         lsp.did_open(matches[0].file)
31 |
32 |         # Get symbols in the document
33 |         symbols = lsp.document_symbols(matches[0].file)
34 |         print("Symbols:", symbols)
35 |
36 |         # Fix the error in the document
37 |         workspace.fs.replace_in_files(
38 |             [matches[0].file], "var obj1 = new Base();", "var obj1 = new E();"
39 |         )
40 |
41 |         # Notify the language server of the document change
42 |         lsp.did_close(matches[0].file)
43 |         lsp.did_open(matches[0].file)
44 |
45 |         # Get completions at a specific position
46 |         completions = lsp.completions(matches[0].file, {"line": 12, "character": 18})
47 |         print("Completions:", completions)
48 |
49 |     except Exception as error:
50 |         print("Error creating workspace:", error)
51 |     finally:
52 |         # Cleanup
53 |         daytona.remove(workspace)
54 |
55 |
56 | if __name__ == "__main__":
57 |     main()
58 |


--------------------------------------------------------------------------------
/examples/python/lifecycle/lifecycle.py:
--------------------------------------------------------------------------------
 1 | from daytona_sdk import Daytona
 2 | from pprint import pprint
 3 |
 4 | daytona = Daytona()
 5 |
 6 | print("Creating workspace")
 7 | workspace = daytona.create()
 8 | print("Workspace created")
 9 |
10 | workspace.set_labels({
11 |     "public": True,
12 | })
13 |
14 | print("Stopping workspace")
15 | daytona.stop(workspace)
16 | print("Workspace stopped")
17 |
18 | print("Starting workspace")
19 | daytona.start(workspace)
20 | print("Workspace started")
21 |
22 | print("Getting existing workspace")
23 | existing_workspace = daytona.get_current_workspace(workspace.id)
24 | print("Get existing workspace")
25 |
26 | response = existing_workspace.process.exec('echo "Hello World from exec!"', cwd="/home/daytona", timeout=10)
27 | if response.exit_code != 0:
28 |     print(f"Error: {response.exit_code} {response.result}")
29 | else:
30 |     print(response.result)
31 |
32 | workspaces = daytona.list()
33 | print("Total workspaces count:" , len(workspaces))
34 | pprint(vars(workspaces[0].info()))  # This will show all attributes of the first workspace
35 |
36 | print("Removing workspace")
37 | daytona.remove(workspace)
38 | print("Workspace removed")
39 |


--------------------------------------------------------------------------------
/packages/python/setup.py:
--------------------------------------------------------------------------------
 1 | from setuptools import setup, find_packages
 2 |
 3 | setup(
 4 |     name="daytona_sdk",
 5 |     version="0.1.4",
 6 |     packages=find_packages(where="src"),
 7 |     package_dir={"": "src"},
 8 |     install_requires=[
 9 |         # Add dependencies here
10 |     ],
11 |     # Include both packages
12 |     package_data={
13 |         "daytona_sdk": ["*"]
14 |     },
15 | )
16 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/__init__.py:
--------------------------------------------------------------------------------
 1 | from .daytona import (
 2 |     Daytona,
 3 |     DaytonaConfig,
 4 |     CreateWorkspaceParams,
 5 |     CodeLanguage,
 6 |     Workspace,
 7 |     SessionExecuteRequest,
 8 |     SessionExecuteResponse,
 9 |     DaytonaError,
10 |     WorkspaceTargetRegion,
11 | )
12 | from .lsp_server import LspLanguageId
13 | from .workspace import WorkspaceState
14 | from .common.code_run_params import CodeRunParams
15 |
16 | __all__ = [
17 |     "Daytona",
18 |     "DaytonaConfig",
19 |     "CreateWorkspaceParams",
20 |     "CodeLanguage",
21 |     "Workspace",
22 |     "SessionExecuteRequest",
23 |     "SessionExecuteResponse",
24 |     "DaytonaError",
25 |     "LspLanguageId",
26 |     "WorkspaceTargetRegion",
27 |     "WorkspaceState",
28 |     "CodeRunParams"
29 | ]
30 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/_utils/__init__.py:
--------------------------------------------------------------------------------
https://raw.githubusercontent.com/daytonaio/sdk/dcf0ddc88a191f3b23a037f3539d78a53a2652b7/packages/python/src/daytona_sdk/_utils/__init__.py


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/_utils/enum.py:
--------------------------------------------------------------------------------
 1 | from enum import Enum
 2 | from typing import Optional
 3 |
 4 |
 5 | def to_enum(enum_class: type, value: str) -> Optional[Enum]:
 6 |     """Convert a string to an enum.
 7 |
 8 |     Args:
 9 |         enum_class (type): The enum class to convert to.
10 |         value (str): The value to convert to an enum.
11 |
12 |     Returns:
13 |         The enum value, or None if the value is not a valid enum.
14 |     """
15 |     if isinstance(value, enum_class):
16 |         return value
17 |     str_value = str(value)
18 |     if str_value in enum_class._value2member_map_:
19 |         return enum_class(str_value)
20 |     return None
21 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/_utils/errors.py:
--------------------------------------------------------------------------------
 1 | import json
 2 | import functools
 3 | from typing import Callable, Optional, TypeVar, Any, ParamSpec
 4 | from daytona_api_client.exceptions import OpenApiException
 5 | from daytona_sdk.common.errors import DaytonaError
 6 |
 7 |
 8 | P = ParamSpec('P')
 9 | T = TypeVar('T')
10 |
11 |
12 | def intercept_errors(message_prefix: str = "") -> Callable[[Callable[P, T]], Callable[P, T]]:
13 |     """Decorator to intercept errors, process them, and optionally add a message prefix.
14 |     If the error is an OpenApiException, it will be processed to extract the most meaningful error message.
15 |
16 |     Args:
17 |         message_prefix (str): Custom message prefix for the error.
18 |     """
19 |     def decorator(func: Callable[P, T]) -> Callable[P, T]:
20 |         @functools.wraps(func)
21 |         def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
22 |             try:
23 |                 return func(*args, **kwargs)
24 |             except OpenApiException as e:
25 |                 message = _get_open_api_exception_message(e)
26 |
27 |                 raise DaytonaError(f"{message_prefix}{message}") from None
28 |             except Exception as e:
29 |                 if message_prefix:
30 |                     message = f"{message_prefix}{str(e)}"
31 |                     raise DaytonaError(message)
32 |                 raise DaytonaError(str(e))
33 |
34 |         return wrapper
35 |     return decorator
36 |
37 |
38 | def _get_open_api_exception_message(exception: OpenApiException) -> str:
39 |     """Process API exceptions to extract the most meaningful error message.
40 |
41 |     This method examines the exception's body attribute and attempts to extract
42 |     the most informative error message using the following logic:
43 |     1. If the body is missing or empty, returns the original exception
44 |     2. If the body contains valid JSON with a 'message' field, uses that message
45 |     3. If the body is not valid JSON or does not contain a 'message' field, uses the raw body string
46 |
47 |     Args:
48 |         exception (OpenApiException): The OpenApiException to process
49 |
50 |     Returns:
51 |         Processed message
52 |     """
53 |     if not hasattr(exception, 'body') or not exception.body:
54 |         return str(exception)
55 |
56 |     body_str = str(exception.body)
57 |     try:
58 |         data = json.loads(body_str)
59 |         message = data.get('message', body_str) if isinstance(
60 |             data, dict) else body_str
61 |     except json.JSONDecodeError:
62 |         message = body_str
63 |
64 |     return message
65 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/_utils/timeout.py:
--------------------------------------------------------------------------------
 1 | import functools
 2 | import concurrent.futures
 3 | from typing import Callable, Optional, Any, TypeVar, ParamSpec
 4 | from daytona_sdk._utils.errors import DaytonaError
 5 |
 6 |
 7 | P = ParamSpec('P')
 8 | T = TypeVar('T')
 9 |
10 |
11 | def with_timeout(error_message: Optional[Callable[[Any, float], str]] = None) -> Callable[[Callable[P, T]], Callable[P, T]]:
12 |     """Decorator to add a timeout mechanism with an optional custom error message.
13 |
14 |     Args:
15 |         error_message (Optional[Callable[[Any, float], str]]): A callable that accepts `self` and `timeout`,
16 |                                                                and returns a string error message.
17 |     """
18 |     def decorator(func: Callable[P, T]) -> Callable[P, T]:
19 |         @functools.wraps(func)
20 |         def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
21 |             # Get function argument names
22 |             arg_names = func.__code__.co_varnames[:func.__code__.co_argcount]
23 |             arg_dict = dict(zip(arg_names, args))
24 |
25 |             # Extract self if method is bound
26 |             self_instance = args[0] if args else None
27 |
28 |             # Check for 'timeout' in kwargs first, then in positional arguments
29 |             timeout = kwargs.get('timeout', arg_dict.get('timeout', None))
30 |
31 |             if timeout is None or timeout == 0:
32 |                 # If timeout is None or 0, run the function normally
33 |                 return func(*args, **kwargs)
34 |
35 |             if timeout < 0:
36 |                 raise DaytonaError(
37 |                     "Timeout must be a non-negative number or None.")
38 |
39 |             with concurrent.futures.ThreadPoolExecutor() as executor:
40 |                 future = executor.submit(func, *args, **kwargs)
41 |                 try:
42 |                     return future.result(timeout=timeout)
43 |                 except concurrent.futures.TimeoutError:
44 |                     # Use custom error message if provided, otherwise default
45 |                     msg = error_message(
46 |                         self_instance, timeout) if error_message else f"Function '{func.__name__}' exceeded timeout of {timeout} seconds."
47 |                     raise TimeoutError(msg)
48 |         return wrapper
49 |     return decorator
50 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/code_toolbox/__init__.py:
--------------------------------------------------------------------------------
https://raw.githubusercontent.com/daytonaio/sdk/dcf0ddc88a191f3b23a037f3539d78a53a2652b7/packages/python/src/daytona_sdk/code_toolbox/__init__.py


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/code_toolbox/workspace_python_code_toolbox.py:
--------------------------------------------------------------------------------
 1 | import base64
 2 | from typing import Optional
 3 | from ..common.code_run_params import CodeRunParams
 4 |
 5 |
 6 | class WorkspacePythonCodeToolbox:
 7 |     def get_run_command(self, code: str, params: Optional[CodeRunParams] = None) -> str:
 8 |         # Encode the provided code in base64
 9 |         base64_code = base64.b64encode(code.encode()).decode()
10 |
11 |         # Build environment variables string
12 |         env_vars = ""
13 |         if params and params.env:
14 |             env_vars = ' '.join(f"{key}='{value}'" for key, value in params.env.items())
15 |
16 |         # Build command-line arguments string
17 |         argv = ""
18 |         if params and params.argv:
19 |             argv = ' '.join(params.argv)
20 |
21 |         # Combine everything into the final command
22 |         return f""" sh -c '{env_vars} python3 -c "exec(__import__(\\\"base64\\\").b64decode(\\\"{base64_code}\\\").decode())" {argv}' """
23 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/code_toolbox/workspace_ts_code_toolbox.py:
--------------------------------------------------------------------------------
 1 | import base64
 2 | from typing import Optional
 3 | from ..common.code_run_params import CodeRunParams
 4 |
 5 |
 6 | class WorkspaceTsCodeToolbox:
 7 |     def get_run_command(self, code: str, params: Optional[CodeRunParams] = None) -> str:
 8 |         # Encode the provided code in base64
 9 |         base64_code = base64.b64encode(code.encode()).decode()
10 |
11 |         # Build environment variables string
12 |         env_vars = ""
13 |         if params and params.env:
14 |             env_vars = ' '.join(f"{key}='{value}'" for key, value in params.env.items())
15 |
16 |         # Build command-line arguments string
17 |         argv = ""
18 |         if params and params.argv:
19 |             argv = ' '.join(params.argv)
20 |
21 |         # Combine everything into the final command for TypeScript
22 |         return f""" sh -c 'echo {base64_code} | base64 --decode | {env_vars} npx ts-node -O "{{\\\"module\\\":\\\"CommonJS\\\"}}" -e "$(cat)" x {argv} 2>&1 | grep -vE "npm notice|npm warn exec"' """
23 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/common/__init__.py:
--------------------------------------------------------------------------------
https://raw.githubusercontent.com/daytonaio/sdk/dcf0ddc88a191f3b23a037f3539d78a53a2652b7/packages/python/src/daytona_sdk/common/__init__.py


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/common/code_run_params.py:
--------------------------------------------------------------------------------
1 | from dataclasses import dataclass
2 | from typing import Optional, List, Dict
3 |
4 | @dataclass
5 | class CodeRunParams:
6 |     """Parameters for code execution."""
7 |     argv: Optional[List[str]] = None
8 |     env: Optional[Dict[str, str]] = None


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/common/errors.py:
--------------------------------------------------------------------------------
1 | class DaytonaError(Exception):
2 |     """Base error for Daytona SDK."""
3 |     pass
4 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/daytona.py:
--------------------------------------------------------------------------------
  1 | """
  2 | Sandboxes are isolated development environments managed by Daytona.
  3 | This guide covers how to create, manage, and remove Sandboxes using the SDK.
  4 |
  5 | Examples:
  6 |     Basic usage with environment variables:
  7 |     ```python
  8 |     from daytona_sdk import Daytona
  9 |     # Initialize using environment variables
 10 |     daytona = Daytona()  # Uses env vars DAYTONA_API_KEY, DAYTONA_SERVER_URL, DAYTONA_TARGET
 11 |
 12 |     # Create a default Python workspace with custom environment variables
 13 |     workspace = daytona.create(CreateWorkspaceParams(
 14 |         language="python",
 15 |         env_vars={"PYTHON_ENV": "development"}
 16 |     ))
 17 |
 18 |     # Execute commands in the workspace
 19 |     response = workspace.process.execute_command('echo "Hello, World!"')
 20 |     print(response.result)
 21 |
 22 |     # Run Python code securely inside the workspace
 23 |     response = workspace.process.code_run('print("Hello from Python!")')
 24 |     print(response.result)
 25 |
 26 |     # Remove the workspace after use
 27 |     daytona.remove(workspace)
 28 |     ```
 29 |
 30 |     Usage with explicit configuration:
 31 |     ```python
 32 |     from daytona_sdk import Daytona, DaytonaConfig, CreateWorkspaceParams, WorkspaceResources
 33 |
 34 |     # Initialize with explicit configuration
 35 |     config = DaytonaConfig(
 36 |         api_key="your-api-key",
 37 |         server_url="https://your-server.com",
 38 |         target="us"
 39 |     )
 40 |     daytona = Daytona(config)
 41 |
 42 |     # Create a custom workspace with specific resources and settings
 43 |     workspace = daytona.create(CreateWorkspaceParams(
 44 |         language="python",
 45 |         image="python:3.11",
 46 |         resources=WorkspaceResources(
 47 |             cpu=2,
 48 |             memory=4,  # 4GB RAM
 49 |             disk=20    # 20GB disk
 50 |         ),
 51 |         env_vars={"PYTHON_ENV": "development"},
 52 |         auto_stop_interval=60  # Auto-stop after 1 hour of inactivity
 53 |     ))
 54 |
 55 |     # Use workspace features
 56 |     workspace.git.clone("https://github.com/user/repo.git")
 57 |     workspace.process.execute_command("python -m pytest")
 58 |     ```
 59 | """
 60 |
 61 | from enum import Enum
 62 | import uuid
 63 | from typing import Optional, Dict, List, Annotated
 64 | from pydantic import BaseModel, Field
 65 | from dataclasses import dataclass
 66 | from environs import Env
 67 | from daytona_api_client import (
 68 |     Configuration,
 69 |     WorkspaceApi,
 70 |     ToolboxApi,
 71 |     ApiClient,
 72 |     CreateWorkspace,
 73 |     SessionExecuteRequest,
 74 |     SessionExecuteResponse
 75 | )
 76 | from daytona_sdk._utils.errors import intercept_errors, DaytonaError
 77 | from .code_toolbox.workspace_python_code_toolbox import WorkspacePythonCodeToolbox
 78 | from .code_toolbox.workspace_ts_code_toolbox import WorkspaceTsCodeToolbox
 79 | from ._utils.enum import to_enum
 80 | from .workspace import Workspace, WorkspaceTargetRegion
 81 | from ._utils.timeout import with_timeout
 82 |
 83 |
 84 | @dataclass
 85 | class CodeLanguage(Enum):
 86 |     """Programming languages supported by Daytona"""
 87 |     PYTHON = "python"
 88 |     TYPESCRIPT = "typescript"
 89 |     JAVASCRIPT = "javascript"
 90 |
 91 |     def __str__(self):
 92 |         return self.value
 93 |
 94 |     def __eq__(self, other):
 95 |         if isinstance(other, str):
 96 |             return self.value == other
 97 |         return super().__eq__(other)
 98 |
 99 |
100 | @dataclass
101 | class DaytonaConfig:
102 |     """Configuration options for initializing the Daytona client.
103 |
104 |     Attributes:
105 |         api_key (str): API key for authentication with Daytona server.
106 |         server_url (str): URL of the Daytona server.
107 |         target (str): Target environment for Sandbox.
108 |
109 |     Example:
110 |         ```python
111 |         config = DaytonaConfig(
112 |             api_key="your-api-key",
113 |             server_url="https://your-server.com",
114 |             target="us"
115 |         )
116 |         daytona = Daytona(config)
117 |         ```
118 |     """
119 |     api_key: str
120 |     server_url: str
121 |     target: WorkspaceTargetRegion
122 |
123 |
124 | @dataclass
125 | class WorkspaceResources:
126 |     """Resources configuration for Sandbox.
127 |
128 |     Attributes:
129 |         cpu (Optional[int]): Number of CPU cores to allocate.
130 |         memory (Optional[int]): Amount of memory in GB to allocate.
131 |         disk (Optional[int]): Amount of disk space in GB to allocate.
132 |         gpu (Optional[int]): Number of GPUs to allocate.
133 |
134 |     Example:
135 |         ```python
136 |         resources = WorkspaceResources(
137 |             cpu=2,
138 |             memory=4,  # 4GB RAM
139 |             disk=20,   # 20GB disk
140 |             gpu=1
141 |         )
142 |         params = CreateWorkspaceParams(
143 |             language="python",
144 |             resources=resources
145 |         )
146 |         ```
147 |     """
148 |     cpu: Optional[int] = None
149 |     memory: Optional[int] = None
150 |     disk: Optional[int] = None
151 |     gpu: Optional[int] = None
152 |
153 |
154 | class CreateWorkspaceParams(BaseModel):
155 |     """Parameters for creating a new Sandbox.
156 |
157 |     Attributes:
158 |         language (CodeLanguage): Programming language for the Sandbox ("python", "javascript", "typescript").
159 |         id (Optional[str]): Custom identifier for the Sandbox. If not provided, a random ID will be generated.
160 |         name (Optional[str]): Display name for the Sandbox. Defaults to Sandbox ID if not provided.
161 |         image (Optional[str]): Custom Docker image to use for the Sandbox.
162 |         os_user (Optional[str]): OS user for the Sandbox.
163 |         env_vars (Optional[Dict[str, str]]): Environment variables to set in the Sandbox.
164 |         labels (Optional[Dict[str, str]]): Custom labels for the Sandbox.
165 |         public (Optional[bool]): Whether the Sandbox should be public.
166 |         target (Optional[str]): Target location for the Sandbox. Can be "us", "eu", or "asia".
167 |         resources (Optional[WorkspaceResources]): Resource configuration for the Sandbox.
168 |         timeout (Optional[float]): Timeout in seconds for Sandbox to be created and started.
169 |         auto_stop_interval (Optional[int]): Interval in minutes after which Sandbox will automatically stop if no Sandbox event occurs during that time. Default is 15 minutes. 0 means no auto-stop.
170 |
171 |     Example:
172 |         ```python
173 |         params = CreateWorkspaceParams(
174 |             language="python",
175 |             name="my-workspace",
176 |             env_vars={"DEBUG": "true"},
177 |             resources=WorkspaceResources(cpu=2, memory=4),
178 |             auto_stop_interval=20
179 |         )
180 |         workspace = daytona.create(params, 50)
181 |         ```
182 |     """
183 |     language: CodeLanguage
184 |     id: Optional[str] = None
185 |     name: Optional[str] = None
186 |     image: Optional[str] = None
187 |     os_user: Optional[str] = None
188 |     env_vars: Optional[Dict[str, str]] = None
189 |     labels: Optional[Dict[str, str]] = None
190 |     public: Optional[bool] = None
191 |     target: Optional[WorkspaceTargetRegion] = None
192 |     resources: Optional[WorkspaceResources] = None
193 |     timeout: Annotated[Optional[float], Field(
194 |         default=None, deprecated='The `timeout` field is deprecated and will be removed in future versions. Use `timeout` argument in method calls instead.')]
195 |     auto_stop_interval: Optional[int] = None
196 |
197 |
198 | class Daytona:
199 |     """Main class for interacting with Daytona Server API.
200 |
201 |     This class provides methods to create, manage, and interact with Daytona Sandboxes.
202 |     It can be initialized either with explicit configuration or using environment variables.
203 |
204 |     Attributes:
205 |         api_key (str): API key for authentication.
206 |         server_url (str): URL of the Daytona server.
207 |         target (str): Default target location for Sandboxes.
208 |
209 |     Example:
210 |         Using environment variables:
211 |         ```python
212 |         daytona = Daytona()  # Uses DAYTONA_API_KEY, DAYTONA_SERVER_URL
213 |         ```
214 |
215 |         Using explicit configuration:
216 |         ```python
217 |         config = DaytonaConfig(
218 |             api_key="your-api-key",
219 |             server_url="https://your-server.com",
220 |             target="us"
221 |         )
222 |         daytona = Daytona(config)
223 |         ```
224 |     """
225 |
226 |     def __init__(self, config: Optional[DaytonaConfig] = None):
227 |         """Initializes Daytona instance with optional configuration.
228 |
229 |         If no config is provided, reads from environment variables:
230 |         - `DAYTONA_API_KEY`: Required API key for authentication
231 |         - `DAYTONA_SERVER_URL`: Required server URL
232 |         - `DAYTONA_TARGET`: Optional target environment (defaults to WorkspaceTargetRegion.US)
233 |
234 |         Args:
235 |             config (Optional[DaytonaConfig]): Object containing api_key, server_url, and target.
236 |
237 |         Raises:
238 |             DaytonaError: If API key or Server URL is not provided either through config or environment variables
239 |
240 |         Example:
241 |             ```python
242 |             from daytona_sdk import Daytona, DaytonaConfig
243 |             # Using environment variables
244 |             daytona1 = Daytona()
245 |             # Using explicit configuration
246 |             config = DaytonaConfig(
247 |                 api_key="your-api-key",
248 |                 server_url="https://your-server.com",
249 |                 target="us"
250 |             )
251 |             daytona2 = Daytona(config)
252 |             ```
253 |         """
254 |         if config is None:
255 |             # Initialize env - it automatically reads from .env and .env.local
256 |             env = Env()
257 |             env.read_env()  # reads .env
258 |             # reads .env.local and overrides values
259 |             env.read_env(".env.local", override=True)
260 |
261 |             self.api_key = env.str("DAYTONA_API_KEY")
262 |             self.server_url = env.str("DAYTONA_SERVER_URL")
263 |             self.target = env.str("DAYTONA_TARGET", WorkspaceTargetRegion.US)
264 |         else:
265 |             self.api_key = config.api_key
266 |             self.server_url = config.server_url
267 |             self.target = config.target
268 |
269 |         if not self.api_key:
270 |             raise DaytonaError("API key is required")
271 |
272 |         if not self.server_url:
273 |             raise DaytonaError("Server URL is required")
274 |
275 |         if not self.target:
276 |             self.target = WorkspaceTargetRegion.US
277 |
278 |         # Create API configuration without api_key
279 |         configuration = Configuration(host=self.server_url)
280 |         api_client = ApiClient(configuration)
281 |         api_client.default_headers["Authorization"] = f"Bearer {self.api_key}"
282 |
283 |         # Initialize API clients with the api_client instance
284 |         self.workspace_api = WorkspaceApi(api_client)
285 |         self.toolbox_api = ToolboxApi(api_client)
286 |
287 |     @intercept_errors(message_prefix="Failed to create workspace: ")
288 |     def create(self, params: Optional[CreateWorkspaceParams] = None, timeout: Optional[float] = 60) -> Workspace:
289 |         """Creates Sandboxes with default or custom configurations. You can specify various parameters,
290 |         including language, image, resources, environment variables, and volumes for the Sandbox.
291 |
292 |         Args:
293 |             params (Optional[CreateWorkspaceParams]): Parameters for Sandbox creation. If not provided,
294 |                    defaults to Python language.
295 |             timeout (Optional[float]): Timeout (in seconds) for workspace creation. 0 means no timeout. Default is 60 seconds.
296 |
297 |         Returns:
298 |             Workspace: The created Sandbox instance.
299 |
300 |         Raises:
301 |             DaytonaError: If timeout or auto_stop_interval is negative; If workspace fails to start or times out
302 |
303 |         Example:
304 |             Create a default Python Sandbox:
305 |             ```python
306 |             workspace = daytona.create()
307 |             ```
308 |
309 |             Create a custom Sandbox:
310 |             ```python
311 |             params = CreateWorkspaceParams(
312 |                 language="python",
313 |                 name="my-workspace",
314 |                 image="debian:12.9",
315 |                 env_vars={"DEBUG": "true"},
316 |                 resources=WorkspaceResources(cpu=2, memory=4096),
317 |                 auto_stop_interval=0
318 |             )
319 |             workspace = daytona.create(params, 40)
320 |             ```
321 |         """
322 |         # If no params provided, create default params for Python
323 |         if params is None:
324 |             params = CreateWorkspaceParams(language="python")
325 |
326 |         params.id = params.id if params.id else f"sandbox-{str(uuid.uuid4())[:8]}"
327 |
328 |         effective_timeout = params.timeout if params.timeout else timeout
329 |
330 |         try:
331 |             return self._create(params, effective_timeout)
332 |         except Exception as e:
333 |             try:
334 |                 self.workspace_api.delete_workspace(
335 |                     workspace_id=params.id, force=True)
336 |             except Exception:
337 |                 pass
338 |             raise e
339 |
340 |     @with_timeout(error_message=lambda self, timeout: f"Failed to create and start workspace within {timeout} seconds timeout period.")
341 |     def _create(self, params: Optional[CreateWorkspaceParams] = None, timeout: Optional[float] = 60) -> Workspace:
342 |         """Creates a new Sandbox and waits for it to start.
343 |
344 |         Args:
345 |             params (Optional[CreateWorkspaceParams]): Parameters for Sandbox creation. If not provided,
346 |                    defaults to Python language.
347 |             timeout (Optional[float]): Timeout (in seconds) for workspace creation. 0 means no timeout. Default is 60 seconds.
348 |
349 |         Returns:
350 |             Workspace: The created Sandbox instance.
351 |
352 |         Raises:
353 |             DaytonaError: If timeout or auto_stop_interval is negative; If workspace fails to start or times out
354 |         """
355 |         code_toolbox = self._get_code_toolbox(params)
356 |
357 |         if timeout < 0:
358 |             raise DaytonaError("Timeout must be a non-negative number")
359 |
360 |         if params.auto_stop_interval is not None and params.auto_stop_interval < 0:
361 |             raise DaytonaError(
362 |                 "auto_stop_interval must be a non-negative integer")
363 |
364 |         target = params.target if params.target else self.target
365 |
366 |         # Create workspace using dictionary
367 |         workspace_data = CreateWorkspace(
368 |             id=params.id,
369 |             name=params.name if params.name else params.id,
370 |             image=params.image,
371 |             user=params.os_user,
372 |             env=params.env_vars if params.env_vars else {},
373 |             labels=params.labels,
374 |             public=params.public,
375 |             target=str(target) if target else None,
376 |             auto_stop_interval=params.auto_stop_interval
377 |         )
378 |
379 |         if params.resources:
380 |             workspace_data.cpu = params.resources.cpu
381 |             workspace_data.memory = params.resources.memory
382 |             workspace_data.disk = params.resources.disk
383 |             workspace_data.gpu = params.resources.gpu
384 |
385 |         response = self.workspace_api.create_workspace(
386 |             create_workspace=workspace_data, _request_timeout=timeout or None)
387 |         workspace_info = Workspace._to_workspace_info(response)
388 |         response.info = workspace_info
389 |
390 |         workspace = Workspace(
391 |             params.id,
392 |             response,
393 |             self.workspace_api,
394 |             self.toolbox_api,
395 |             code_toolbox
396 |         )
397 |
398 |         # Wait for workspace to start
399 |         try:
400 |             workspace.wait_for_workspace_start()
401 |         finally:
402 |             # If not Daytona SaaS, we don't need to handle pulling image state
403 |             pass
404 |
405 |         return workspace
406 |
407 |     def _get_code_toolbox(self, params: Optional[CreateWorkspaceParams] = None):
408 |         """Helper method to get the appropriate code toolbox based on language.
409 |
410 |         Args:
411 |             params (Optional[CreateWorkspaceParams]): Sandbox parameters. If not provided, defaults to Python toolbox.
412 |
413 |         Returns:
414 |             The appropriate code toolbox instance for the specified language.
415 |
416 |         Raises:
417 |             DaytonaError: If an unsupported language is specified.
418 |         """
419 |         if not params:
420 |             return WorkspacePythonCodeToolbox()
421 |
422 |         enum_language = to_enum(CodeLanguage, params.language)
423 |         if enum_language is None:
424 |             raise DaytonaError(f"Unsupported language: {params.language}")
425 |         else:
426 |             params.language = enum_language
427 |
428 |         match params.language:
429 |             case CodeLanguage.JAVASCRIPT | CodeLanguage.TYPESCRIPT:
430 |                 return WorkspaceTsCodeToolbox()
431 |             case CodeLanguage.PYTHON:
432 |                 return WorkspacePythonCodeToolbox()
433 |             case _:
434 |                 raise DaytonaError(f"Unsupported language: {params.language}")
435 |
436 |     @intercept_errors(message_prefix="Failed to remove workspace: ")
437 |     def remove(self, workspace: Workspace, timeout: Optional[float] = 60) -> None:
438 |         """Removes a Sandbox.
439 |
440 |         Args:
441 |             workspace (Workspace): The Sandbox instance to remove.
442 |             timeout (Optional[float]): Timeout (in seconds) for workspace removal. 0 means no timeout. Default is 60 seconds.
443 |
444 |         Raises:
445 |             DaytonaError: If workspace fails to remove or times out
446 |
447 |         Example:
448 |             ```python
449 |             workspace = daytona.create()
450 |             # ... use workspace ...
451 |             daytona.remove(workspace)  # Clean up when done
452 |             ```
453 |         """
454 |         return self.workspace_api.delete_workspace(workspace_id=workspace.id, force=True, _request_timeout=timeout or None)
455 |
456 |     @intercept_errors(message_prefix="Failed to get workspace: ")
457 |     def get_current_workspace(self, workspace_id: str) -> Workspace:
458 |         """Get a Sandbox by its ID.
459 |
460 |         Args:
461 |             workspace_id (str): The ID of the Sandbox to retrieve.
462 |
463 |         Returns:
464 |             Workspace: The Sandbox instance.
465 |
466 |         Raises:
467 |             DaytonaError: If workspace_id is not provided.
468 |
469 |         Example:
470 |             ```python
471 |             workspace = daytona.get_current_workspace("my-workspace-id")
472 |             print(workspace.status)
473 |             ```
474 |         """
475 |         if not workspace_id:
476 |             raise DaytonaError("workspace_id is required")
477 |
478 |         # Get the workspace instance
479 |         workspace_instance = self.workspace_api.get_workspace(
480 |             workspace_id=workspace_id)
481 |         workspace_info = Workspace._to_workspace_info(workspace_instance)
482 |         workspace_instance.info = workspace_info
483 |
484 |         # Create and return workspace with Python code toolbox as default
485 |         code_toolbox = WorkspacePythonCodeToolbox()
486 |         return Workspace(
487 |             workspace_id,
488 |             workspace_instance,
489 |             self.workspace_api,
490 |             self.toolbox_api,
491 |             code_toolbox
492 |         )
493 |
494 |     @intercept_errors(message_prefix="Failed to list workspaces: ")
495 |     def list(self) -> List[Workspace]:
496 |         """Lists all Sandboxes.
497 |
498 |         Returns:
499 |             List[Workspace]: List of all available Sandbox instances.
500 |
501 |         Example:
502 |             ```python
503 |             workspaces = daytona.list()
504 |             for workspace in workspaces:
505 |                 print(f"{workspace.id}: {workspace.status}")
506 |             ```
507 |         """
508 |         workspaces = self.workspace_api.list_workspaces()
509 |
510 |         for workspace in workspaces:
511 |             workspace_info = Workspace._to_workspace_info(workspace)
512 |             workspace.info = workspace_info
513 |
514 |         return [
515 |             Workspace(
516 |                 workspace.id,
517 |                 workspace,
518 |                 self.workspace_api,
519 |                 self.toolbox_api,
520 |                 self._get_code_toolbox(
521 |                     CreateWorkspaceParams(
522 |                         language=self._validate_language_label(
523 |                             workspace.labels.get("code-toolbox-language"))
524 |                     )
525 |                 )
526 |             )
527 |             for workspace in workspaces
528 |         ]
529 |
530 |     def _validate_language_label(self, language: Optional[str]) -> CodeLanguage:
531 |         """Validates and normalizes the language label.
532 |
533 |         Args:
534 |             language (Optional[str]): The language label to validate.
535 |
536 |         Returns:
537 |             CodeLanguage: The validated language, defaults to "python" if None
538 |
539 |         Raises:
540 |             DaytonaError: If the language is not supported.
541 |         """
542 |         if not language:
543 |             return CodeLanguage.PYTHON
544 |
545 |         enum_language = to_enum(CodeLanguage, language)
546 |         if enum_language is None:
547 |             raise DaytonaError(f"Invalid code-toolbox-language: {language}")
548 |         else:
549 |             return enum_language
550 |
551 |     # def resize(self, workspace: Workspace, resources: WorkspaceResources) -> None:
552 |     #     """Resizes a workspace.
553 |
554 |     #     Args:
555 |     #         workspace: The workspace to resize
556 |     #         resources: The new resources to set
557 |     #     """
558 |     #     self.workspace_api. (workspace_id=workspace.id, resources=resources)
559 |
560 |     def start(self, workspace: Workspace, timeout: Optional[float] = 60) -> None:
561 |         """Starts a Sandbox and waits for it to be ready.
562 |
563 |         Args:
564 |             workspace (Workspace): The Sandbox to start.
565 |             timeout (Optional[float]): Optional timeout in seconds to wait for the Sandbox to start. 0 means no timeout. Default is 60 seconds.
566 |
567 |         Raises:
568 |             DaytonaError: If timeout is negative; If Sandbox fails to start or times out
569 |         """
570 |         workspace.start(timeout)
571 |
572 |     def stop(self, workspace: Workspace, timeout: Optional[float] = 60) -> None:
573 |         """Stops a Sandbox and waits for it to be stopped.
574 |
575 |         Args:
576 |             workspace (Workspace): The workspace to stop
577 |             timeout (Optional[float]): Optional timeout (in seconds) for workspace stop. 0 means no timeout. Default is 60 seconds.
578 |
579 |         Raises:
580 |             DaytonaError: If timeout is negative; If Sandbox fails to stop or times out
581 |         """
582 |         workspace.stop(timeout)
583 |
584 |
585 | # Export these at module level
586 | __all__ = [
587 |     "Daytona",
588 |     "DaytonaConfig",
589 |     "CreateWorkspaceParams",
590 |     "CodeLanguage",
591 |     "Workspace",
592 |     "SessionExecuteRequest",
593 |     "SessionExecuteResponse"
594 | ]
595 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/filesystem.py:
--------------------------------------------------------------------------------
  1 | """
  2 | The Daytona SDK provides comprehensive file system operations through the `fs` module in Sandboxes.
  3 | You can perform various operations like listing files, creating directories, reading and writing files, and more.
  4 | This guide covers all available file system operations and best practices.
  5 |
  6 | Examples:
  7 |     Basic file operations:
  8 |     ```python
  9 |     workspace = daytona.create()
 10 |
 11 |     # Create a directory
 12 |     workspace.fs.create_folder("/workspace/data", "755")
 13 |
 14 |     # Upload a file
 15 |     with open("local_file.txt", "rb") as f:
 16 |         content = f.read()
 17 |     workspace.fs.upload_file("/workspace/data/file.txt", content)
 18 |
 19 |     # List directory contents
 20 |     files = workspace.fs.list_files("/workspace")
 21 |     for file in files:
 22 |         print(f"Name: {file.name}")
 23 |         print(f"Is directory: {file.is_dir}")
 24 |         print(f"Size: {file.size}")
 25 |         print(f"Modified: {file.mod_time}")
 26 |
 27 |     # Search file contents
 28 |     matches = workspace.fs.find_files(
 29 |         path="/workspace/src",
 30 |         pattern="text-of-interest"
 31 |     )
 32 |     for match in matches:
 33 |         print(f"Absolute file path: {match.file}")
 34 |         print(f"Line number: {match.line}")
 35 |         print(f"Line content: {match.content}")
 36 |         print("\n")
 37 |     ```
 38 |
 39 |     File manipulation:
 40 |     ```python
 41 |     # Move files
 42 |     workspace.fs.move_files(
 43 |         "/workspace/data/old.txt",
 44 |         "/workspace/data/new.txt"
 45 |     )
 46 |
 47 |     # Replace text in files
 48 |     results = workspace.fs.replace_in_files(
 49 |         files=["/workspace/data/new.txt"],
 50 |         pattern="old_version",
 51 |         new_value="new_version"
 52 |     )
 53 |
 54 |     # Set permissions
 55 |     workspace.fs.set_file_permissions(
 56 |         path="/workspace/data/script.sh",
 57 |         mode="755",
 58 |         owner="daytona"
 59 |     )
 60 |     ```
 61 |
 62 | Note:
 63 |     All paths should be absolute paths within the Sandbox if not explicitly
 64 |     stated otherwise.
 65 | """
 66 |
 67 | from typing import List
 68 | from daytona_api_client import (
 69 |     FileInfo,
 70 |     Match,
 71 |     ReplaceRequest,
 72 |     ReplaceResult,
 73 |     SearchFilesResponse,
 74 |     ToolboxApi,
 75 | )
 76 | from daytona_sdk._utils.errors import intercept_errors
 77 | from .protocols import WorkspaceInstance
 78 |
 79 |
 80 | class FileSystem:
 81 |     """Provides file system operations within a Sandbox.
 82 |
 83 |     This class implements a high-level interface to file system operations that can
 84 |     be performed within a Daytona Sandbox. It supports common operations like
 85 |     creating, deleting, and moving files, as well as searching file contents and
 86 |     managing permissions.
 87 |
 88 |     Attributes:
 89 |         instance (WorkspaceInstance): The Sandbox instance this file system belongs to.
 90 |     """
 91 |
 92 |     def __init__(self, instance: WorkspaceInstance, toolbox_api: ToolboxApi):
 93 |         """Initializes a new FileSystem instance.
 94 |
 95 |         Args:
 96 |             instance (WorkspaceInstance): The Sandbox instance this file system belongs to.
 97 |             toolbox_api (ToolboxApi): API client for Sandbox operations.
 98 |         """
 99 |         self.instance = instance
100 |         self.toolbox_api = toolbox_api
101 |
102 |     @intercept_errors(message_prefix="Failed to create folder: ")
103 |     def create_folder(self, path: str, mode: str) -> None:
104 |         """Creates a new directory in the Sandbox.
105 |
106 |         This method creates a new directory at the specified path with the given
107 |         permissions.
108 |
109 |         Args:
110 |             path (str): Absolute path where the folder should be created.
111 |             mode (str): Folder permissions in octal format (e.g., "755" for rwxr-xr-x).
112 |
113 |         Example:
114 |             ```python
115 |             # Create a directory with standard permissions
116 |             workspace.fs.create_folder("/workspace/data", "755")
117 |
118 |             # Create a private directory
119 |             workspace.fs.create_folder("/workspace/secrets", "700")
120 |             ```
121 |         """
122 |         self.toolbox_api.create_folder(
123 |             workspace_id=self.instance.id, path=path, mode=mode
124 |         )
125 |
126 |     @intercept_errors(message_prefix="Failed to delete file: ")
127 |     def delete_file(self, path: str) -> None:
128 |         """Deletes a file from the Sandbox.
129 |
130 |         This method permanently deletes a file from the Sandbox.
131 |
132 |         Args:
133 |             path (str): Absolute path to the file to delete.
134 |
135 |         Example:
136 |             ```python
137 |             # Delete a file
138 |             workspace.fs.delete_file("/workspace/data/old_file.txt")
139 |             ```
140 |         """
141 |         self.toolbox_api.delete_file(
142 |             workspace_id=self.instance.id, path=path
143 |         )
144 |
145 |     @intercept_errors(message_prefix="Failed to download file: ")
146 |     def download_file(self, path: str) -> bytes:
147 |         """Downloads a file from the Sandbox.
148 |
149 |         This method retrieves the contents of a file from the Sandbox.
150 |
151 |         Args:
152 |             path (str): Absolute path to the file to download.
153 |
154 |         Returns:
155 |             bytes: The file contents as a bytes object.
156 |
157 |         Example:
158 |             ```python
159 |             # Download and save a file locally
160 |             content = workspace.fs.download_file("/workspace/data/file.txt")
161 |             with open("local_copy.txt", "wb") as f:
162 |                 f.write(content)
163 |
164 |             # Download and process text content
165 |             content = workspace.fs.download_file("/workspace/data/config.json")
166 |             config = json.loads(content.decode('utf-8'))
167 |             ```
168 |         """
169 |         return self.toolbox_api.download_file(
170 |             workspace_id=self.instance.id, path=path
171 |         )
172 |
173 |     @intercept_errors(message_prefix="Failed to find files: ")
174 |     def find_files(self, path: str, pattern: str) -> List[Match]:
175 |         """Searches for files containing a pattern.
176 |
177 |         This method searches file contents for a specified pattern, similar to
178 |         the grep command.
179 |
180 |         Args:
181 |             path (str): Absolute path to the file or directory to search. If the path is a directory, the search will be performed recursively.
182 |             pattern (str): Search pattern to match against file contents.
183 |
184 |         Returns:
185 |             List[Match]: List of matches found in files. Each Match object includes:
186 |                 - file: Path to the file containing the match
187 |                 - line: The line number where the match was found
188 |                 - content: The matching line content
189 |
190 |         Example:
191 |             ```python
192 |             # Search for TODOs in Python files
193 |             matches = workspace.fs.find_files("/workspace/src", "TODO:")
194 |             for match in matches:
195 |                 print(f"{match.file}:{match.line}: {match.content.strip()}")
196 |             ```
197 |         """
198 |         return self.toolbox_api.find_in_files(
199 |             workspace_id=self.instance.id, path=path, pattern=pattern
200 |         )
201 |
202 |     @intercept_errors(message_prefix="Failed to get file info: ")
203 |     def get_file_info(self, path: str) -> FileInfo:
204 |         """Gets detailed information about a file.
205 |
206 |         This method retrieves metadata about a file or directory, including its
207 |         size, permissions, and timestamps.
208 |
209 |         Args:
210 |             path (str): Absolute path to the file or directory.
211 |
212 |         Returns:
213 |             FileInfo: Detailed file information including:
214 |                 - name: File name
215 |                 - is_dir: Whether the path is a directory
216 |                 - size: File size in bytes
217 |                 - mode: File permissions
218 |                 - mod_time: Last modification timestamp
219 |                 - permissions: File permissions in octal format
220 |                 - owner: File owner
221 |                 - group: File group
222 |
223 |         Example:
224 |             ```python
225 |             # Get file metadata
226 |             info = workspace.fs.get_file_info("/workspace/data/file.txt")
227 |             print(f"Size: {info.size} bytes")
228 |             print(f"Modified: {info.mod_time}")
229 |             print(f"Mode: {info.mode}")
230 |
231 |             # Check if path is a directory
232 |             info = workspace.fs.get_file_info("/workspace/data")
233 |             if info.is_dir:
234 |                 print("Path is a directory")
235 |             ```
236 |         """
237 |         return self.toolbox_api.get_file_info(
238 |             workspace_id=self.instance.id, path=path
239 |         )
240 |
241 |     @intercept_errors(message_prefix="Failed to list files: ")
242 |     def list_files(self, path: str) -> List[FileInfo]:
243 |         """Lists files and directories in a given path.
244 |
245 |         This method returns information about all files and directories in the
246 |         specified directory, similar to the ls -l command.
247 |
248 |         Args:
249 |             path (str): Absolute path to the directory to list contents from.
250 |
251 |         Returns:
252 |             List[FileInfo]: List of file and directory information. Each FileInfo
253 |                 object includes the same fields as described in get_file_info().
254 |
255 |         Example:
256 |             ```python
257 |             # List directory contents
258 |             files = workspace.fs.list_files("/workspace/data")
259 |
260 |             # Print files and their sizes
261 |             for file in files:
262 |                 if not file.is_dir:
263 |                     print(f"{file.name}: {file.size} bytes")
264 |
265 |             # List only directories
266 |             dirs = [f for f in files if f.is_dir]
267 |             print("Subdirectories:", ", ".join(d.name for d in dirs))
268 |             ```
269 |         """
270 |         return self.toolbox_api.list_files(
271 |             workspace_id=self.instance.id, path=path
272 |         )
273 |
274 |     @intercept_errors(message_prefix="Failed to move files: ")
275 |     def move_files(self, source: str, destination: str) -> None:
276 |         """Moves files from one location to another.
277 |
278 |         This method moves or renames a file or directory. The parent directory
279 |         of the destination must exist.
280 |
281 |         Args:
282 |             source (str): Absolute path to the source file or directory.
283 |             destination (str): Absolute path to the destination.
284 |
285 |         Example:
286 |             ```python
287 |             # Rename a file
288 |             workspace.fs.move_files(
289 |                 "/workspace/data/old_name.txt",
290 |                 "/workspace/data/new_name.txt"
291 |             )
292 |
293 |             # Move a file to a different directory
294 |             workspace.fs.move_files(
295 |                 "/workspace/data/file.txt",
296 |                 "/workspace/archive/file.txt"
297 |             )
298 |
299 |             # Move a directory
300 |             workspace.fs.move_files(
301 |                 "/workspace/old_dir",
302 |                 "/workspace/new_dir"
303 |             )
304 |             ```
305 |         """
306 |         self.toolbox_api.move_file(
307 |             workspace_id=self.instance.id,
308 |             source=source,
309 |             destination=destination,
310 |         )
311 |
312 |     @intercept_errors(message_prefix="Failed to replace in files: ")
313 |     def replace_in_files(
314 |         self, files: List[str], pattern: str, new_value: str
315 |     ) -> List[ReplaceResult]:
316 |         """Replaces text in multiple files.
317 |
318 |         This method performs search and replace operations across multiple files.
319 |
320 |         Args:
321 |             files (List[str]): List of absolute file paths to perform replacements in.
322 |             pattern (str): Pattern to search for.
323 |             new_value (str): Text to replace matches with.
324 |
325 |         Returns:
326 |             List[ReplaceResult]: List of results indicating replacements made in
327 |                 each file. Each ReplaceResult includes:
328 |                 - file: Path to the modified file
329 |                 - success: Whether the operation was successful
330 |                 - error: Error message if the operation failed
331 |
332 |         Example:
333 |             ```python
334 |             # Replace in specific files
335 |             results = workspace.fs.replace_in_files(
336 |                 files=["/workspace/src/file1.py", "/workspace/src/file2.py"],
337 |                 pattern="old_function",
338 |                 new_value="new_function"
339 |             )
340 |
341 |             # Print results
342 |             for result in results:
343 |                 if result.success:
344 |                     print(f"{result.file}: {result.success}")
345 |                 else:
346 |                     print(f"{result.file}: {result.error}")
347 |             ```
348 |         """
349 |         replace_request = ReplaceRequest(
350 |             files=files, new_value=new_value, pattern=pattern
351 |         )
352 |
353 |         return self.toolbox_api.replace_in_files(
354 |             workspace_id=self.instance.id, replace_request=replace_request
355 |         )
356 |
357 |     @intercept_errors(message_prefix="Failed to search files: ")
358 |     def search_files(self, path: str, pattern: str) -> SearchFilesResponse:
359 |         """Searches for files and directories matching a pattern in their names.
360 |
361 |         This method searches for files and directories whose names match the
362 |         specified pattern. The pattern can be a simple string or a glob pattern.
363 |
364 |         Args:
365 |             path (str): Absolute path to the root directory to start search from.
366 |             pattern (str): Pattern to match against file names. Supports glob
367 |                 patterns (e.g., "*.py" for Python files).
368 |
369 |         Returns:
370 |             SearchFilesResponse: Search results containing:
371 |                 - files: List of matching file and directory paths
372 |
373 |         Example:
374 |             ```python
375 |             # Find all Python files
376 |             result = workspace.fs.search_files("/workspace", "*.py")
377 |             for file in result.files:
378 |                 print(file)
379 |
380 |             # Find files with specific prefix
381 |             result = workspace.fs.search_files("/workspace/data", "test_*")
382 |             print(f"Found {len(result.files)} test files")
383 |             ```
384 |         """
385 |         return self.toolbox_api.search_files(
386 |             workspace_id=self.instance.id, path=path, pattern=pattern
387 |         )
388 |
389 |     @intercept_errors(message_prefix="Failed to set file permissions: ")
390 |     def set_file_permissions(
391 |         self, path: str, mode: str = None, owner: str = None, group: str = None
392 |     ) -> None:
393 |         """Sets permissions and ownership for a file or directory.
394 |
395 |         This method allows changing the permissions and ownership of a file or
396 |         directory. Any of the parameters can be None to leave that attribute
397 |         unchanged.
398 |
399 |         Args:
400 |             path (str): Absolute path to the file or directory.
401 |             mode (Optional[str]): File mode/permissions in octal format
402 |                 (e.g., "644" for rw-r--r--).
403 |             owner (Optional[str]): User owner of the file.
404 |             group (Optional[str]): Group owner of the file.
405 |
406 |         Example:
407 |             ```python
408 |             # Make a file executable
409 |             workspace.fs.set_file_permissions(
410 |                 path="/workspace/scripts/run.sh",
411 |                 mode="755"  # rwxr-xr-x
412 |             )
413 |
414 |             # Change file owner
415 |             workspace.fs.set_file_permissions(
416 |                 path="/workspace/data/file.txt",
417 |                 owner="daytona",
418 |                 group="daytona"
419 |             )
420 |             ```
421 |         """
422 |         self.toolbox_api.set_file_permissions(
423 |             workspace_id=self.instance.id,
424 |             path=path,
425 |             mode=mode,
426 |             owner=owner,
427 |             group=group,
428 |         )
429 |
430 |     @intercept_errors(message_prefix="Failed to upload file: ")
431 |     def upload_file(self, path: str, file: bytes) -> None:
432 |         """Uploads a file to the Sandbox.
433 |
434 |         This method uploads a file to the specified path in the Sandbox. The
435 |         parent directory must exist. If a file already exists at the destination
436 |         path, it will be overwritten.
437 |
438 |         Args:
439 |             path (str): Absolute destination path in the Sandbox.
440 |             file (bytes): File contents as a bytes object.
441 |
442 |         Example:
443 |             ```python
444 |             # Upload a text file
445 |             content = b"Hello, World!"
446 |             workspace.fs.upload_file("/workspace/data/hello.txt", content)
447 |
448 |             # Upload a local file
449 |             with open("local_file.txt", "rb") as f:
450 |                 content = f.read()
451 |             workspace.fs.upload_file("/workspace/data/file.txt", content)
452 |
453 |             # Upload binary data
454 |             import json
455 |             data = {"key": "value"}
456 |             content = json.dumps(data).encode('utf-8')
457 |             workspace.fs.upload_file("/workspace/data/config.json", content)
458 |             ```
459 |         """
460 |         self.toolbox_api.upload_file(
461 |             workspace_id=self.instance.id, path=path, file=file
462 |         )
463 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/git.py:
--------------------------------------------------------------------------------
  1 | """
  2 | The Daytona SDK provides built-in Git support. This guide covers all available Git
  3 | operations and best practices. Daytona SDK provides an option to clone, check status,
  4 | and manage Git repositories in Sandboxes. You can interact with Git repositories using
  5 | the `git` module.
  6 |
  7 | Example:
  8 |     Basic Git workflow:
  9 |     ```python
 10 |     workspace = daytona.create()
 11 |
 12 |     # Clone a repository
 13 |     workspace.git.clone(
 14 |         url="https://github.com/user/repo.git",
 15 |         path="/workspace/repo"
 16 |     )
 17 |
 18 |     # Make some changes
 19 |     workspace.fs.upload_file("/workspace/repo/test.txt", "Hello, World!")
 20 |
 21 |     # Stage and commit changes
 22 |     workspace.git.add("/workspace/repo", ["test.txt"])
 23 |     workspace.git.commit(
 24 |         path="/workspace/repo",
 25 |         message="Add test file",
 26 |         author="John Doe",
 27 |         email="john@example.com"
 28 |     )
 29 |
 30 |     # Push changes (with authentication)
 31 |     workspace.git.push(
 32 |         path="/workspace/repo",
 33 |         username="user",
 34 |         password="token"
 35 |     )
 36 |     ```
 37 |
 38 | Note:
 39 |     All paths should be absolute paths within the Sandbox if not explicitly
 40 |     stated otherwise.
 41 | """
 42 |
 43 | from typing import List, Optional, TYPE_CHECKING
 44 | from daytona_api_client import (
 45 |     GitStatus,
 46 |     ListBranchResponse,
 47 |     ToolboxApi,
 48 |     GitAddRequest,
 49 |     GitCloneRequest,
 50 |     GitCommitRequest,
 51 |     GitRepoRequest,
 52 | )
 53 | from daytona_sdk._utils.errors import intercept_errors
 54 | from .protocols import WorkspaceInstance
 55 |
 56 | if TYPE_CHECKING:
 57 |     from .workspace import Workspace
 58 |
 59 |
 60 | class Git:
 61 |     """Provides Git operations within a Sandbox.
 62 |
 63 |     This class implements a high-level interface to Git operations that can be
 64 |     performed within a Daytona Sandbox. It supports common Git operations like
 65 |     cloning repositories, staging and committing changes, pushing and pulling
 66 |     changes, and checking repository status.
 67 |
 68 |     Attributes:
 69 |         workspace (Workspace): The parent Sandbox instance.
 70 |         instance (WorkspaceInstance): The Sandbox instance this Git handler belongs to.
 71 |
 72 |     Example:
 73 |         ```python
 74 |         # Clone a repository
 75 |         workspace.git.clone(
 76 |             url="https://github.com/user/repo.git",
 77 |             path="/workspace/repo"
 78 |         )
 79 |
 80 |         # Check repository status
 81 |         status = workspace.git.status("/workspace/repo")
 82 |         print(f"Modified files: {status.modified}")
 83 |
 84 |         # Stage and commit changes
 85 |         workspace.git.add("/workspace/repo", ["file.txt"])
 86 |         workspace.git.commit(
 87 |             path="/workspace/repo",
 88 |             message="Update file",
 89 |             author="John Doe",
 90 |             email="john@example.com"
 91 |         )
 92 |         ```
 93 |     """
 94 |
 95 |     def __init__(
 96 |         self,
 97 |         workspace: "Workspace",
 98 |         toolbox_api: ToolboxApi,
 99 |         instance: WorkspaceInstance,
100 |     ):
101 |         """Initializes a new Git handler instance.
102 |
103 |         Args:
104 |             workspace (Workspace): The parent Sandbox instance.
105 |             toolbox_api (ToolboxApi): API client for Sandbox operations.
106 |             instance (WorkspaceInstance): The Sandbox instance this Git handler belongs to.
107 |         """
108 |         self.workspace = workspace
109 |         self.toolbox_api = toolbox_api
110 |         self.instance = instance
111 |
112 |     @intercept_errors(message_prefix="Failed to add files: ")
113 |     def add(self, path: str, files: List[str]) -> None:
114 |         """Stages files for commit.
115 |
116 |         This method stages the specified files for the next commit, similar to
117 |         running 'git add' on the command line.
118 |
119 |         Args:
120 |             path (str): Absolute path to the Git repository root.
121 |             files (List[str]): List of file paths or directories to stage, relative to the repository root.
122 |
123 |         Example:
124 |             ```python
125 |             # Stage a single file
126 |             workspace.git.add("/workspace/repo", ["file.txt"])
127 |
128 |             # Stage multiple files
129 |             workspace.git.add("/workspace/repo", [
130 |                 "src/main.py",
131 |                 "tests/test_main.py",
132 |                 "README.md"
133 |             ])
134 |             ```
135 |         """
136 |         self.toolbox_api.git_add_files(
137 |             workspace_id=self.instance.id,
138 |             git_add_request=GitAddRequest(
139 |                 path=path,
140 |                 files=files
141 |             ),
142 |         )
143 |
144 |     @intercept_errors(message_prefix="Failed to list branches: ")
145 |     def branches(self, path: str) -> ListBranchResponse:
146 |         """Lists branches in the repository.
147 |
148 |         This method returns information about all branches in the repository.
149 |
150 |         Args:
151 |             path (str): Absolute path to the Git repository root.
152 |
153 |         Returns:
154 |             ListBranchResponse: List of branches in the repository.
155 |
156 |         Example:
157 |             ```python
158 |             response = workspace.git.branches("/workspace/repo")
159 |             print(f"Branches: {response.branches}")
160 |             ```
161 |         """
162 |         return self.toolbox_api.git_list_branches(
163 |             workspace_id=self.instance.id,
164 |             path=path,
165 |         )
166 |
167 |     @intercept_errors(message_prefix="Failed to clone repository: ")
168 |     def clone(
169 |         self,
170 |         url: str,
171 |         path: str,
172 |         branch: Optional[str] = None,
173 |         commit_id: Optional[str] = None,
174 |         username: Optional[str] = None,
175 |         password: Optional[str] = None,
176 |     ) -> None:
177 |         """Clones a Git repository.
178 |
179 |         This method clones a Git repository into the specified path. It supports
180 |         cloning specific branches or commits, and can authenticate with the remote
181 |         repository if credentials are provided.
182 |
183 |         Args:
184 |             url (str): Repository URL to clone from.
185 |             path (str): Absolute path where the repository should be cloned.
186 |             branch (Optional[str]): Specific branch to clone. If not specified,
187 |                 clones the default branch.
188 |             commit_id (Optional[str]): Specific commit to clone. If specified,
189 |                 the repository will be left in a detached HEAD state at this commit.
190 |             username (Optional[str]): Git username for authentication.
191 |             password (Optional[str]): Git password or token for authentication.
192 |
193 |         Example:
194 |             ```python
195 |             # Clone the default branch
196 |             workspace.git.clone(
197 |                 url="https://github.com/user/repo.git",
198 |                 path="/workspace/repo"
199 |             )
200 |
201 |             # Clone a specific branch with authentication
202 |             workspace.git.clone(
203 |                 url="https://github.com/user/private-repo.git",
204 |                 path="/workspace/private",
205 |                 branch="develop",
206 |                 username="user",
207 |                 password="token"
208 |             )
209 |
210 |             # Clone a specific commit
211 |             workspace.git.clone(
212 |                 url="https://github.com/user/repo.git",
213 |                 path="/workspace/repo-old",
214 |                 commit_id="abc123"
215 |             )
216 |             ```
217 |         """
218 |         self.toolbox_api.git_clone_repository(
219 |             workspace_id=self.instance.id,
220 |             git_clone_request=GitCloneRequest(
221 |                 url=url,
222 |                 branch=branch,
223 |                 path=path,
224 |                 username=username,
225 |                 password=password,
226 |                 commitId=commit_id,
227 |             )
228 |         )
229 |
230 |     @intercept_errors(message_prefix="Failed to commit changes: ")
231 |     def commit(self, path: str, message: str, author: str, email: str) -> None:
232 |         """Commits staged changes.
233 |
234 |         This method creates a new commit with the staged changes. Make sure to stage
235 |         changes using the add() method before committing.
236 |
237 |         Args:
238 |             path (str): Absolute path to the Git repository root.
239 |             message (str): Commit message describing the changes.
240 |             author (str): Name of the commit author.
241 |             email (str): Email address of the commit author.
242 |
243 |         Example:
244 |             ```python
245 |             # Stage and commit changes
246 |             workspace.git.add("/workspace/repo", ["README.md"])
247 |             workspace.git.commit(
248 |                 path="/workspace/repo",
249 |                 message="Update documentation",
250 |                 author="John Doe",
251 |                 email="john@example.com"
252 |             )
253 |             ```
254 |         """
255 |         self.toolbox_api.git_commit_changes(
256 |             workspace_id=self.instance.id,
257 |             git_commit_request=GitCommitRequest(
258 |                 path=path,
259 |                 message=message,
260 |                 author=author,
261 |                 email=email
262 |             ),
263 |         )
264 |
265 |     @intercept_errors(message_prefix="Failed to push changes: ")
266 |     def push(
267 |         self, path: str, username: Optional[str] = None, password: Optional[str] = None
268 |     ) -> None:
269 |         """Pushes local commits to the remote repository.
270 |
271 |         This method pushes all local commits on the current branch to the remote
272 |         repository. If the remote repository requires authentication, provide
273 |         username and password/token.
274 |
275 |         Args:
276 |             path (str): Absolute path to the Git repository root.
277 |             username (Optional[str]): Git username for authentication.
278 |             password (Optional[str]): Git password or token for authentication.
279 |
280 |         Example:
281 |             ```python
282 |             # Push without authentication (for public repos or SSH)
283 |             workspace.git.push("/workspace/repo")
284 |
285 |             # Push with authentication
286 |             workspace.git.push(
287 |                 path="/workspace/repo",
288 |                 username="user",
289 |                 password="github_token"
290 |             )
291 |             ```
292 |         """
293 |         self.toolbox_api.git_push_changes(
294 |             workspace_id=self.instance.id,
295 |             git_repo_request=GitRepoRequest(
296 |                 path=path,
297 |                 username=username,
298 |                 password=password
299 |             ),
300 |         )
301 |
302 |     @intercept_errors(message_prefix="Failed to pull changes: ")
303 |     def pull(
304 |         self, path: str, username: Optional[str] = None, password: Optional[str] = None
305 |     ) -> None:
306 |         """Pulls changes from the remote repository.
307 |
308 |         This method fetches and merges changes from the remote repository into
309 |         the current branch. If the remote repository requires authentication,
310 |         provide username and password/token.
311 |
312 |         Args:
313 |             path (str): Absolute path to the Git repository root.
314 |             username (Optional[str]): Git username for authentication.
315 |             password (Optional[str]): Git password or token for authentication.
316 |
317 |         Example:
318 |             ```python
319 |             # Pull without authentication
320 |             workspace.git.pull("/workspace/repo")
321 |
322 |             # Pull with authentication
323 |             workspace.git.pull(
324 |                 path="/workspace/repo",
325 |                 username="user",
326 |                 password="github_token"
327 |             )
328 |             ```
329 |         """
330 |         self.toolbox_api.git_pull_changes(
331 |             workspace_id=self.instance.id,
332 |             git_repo_request=GitRepoRequest(
333 |                 path=path,
334 |                 username=username,
335 |                 password=password
336 |             ),
337 |         )
338 |
339 |     @intercept_errors(message_prefix="Failed to get status: ")
340 |     def status(self, path: str) -> GitStatus:
341 |         """Gets the current Git repository status.
342 |
343 |         This method returns detailed information about the current state of the
344 |         repository, including staged, unstaged, and untracked files.
345 |
346 |         Args:
347 |             path (str): Absolute path to the Git repository root.
348 |
349 |         Returns:
350 |             GitStatus: Repository status information including:
351 |                 - current_branch: Current branch name
352 |                 - file_status: List of file statuses
353 |                 - ahead: Number of local commits not pushed to remote
354 |                 - behind: Number of remote commits not pulled locally
355 |                 - branch_published: Whether the branch has been published to the remote repository
356 |
357 |         Example:
358 |             ```python
359 |             status = workspace.git.status("/workspace/repo")
360 |             print(f"On branch: {status.current_branch}")
361 |             print(f"Commits ahead: {status.ahead}")
362 |             print(f"Commits behind: {status.behind}")
363 |             ```
364 |         """
365 |         return self.toolbox_api.git_get_status(
366 |             workspace_id=self.instance.id,
367 |             path=path,
368 |         )
369 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/lsp_server.py:
--------------------------------------------------------------------------------
  1 | """
  2 | The Daytona SDK provides Language Server Protocol (LSP) support through Sandbox instances.
  3 | This enables advanced language features like code completion, diagnostics, and more.
  4 |
  5 | Example:
  6 |     Basic LSP server usage:
  7 |     ```python
  8 |     workspace = daytona.create()
  9 |
 10 |     # Create and start LSP server
 11 |     lsp = workspace.create_lsp_server("typescript", "/workspace/project")
 12 |     lsp.start()
 13 |
 14 |     # Open a file for editing
 15 |     lsp.did_open("/workspace/project/src/index.ts")
 16 |
 17 |     # Get completions at a position
 18 |     pos = Position(line=10, character=15)
 19 |     completions = lsp.completions("/workspace/project/src/index.ts", pos)
 20 |     print(f"Completions: {completions}")
 21 |
 22 |     # Get document symbols
 23 |     symbols = lsp.document_symbols("/workspace/project/src/index.ts")
 24 |     for symbol in symbols:
 25 |         print(f"{symbol.name}: {symbol.kind}")
 26 |
 27 |     # Clean up
 28 |     lsp.did_close("/workspace/project/src/index.ts")
 29 |     lsp.stop()
 30 |     ```
 31 |
 32 | Note:
 33 |     The LSP server must be started with start() before using any other methods,
 34 |     and should be stopped with stop() when no longer needed to free resources.
 35 | """
 36 | from enum import Enum
 37 | from typing import List
 38 | from daytona_api_client import (
 39 |     CompletionList,
 40 |     LspSymbol,
 41 |     ToolboxApi,
 42 |     LspServerRequest,
 43 |     LspDocumentRequest,
 44 |     LspCompletionParams
 45 | )
 46 | from daytona_sdk._utils.errors import intercept_errors
 47 | from .protocols import WorkspaceInstance
 48 |
 49 |
 50 | class LspLanguageId(Enum):
 51 |     PYTHON = "python"
 52 |     TYPESCRIPT = "typescript"
 53 |     JAVASCRIPT = "javascript"
 54 |
 55 |     def __str__(self):
 56 |         return self.value
 57 |
 58 |     def __eq__(self, other):
 59 |         if isinstance(other, str):
 60 |             return self.value == other
 61 |         return super().__eq__(other)
 62 |
 63 |
 64 | class Position:
 65 |     """Represents a position in a text document.
 66 |
 67 |     This class represents a zero-based position within a text document,
 68 |     specified by line number and character offset.
 69 |
 70 |     Attributes:
 71 |         line (int): Zero-based line number in the document.
 72 |         character (int): Zero-based character offset on the line.
 73 |     """
 74 |
 75 |     def __init__(self, line: int, character: int):
 76 |         """Initialize a new Position instance.
 77 |
 78 |         Args:
 79 |             line (int): Zero-based line number in the document.
 80 |             character (int): Zero-based character offset on the line.
 81 |         """
 82 |         self.line = line
 83 |         self.character = character
 84 |
 85 |
 86 | class LspServer:
 87 |     """Provides Language Server Protocol functionality for code intelligence.
 88 |
 89 |     This class implements a subset of the Language Server Protocol (LSP) to provide
 90 |     IDE-like features such as code completion, symbol search, and more.
 91 |
 92 |     Attributes:
 93 |         language_id (LspLanguageId): The language server type (e.g., "python", "typescript").
 94 |         path_to_project (str): Absolute path to the project root directory.
 95 |         instance (WorkspaceInstance): The Sandbox instance this server belongs to.
 96 |     """
 97 |
 98 |     def __init__(
 99 |         self,
100 |         language_id: LspLanguageId,
101 |         path_to_project: str,
102 |         toolbox_api: ToolboxApi,
103 |         instance: WorkspaceInstance,
104 |     ):
105 |         """Initializes a new LSP server instance.
106 |
107 |         Args:
108 |             language_id (LspLanguageId): The language server type (e.g., LspLanguageId.TYPESCRIPT).
109 |             path_to_project (str): Absolute path to the project root directory.
110 |             toolbox_api (ToolboxApi): API client for Sandbox operations.
111 |             instance (WorkspaceInstance): The Sandbox instance this server belongs to.
112 |         """
113 |         self.language_id = str(language_id)
114 |         self.path_to_project = path_to_project
115 |         self.toolbox_api = toolbox_api
116 |         self.instance = instance
117 |
118 |     @intercept_errors(message_prefix="Failed to start LSP server: ")
119 |     def start(self) -> None:
120 |         """Starts the language server.
121 |
122 |         This method must be called before using any other LSP functionality.
123 |         It initializes the language server for the specified language and project.
124 |
125 |         Example:
126 |             ```python
127 |             lsp = workspace.create_lsp_server("typescript", "/workspace/project")
128 |             lsp.start()  # Initialize the server
129 |             # Now ready for LSP operations
130 |             ```
131 |         """
132 |         self.toolbox_api.lsp_start(
133 |             workspace_id=self.instance.id,
134 |             lsp_server_request=LspServerRequest(
135 |                 language_id=self.language_id,
136 |                 path_to_project=self.path_to_project,
137 |             ),
138 |         )
139 |
140 |     @intercept_errors(message_prefix="Failed to stop LSP server: ")
141 |     def stop(self) -> None:
142 |         """Stops the language server.
143 |
144 |         This method should be called when the LSP server is no longer needed to
145 |         free up system resources.
146 |
147 |         Example:
148 |             ```python
149 |             # When done with LSP features
150 |             lsp.stop()  # Clean up resources
151 |             ```
152 |         """
153 |         self.toolbox_api.lsp_stop(
154 |             workspace_id=self.instance.id,
155 |             lsp_server_request=LspServerRequest(
156 |                 language_id=self.language_id,
157 |                 path_to_project=self.path_to_project,
158 |             ),
159 |         )
160 |
161 |     @intercept_errors(message_prefix="Failed to open file: ")
162 |     def did_open(self, path: str) -> None:
163 |         """Notifies the language server that a file has been opened.
164 |
165 |         This method should be called when a file is opened in the editor to enable
166 |         language features like diagnostics and completions for that file. The server
167 |         will begin tracking the file's contents and providing language features.
168 |
169 |         Args:
170 |             path (str): Absolute path to the opened file.
171 |
172 |         Example:
173 |             ```python
174 |             # When opening a file for editing
175 |             lsp.did_open("/workspace/project/src/index.ts")
176 |             # Now can get completions, symbols, etc. for this file
177 |             ```
178 |         """
179 |         self.toolbox_api.lsp_did_open(
180 |             workspace_id=self.instance.id,
181 |             lsp_document_request=LspDocumentRequest(
182 |                 language_id=self.language_id,
183 |                 path_to_project=self.path_to_project,
184 |                 uri=f"file://{path}",
185 |             ),
186 |         )
187 |
188 |     @intercept_errors(message_prefix="Failed to close file: ")
189 |     def did_close(self, path: str) -> None:
190 |         """Notify the language server that a file has been closed.
191 |
192 |         This method should be called when a file is closed in the editor to allow
193 |         the language server to clean up any resources associated with that file.
194 |         Args:
195 |             path (str): Absolute path to the closed file.
196 |
197 |         Example:
198 |             ```python
199 |             # When done editing a file
200 |             lsp.did_close("/workspace/project/src/index.ts")
201 |             ```
202 |         """
203 |         self.toolbox_api.lsp_did_close(
204 |             workspace_id=self.instance.id,
205 |             lsp_document_request=LspDocumentRequest(
206 |                 language_id=self.language_id,
207 |                 path_to_project=self.path_to_project,
208 |                 uri=f"file://{path}",
209 |             ),
210 |         )
211 |
212 |     @intercept_errors(message_prefix="Failed to get symbols from document: ")
213 |     def document_symbols(self, path: str) -> List[LspSymbol]:
214 |         """Gets symbol information from a document.
215 |
216 |         This method returns information about all symbols (functions, classes,
217 |         variables, etc.) defined in the specified document.
218 |
219 |         Args:
220 |             path (str): Absolute path to the file to get symbols from.
221 |
222 |         Returns:
223 |             List[LspSymbol]: List of symbols in the document. Each symbol includes:
224 |                 - name: The symbol's name
225 |                 - kind: The symbol's kind (function, class, variable, etc.)
226 |                 - location: The location of the symbol in the file
227 |
228 |         Example:
229 |             ```python
230 |             # Get all symbols in a file
231 |             symbols = lsp.document_symbols("/workspace/project/src/index.ts")
232 |             for symbol in symbols:
233 |                 print(f"{symbol.kind} {symbol.name}: {symbol.location}")
234 |             ```
235 |         """
236 |         return self.toolbox_api.lsp_document_symbols(
237 |             workspace_id=self.instance.id,
238 |             language_id=self.language_id,
239 |             path_to_project=self.path_to_project,
240 |             uri=f"file://{path}",
241 |         )
242 |
243 |     @intercept_errors(message_prefix="Failed to get symbols from workspace: ")
244 |     def workspace_symbols(self, query: str) -> List[LspSymbol]:
245 |         """Searches for symbols across the entire Sandbox.
246 |
247 |         This method searches for symbols matching the query string across all files
248 |         in the Sandbox. It's useful for finding declarations and definitions
249 |         without knowing which file they're in.
250 |
251 |         Args:
252 |             query (str): Search query to match against symbol names.
253 |
254 |         Returns:
255 |             List[LspSymbol]: List of matching symbols from all files. Each symbol
256 |                 includes:
257 |                 - name: The symbol's name
258 |                 - kind: The symbol's kind (function, class, variable, etc.)
259 |                 - location: The location of the symbol in the file
260 |
261 |         Example:
262 |             ```python
263 |             # Search for all symbols containing "User"
264 |             symbols = lsp.workspace_symbols("User")
265 |             for symbol in symbols:
266 |                 print(f"{symbol.name} in {symbol.location}")
267 |             ```
268 |         """
269 |         return self.toolbox_api.lsp_workspace_symbols(
270 |             workspace_id=self.instance.id,
271 |             language_id=self.language_id,
272 |             path_to_project=self.path_to_project,
273 |             query=query,
274 |         )
275 |
276 |     @intercept_errors(message_prefix="Failed to get completions: ")
277 |     def completions(self, path: str, position: Position) -> CompletionList:
278 |         """Gets completion suggestions at a position in a file.
279 |
280 |         Args:
281 |             path (str): Absolute path to the file.
282 |             position (Position): Cursor position to get completions for.
283 |
284 |         Returns:
285 |             CompletionList: List of completion suggestions. The list includes:
286 |                 - isIncomplete: Whether more items might be available
287 |                 - items: List of completion items, each containing:
288 |                     - label: The text to insert
289 |                     - kind: The kind of completion
290 |                     - detail: Additional details about the item
291 |                     - documentation: Documentation for the item
292 |                     - sortText: Text used to sort the item in the list
293 |                     - filterText: Text used to filter the item
294 |                     - insertText: The actual text to insert (if different from label)
295 |
296 |         Example:
297 |             ```python
298 |             # Get completions at a specific position
299 |             pos = Position(line=10, character=15)
300 |             completions = lsp.completions("/workspace/project/src/index.ts", pos)
301 |             for item in completions.items:
302 |                 print(f"{item.label} ({item.kind}): {item.detail}")
303 |             ```
304 |         """
305 |         return self.toolbox_api.lsp_completions(
306 |             workspace_id=self.instance.id,
307 |             lsp_completion_params=LspCompletionParams(
308 |                 language_id=self.language_id,
309 |                 path_to_project=self.path_to_project,
310 |                 uri=f"file://{path}",
311 |                 position=position,
312 |             ),
313 |         )
314 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/process.py:
--------------------------------------------------------------------------------
  1 | """
  2 | The Daytona SDK provides powerful process and code execution capabilities through
  3 | the `process` module in Sandboxes. This guide covers all available process operations
  4 | and best practices.
  5 |
  6 | Example:
  7 |     Basic command execution:
  8 |     ```python
  9 |     workspace = daytona.create()
 10 |
 11 |     # Execute a shell command
 12 |     response = workspace.process.exec("ls -la")
 13 |     print(response.result)
 14 |
 15 |     # Run Python code
 16 |     response = workspace.process.code_run("print('Hello, World!')")
 17 |     print(response.result)
 18 |     ```
 19 |
 20 |     Using interactive sessions:
 21 |     ```python
 22 |     # Create a new session
 23 |     session_id = "my-session"
 24 |     workspace.process.create_session(session_id)
 25 |
 26 |     # Execute commands in the session
 27 |     req = SessionExecuteRequest(command="cd /workspace", var_async=False)
 28 |     workspace.process.execute_session_command(session_id, req)
 29 |
 30 |     req = SessionExecuteRequest(command="pwd", var_async=False)
 31 |     response = workspace.process.execute_session_command(session_id, req)
 32 |     print(response.result)  # Should print "/workspace"
 33 |
 34 |     # Clean up
 35 |     workspace.process.delete_session(session_id)
 36 |     ```
 37 | """
 38 |
 39 | from typing import Optional, List, Dict
 40 | from daytona_api_client import (
 41 |     ToolboxApi,
 42 |     ExecuteResponse,
 43 |     ExecuteRequest,
 44 |     Session,
 45 |     SessionExecuteRequest,
 46 |     SessionExecuteResponse,
 47 |     CreateSessionRequest,
 48 |     Command
 49 | )
 50 |
 51 | from daytona_sdk._utils.errors import intercept_errors
 52 | from .code_toolbox.workspace_python_code_toolbox import WorkspacePythonCodeToolbox
 53 | from .protocols import WorkspaceInstance
 54 | from .common.code_run_params import CodeRunParams
 55 |
 56 |
 57 | class Process:
 58 |     """Handles process and code execution within a Sandbox.
 59 |
 60 |     This class provides methods for executing shell commands and running code in
 61 |     the Sandbox environment.
 62 |
 63 |     Attributes:
 64 |         code_toolbox (WorkspacePythonCodeToolbox): Language-specific code execution toolbox.
 65 |         toolbox_api (ToolboxApi): API client for Sandbox operations.
 66 |         instance (WorkspaceInstance): The Sandbox instance this process belongs to.
 67 |     """
 68 |
 69 |     def __init__(
 70 |         self,
 71 |         code_toolbox: WorkspacePythonCodeToolbox,
 72 |         toolbox_api: ToolboxApi,
 73 |         instance: WorkspaceInstance,
 74 |     ):
 75 |         """Initialize a new Process instance.
 76 |
 77 |         Args:
 78 |             code_toolbox (WorkspacePythonCodeToolbox): Language-specific code execution toolbox.
 79 |             toolbox_api (ToolboxApi): API client for Sandbox operations.
 80 |             instance (WorkspaceInstance): The Sandbox instance this process belongs to.
 81 |         """
 82 |         self.code_toolbox = code_toolbox
 83 |         self.toolbox_api = toolbox_api
 84 |         self.instance = instance
 85 |
 86 |     @intercept_errors(message_prefix="Failed to execute command: ")
 87 |     def exec(self, command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> ExecuteResponse:
 88 |         """Execute a shell command in the Sandbox.
 89 |
 90 |         Args:
 91 |             command (str): Shell command to execute.
 92 |             cwd (Optional[str]): Working directory for command execution. If not
 93 |                 specified, uses the Sandbox root directory.
 94 |             timeout (Optional[int]): Maximum time in seconds to wait for the command
 95 |                 to complete. 0 means wait indefinitely.
 96 |
 97 |         Returns:
 98 |             ExecuteResponse: Command execution results containing:
 99 |                 - exit_code: The command's exit status
100 |                 - result: Standard output from the command
101 |
102 |         Example:
103 |             ```python
104 |             # Simple command
105 |             response = workspace.process.exec("echo 'Hello'")
106 |             print(response.result)  # Prints: Hello
107 |
108 |             # Command with working directory
109 |             result = workspace.process.exec("ls", cwd="/workspace/src")
110 |
111 |             # Command with timeout
112 |             result = workspace.process.exec("sleep 10", timeout=5)
113 |             ```
114 |         """
115 |         execute_request = ExecuteRequest(
116 |             command=command,
117 |             cwd=cwd,
118 |             timeout=timeout
119 |         )
120 |
121 |         return self.toolbox_api.execute_command(
122 |             workspace_id=self.instance.id,
123 |             execute_request=execute_request
124 |         )
125 |
126 |     def code_run(self, code: str, params: Optional[CodeRunParams] = None, timeout: Optional[int] = None) -> ExecuteResponse:
127 |         """Executes code in the Sandbox using the appropriate language runtime.
128 |
129 |         Args:
130 |             code (str): Code to execute.
131 |             params (Optional[CodeRunParams]): Parameters for code execution.
132 |             timeout (Optional[int]): Maximum time in seconds to wait for the code
133 |                 to complete. 0 means wait indefinitely.
134 |
135 |         Returns:
136 |             ExecuteResponse: Code execution result containing:
137 |                 - exit_code: The execution's exit status
138 |                 - result: Standard output from the code
139 |
140 |         Example:
141 |             ```python
142 |             # Run Python code
143 |             response = workspace.process.code_run('''
144 |                 x = 10
145 |                 y = 20
146 |                 print(f"Sum: {x + y}")
147 |             ''')
148 |             print(response.result)  # Prints: Sum: 30
149 |             ```
150 |         """
151 |         command = self.code_toolbox.get_run_command(code, params)
152 |         return self.exec(command, timeout=timeout)
153 |
154 |     @intercept_errors(message_prefix="Failed to create session: ")
155 |     def create_session(self, session_id: str) -> None:
156 |         """Create a new long-running background session in the Sandbox.
157 |
158 |         Sessions are background processes that maintain state between commands, making them ideal for
159 |         scenarios requiring multiple related commands or persistent environment setup. You can run
160 |         long-running commands and monitor process status.
161 |
162 |         Args:
163 |             session_id (str): Unique identifier for the new session.
164 |
165 |         Example:
166 |             ```python
167 |             # Create a new session
168 |             session_id = "my-session"
169 |             workspace.process.create_session(session_id)
170 |             session = workspace.process.get_session(session_id)
171 |             # Do work...
172 |             workspace.process.delete_session(session_id)
173 |             ```
174 |         """
175 |         request = CreateSessionRequest(sessionId=session_id)
176 |         self.toolbox_api.create_session(
177 |             workspace_id=self.instance.id,
178 |             create_session_request=request
179 |         )
180 |
181 |     @intercept_errors(message_prefix="Failed to get session: ")
182 |     def get_session(self, session_id: str) -> Session:
183 |         """Get a session in the Sandbox.
184 |
185 |         Args:
186 |             session_id (str): Unique identifier of the session to retrieve.
187 |
188 |         Returns:
189 |             Session: Session information including:
190 |                 - session_id: The session's unique identifier
191 |                 - commands: List of commands executed in the session
192 |
193 |         Example:
194 |             ```python
195 |             session = workspace.process.get_session("my-session")
196 |             for cmd in session.commands:
197 |                 print(f"Command: {cmd.command}")
198 |             ```
199 |         """
200 |         return self.toolbox_api.get_session(
201 |             workspace_id=self.instance.id,
202 |             session_id=session_id
203 |         )
204 |
205 |     @intercept_errors(message_prefix="Failed to get session command: ")
206 |     def get_session_command(self, session_id: str, command_id: str) -> Command:
207 |         """Get information about a specific command executed in a session.
208 |
209 |         Args:
210 |             session_id (str): Unique identifier of the session.
211 |             command_id (str): Unique identifier of the command.
212 |
213 |         Returns:
214 |             Command: Command information including:
215 |                 - id: The command's unique identifier
216 |                 - command: The executed command string
217 |                 - exit_code: Command's exit status (if completed)
218 |
219 |         Example:
220 |             ```python
221 |             cmd = workspace.process.get_session_command("my-session", "cmd-123")
222 |             if cmd.exit_code == 0:
223 |                 print(f"Command {cmd.command} completed successfully")
224 |             ```
225 |         """
226 |         return self.toolbox_api.get_session_command(
227 |             workspace_id=self.instance.id,
228 |             session_id=session_id,
229 |             command_id=command_id
230 |         )
231 |
232 |     @intercept_errors(message_prefix="Failed to execute session command: ")
233 |     def execute_session_command(self, session_id: str, req: SessionExecuteRequest, timeout: Optional[int] = None) -> SessionExecuteResponse:
234 |         """Executes a command in the session.
235 |
236 |         Args:
237 |             session_id (str): Unique identifier of the session to use.
238 |             req (SessionExecuteRequest): Command execution request containing:
239 |                 - command: The command to execute
240 |                 - var_async: Whether to execute asynchronously
241 |
242 |         Returns:
243 |             SessionExecuteResponse: Command execution results containing:
244 |                 - cmd_id: Unique identifier for the executed command
245 |                 - output: Command output (if synchronous execution)
246 |                 - exit_code: Command exit status (if synchronous execution)
247 |
248 |         Example:
249 |             ```python
250 |             # Execute commands in sequence, maintaining state
251 |             session_id = "my-session"
252 |
253 |             # Change directory
254 |             req = SessionExecuteRequest(command="cd /workspace")
255 |             workspace.process.execute_session_command(session_id, req)
256 |
257 |             # Create a file
258 |             req = SessionExecuteRequest(command="echo 'Hello' > test.txt")
259 |             workspace.process.execute_session_command(session_id, req)
260 |
261 |             # Read the file
262 |             req = SessionExecuteRequest(command="cat test.txt")
263 |             result = workspace.process.execute_session_command(session_id, req)
264 |             print(result.output)  # Prints: Hello
265 |             ```
266 |         """
267 |         return self.toolbox_api.execute_session_command(
268 |             workspace_id=self.instance.id,
269 |             session_id=session_id,
270 |             session_execute_request=req,
271 |             _request_timeout=timeout or None
272 |         )
273 |
274 |     @intercept_errors(message_prefix="Failed to get session command logs: ")
275 |     def get_session_command_logs(self, session_id: str, command_id: str) -> str:
276 |         """Get the logs for a command executed in a session.
277 |
278 |         This method retrieves the complete output (stdout and stderr) from a
279 |         command executed in a session. It's particularly useful for checking
280 |         the output of asynchronous commands.
281 |
282 |         Args:
283 |             session_id (str): Unique identifier of the session.
284 |             command_id (str): Unique identifier of the command.
285 |
286 |         Returns:
287 |             str: Complete command output including both stdout and stderr.
288 |
289 |         Example:
290 |             ```python
291 |             # Execute a long-running command asynchronously
292 |             req = SessionExecuteRequest(
293 |                 command="sleep 5; echo 'Done'",
294 |                 var_async=True
295 |             )
296 |             response = workspace.process.execute_session_command("my-session", req)
297 |
298 |             # Wait a bit, then get the logs
299 |             import time
300 |             time.sleep(6)
301 |             logs = workspace.process.get_session_command_logs(
302 |                 "my-session",
303 |                 response.command_id
304 |             )
305 |             print(logs)  # Prints: Done
306 |             ```
307 |         """
308 |         return self.toolbox_api.get_session_command_logs(
309 |             workspace_id=self.instance.id,
310 |             session_id=session_id,
311 |             command_id=command_id
312 |         )
313 |
314 |     @intercept_errors(message_prefix="Failed to list sessions: ")
315 |     def list_sessions(self) -> List[Session]:
316 |         """List all sessions in the Sandbox.
317 |
318 |         Returns:
319 |             List[Session]: List of all sessions in the Sandbox.
320 |
321 |         Example:
322 |             ```python
323 |             sessions = workspace.process.list_sessions()
324 |             for session in sessions:
325 |                 print(f"Session {session.session_id}:")
326 |                 print(f"  Commands: {len(session.commands)}")
327 |             ```
328 |         """
329 |         return self.toolbox_api.list_sessions(
330 |             workspace_id=self.instance.id
331 |         )
332 |
333 |     @intercept_errors(message_prefix="Failed to delete session: ")
334 |     def delete_session(self, session_id: str) -> None:
335 |         """Delete an interactive session from the Sandbox.
336 |
337 |         This method terminates and removes a session, cleaning up any resources
338 |         associated with it.
339 |
340 |         Args:
341 |             session_id (str): Unique identifier of the session to delete.
342 |
343 |         Example:
344 |             ```python
345 |             # Create and use a session
346 |             workspace.process.create_session("temp-session")
347 |             # ... use the session ...
348 |
349 |             # Clean up when done
350 |             workspace.process.delete_session("temp-session")
351 |             ```
352 |         """
353 |         self.toolbox_api.delete_session(
354 |             workspace_id=self.instance.id,
355 |             session_id=session_id
356 |         )
357 |


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/protocols.py:
--------------------------------------------------------------------------------
 1 | from typing import Protocol, Dict, Any
 2 |
 3 | class WorkspaceCodeToolbox(Protocol):
 4 |     def get_default_image(self) -> str: ...
 5 |     def get_code_run_command(self, code: str) -> str: ...
 6 |     def get_code_run_args(self) -> list[str]: ...
 7 |     # ... other protocol methods
 8 |
 9 | class WorkspaceInstance(Protocol):
10 |     id: str


--------------------------------------------------------------------------------
/packages/python/src/daytona_sdk/workspace.py:
--------------------------------------------------------------------------------
  1 | """
  2 | The Daytona SDK core Sandbox functionality.
  3 |
  4 | Provides the main Workspace class representing a Daytona Sandbox that coordinates file system,
  5 | Git, process execution, and LSP functionality. It serves as the central point
  6 | for interacting with Daytona Sandboxes.
  7 |
  8 | Example:
  9 |     Basic Sandbox operations:
 10 |     ```python
 11 |     from daytona_sdk import Daytona
 12 |     daytona = Daytona()
 13 |     workspace = daytona.create()
 14 |
 15 |     # File operations
 16 |     workspace.fs.upload_file("/workspace/test.txt", b"Hello, World!")
 17 |     content = workspace.fs.download_file("/workspace/test.txt")
 18 |
 19 |     # Git operations
 20 |     workspace.git.clone("https://github.com/user/repo.git")
 21 |
 22 |     # Process execution
 23 |     response = workspace.process.exec("ls -la")
 24 |     print(response.result)
 25 |
 26 |     # LSP functionality
 27 |     lsp = workspace.create_lsp_server("python", "/workspace/project")
 28 |     lsp.did_open("/workspace/project/src/index.ts")
 29 |     completions = lsp.completions("/workspace/project/src/index.ts", Position(line=10, character=15))
 30 |     print(completions)
 31 |     ```
 32 |
 33 | Note:
 34 |     The Sandbox must be in a 'started' state before performing operations.
 35 | """
 36 |
 37 | import json
 38 | import time
 39 | from typing import Dict, Optional
 40 | from daytona_sdk._utils.errors import intercept_errors
 41 | from .filesystem import FileSystem
 42 | from .git import Git
 43 | from .process import Process
 44 | from .lsp_server import LspServer, LspLanguageId
 45 | from daytona_api_client import Workspace as ApiWorkspace, ToolboxApi, WorkspaceApi, WorkspaceInfo as ApiWorkspaceInfo
 46 | from .protocols import WorkspaceCodeToolbox
 47 | from dataclasses import dataclass
 48 | from datetime import datetime
 49 | from daytona_sdk._utils.errors import DaytonaError
 50 | from enum import Enum
 51 | from pydantic import Field
 52 | from typing_extensions import Annotated
 53 | from ._utils.enum import to_enum
 54 | from ._utils.timeout import with_timeout
 55 |
 56 |
 57 | @dataclass
 58 | class WorkspaceTargetRegion(Enum):
 59 |     """Target regions for workspaces"""
 60 |     EU = "eu"
 61 |     US = "us"
 62 |     ASIA = "asia"
 63 |
 64 |     def __str__(self):
 65 |         return self.value
 66 |
 67 |     def __eq__(self, other):
 68 |         if isinstance(other, str):
 69 |             return self.value == other
 70 |         return super().__eq__(other)
 71 |
 72 |
 73 | @dataclass
 74 | class WorkspaceResources:
 75 |     """Resources allocated to a Sandbox.
 76 |
 77 |     Attributes:
 78 |         cpu (str): Number of CPU cores allocated (e.g., "1", "2").
 79 |         gpu (Optional[str]): Number of GPUs allocated (e.g., "1") or None if no GPU.
 80 |         memory (str): Amount of memory allocated with unit (e.g., "2Gi", "4Gi").
 81 |         disk (str): Amount of disk space allocated with unit (e.g., "10Gi", "20Gi").
 82 |
 83 |     Example:
 84 |         ```python
 85 |         resources = WorkspaceResources(
 86 |             cpu="2",
 87 |             gpu="1",
 88 |             memory="4Gi",
 89 |             disk="20Gi"
 90 |         )
 91 |         ```
 92 |     """
 93 |     cpu: str
 94 |     gpu: Optional[str]
 95 |     memory: str
 96 |     disk: str
 97 |
 98 |
 99 | @dataclass
100 | class WorkspaceState(Enum):
101 |     """States of a Sandbox."""
102 |     CREATING = "creating"
103 |     RESTORING = "restoring"
104 |     DESTROYED = "destroyed"
105 |     DESTROYING = "destroying"
106 |     STARTED = "started"
107 |     STOPPED = "stopped"
108 |     STARTING = "starting"
109 |     STOPPING = "stopping"
110 |     RESIZING = "resizing"
111 |     ERROR = "error"
112 |     UNKNOWN = "unknown"
113 |     PULLING_IMAGE = "pulling_image"
114 |
115 |     def __str__(self):
116 |         return self.value
117 |
118 |     def __eq__(self, other):
119 |         if isinstance(other, str):
120 |             return self.value == other
121 |         return super().__eq__(other)
122 |
123 |
124 | class WorkspaceInfo(ApiWorkspaceInfo):
125 |     """Structured information about a Sandbox.
126 |
127 |     This class provides detailed information about a Sandbox's configuration,
128 |     resources, and current state.
129 |
130 |     Attributes:
131 |         id (str): Unique identifier for the Sandbox.
132 |         name (str): Display name of the Sandbox.
133 |         image (str): Docker image used for the Sandbox.
134 |         user (str): OS user running in the Sandbox.
135 |         env (Dict[str, str]): Environment variables set in the Sandbox.
136 |         labels (Dict[str, str]): Custom labels attached to the Sandbox.
137 |         public (bool): Whether the Sandbox is publicly accessible.
138 |         target (str): Target environment where the Sandbox runs.
139 |         resources (WorkspaceResources): Resource allocations for the Sandbox.
140 |         state (str): Current state of the Sandbox (e.g., "started", "stopped").
141 |         error_reason (Optional[str]): Error message if Sandbox is in error state.
142 |         snapshot_state (Optional[str]): Current state of Sandbox snapshot.
143 |         snapshot_state_created_at (Optional[datetime]): When the snapshot state was created.
144 |
145 |     Example:
146 |         ```python
147 |         workspace = daytona.create()
148 |         info = workspace.info()
149 |         print(f"Workspace {info.name} is {info.state}")
150 |         print(f"Resources: {info.resources.cpu} CPU, {info.resources.memory} RAM")
151 |         ```
152 |     """
153 |     id: str
154 |     name: str
155 |     image: str
156 |     user: str
157 |     env: Dict[str, str]
158 |     labels: Dict[str, str]
159 |     public: bool
160 |     target: WorkspaceTargetRegion
161 |     resources: WorkspaceResources
162 |     state: WorkspaceState
163 |     error_reason: Optional[str]
164 |     snapshot_state: Optional[str]
165 |     snapshot_state_created_at: Optional[datetime]
166 |     node_domain: str
167 |     region: str
168 |     class_name: str
169 |     updated_at: str
170 |     last_snapshot: Optional[str]
171 |     auto_stop_interval: int
172 |     provider_metadata: Annotated[Optional[str], Field(
173 |         deprecated='The `provider_metadata` field is deprecated. Use `state`, `node_domain`, `region`, `class_name`, `updated_at`, `last_snapshot`, `resources`, `auto_stop_interval` instead.')]
174 |
175 |
176 | class WorkspaceInstance(ApiWorkspace):
177 |     """Represents a Daytona workspace instance."""
178 |     info: Optional[WorkspaceInfo]
179 |
180 |
181 | class Workspace:
182 |     """Represents a Daytona Sandbox.
183 |
184 |     A Sandbox provides file system operations, Git operations, process execution,
185 |     and LSP functionality. It serves as the main interface for interacting with
186 |     a Daytona Sandbox.
187 |
188 |     Attributes:
189 |         id (str): Unique identifier for the Sandbox.
190 |         instance (WorkspaceInstance): The underlying Sandbox instance.
191 |         code_toolbox (WorkspaceCodeToolbox): Language-specific toolbox implementation.
192 |         fs (FileSystem): File system operations interface.
193 |         git (Git): Git operations interface.
194 |         process (Process): Process execution interface.
195 |     """
196 |
197 |     def __init__(
198 |         self,
199 |         id: str,
200 |         instance: WorkspaceInstance,
201 |         workspace_api: WorkspaceApi,
202 |         toolbox_api: ToolboxApi,
203 |         code_toolbox: WorkspaceCodeToolbox,
204 |     ):
205 |         """Initialize a new Workspace instance.
206 |
207 |         Args:
208 |             id (str): Unique identifier for the Sandbox.
209 |             instance (WorkspaceInstance): The underlying Sandbox instance.
210 |             workspace_api (WorkspaceApi): API client for Sandbox operations.
211 |             toolbox_api (ToolboxApi): API client for toolbox operations.
212 |             code_toolbox (WorkspaceCodeToolbox): Language-specific toolbox implementation.
213 |         """
214 |         self.id = id
215 |         self.instance = instance
216 |         self.workspace_api = workspace_api
217 |         self.toolbox_api = toolbox_api
218 |         self.code_toolbox = code_toolbox
219 |
220 |         # Initialize components
221 |         # File system operations
222 |         self.fs = FileSystem(instance, self.toolbox_api)
223 |         self.git = Git(self, self.toolbox_api, instance)  # Git operations
224 |         self.process = Process(
225 |             self.code_toolbox, self.toolbox_api, instance)  # Process execution
226 |
227 |     def info(self) -> WorkspaceInfo:
228 |         """Gets structured information about the Sandbox.
229 |
230 |         Returns:
231 |             WorkspaceInfo: Detailed information about the Sandbox including its
232 |                 configuration, resources, and current state.
233 |
234 |         Example:
235 |             ```python
236 |             info = workspace.info()
237 |             print(f"Workspace {info.name}:")
238 |             print(f"State: {info.state}")
239 |             print(f"Resources: {info.resources.cpu} CPU, {info.resources.memory} RAM")
240 |             ```
241 |         """
242 |         instance = self.workspace_api.get_workspace(self.id)
243 |         return Workspace._to_workspace_info(instance)
244 |
245 |     @intercept_errors(message_prefix="Failed to get workspace root directory: ")
246 |     def get_workspace_root_dir(self) -> str:
247 |         """Gets the root directory path of the Sandbox.
248 |
249 |         Returns:
250 |             str: The absolute path to the Sandbox root directory.
251 |
252 |         Example:
253 |             ```python
254 |             root_dir = workspace.get_workspace_root_dir()
255 |             print(f"Workspace root: {root_dir}")
256 |             ```
257 |         """
258 |         response = self.toolbox_api.get_project_dir(
259 |             workspace_id=self.instance.id
260 |         )
261 |         return response.dir
262 |
263 |     def create_lsp_server(
264 |         self, language_id: LspLanguageId, path_to_project: str
265 |     ) -> LspServer:
266 |         """Creates a new Language Server Protocol (LSP) server instance.
267 |
268 |         The LSP server provides language-specific features like code completion,
269 |         diagnostics, and more.
270 |
271 |         Args:
272 |             language_id (LspLanguageId): The language server type (e.g., LspLanguageId.PYTHON).
273 |             path_to_project (str): Absolute path to the project root directory.
274 |
275 |         Returns:
276 |             LspServer: A new LSP server instance configured for the specified language.
277 |
278 |         Example:
279 |             ```python
280 |             lsp = workspace.create_lsp_server("python", "/workspace/project")
281 |             ```
282 |         """
283 |         return LspServer(language_id, path_to_project, self.toolbox_api, self.instance)
284 |
285 |     @intercept_errors(message_prefix="Failed to set labels: ")
286 |     def set_labels(self, labels: Dict[str, str]) -> Dict[str, str]:
287 |         """Sets labels for the Sandbox.
288 |
289 |         Labels are key-value pairs that can be used to organize and identify Sandboxes.
290 |
291 |         Args:
292 |             labels (Dict[str, str]): Dictionary of key-value pairs representing Sandbox labels.
293 |
294 |         Returns:
295 |             Dict[str, str]: Dictionary containing the updated Sandbox labels.
296 |
297 |         Example:
298 |             ```python
299 |             new_labels = workspace.set_labels({
300 |                 "project": "my-project",
301 |                 "environment": "development",
302 |                 "team": "backend"
303 |             })
304 |             print(f"Updated labels: {new_labels}")
305 |             ```
306 |         """
307 |         # Convert all values to strings and create the expected labels structure
308 |         string_labels = {k: str(v).lower() if isinstance(
309 |             v, bool) else str(v) for k, v in labels.items()}
310 |         labels_payload = {"labels": string_labels}
311 |         return self.workspace_api.replace_labels(self.id, labels_payload)
312 |
313 |     @intercept_errors(message_prefix="Failed to start workspace: ")
314 |     @with_timeout(error_message=lambda self, timeout: f"Workspace {self.id} failed to start within the {timeout} seconds timeout period")
315 |     def start(self, timeout: Optional[float] = 60):
316 |         """Starts the Sandbox.
317 |
318 |         This method starts the Sandbox and waits for it to be ready.
319 |
320 |         Args:
321 |             timeout (Optional[float]): Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
322 |
323 |         Raises:
324 |             DaytonaError: If timeout is negative. If workspace fails to start or times out.
325 |
326 |         Example:
327 |             ```python
328 |             workspace = daytona.get_current_workspace("my-workspace")
329 |             workspace.start(timeout=40)  # Wait up to 40 seconds
330 |             print("Workspace started successfully")
331 |             ```
332 |         """
333 |         self.workspace_api.start_workspace(self.id, _request_timeout=timeout or None)
334 |         self.wait_for_workspace_start()
335 |
336 |     @intercept_errors(message_prefix="Failed to stop workspace: ")
337 |     @with_timeout(error_message=lambda self, timeout: f"Workspace {self.id} failed to stop within the {timeout} seconds timeout period")
338 |     def stop(self, timeout: Optional[float] = 60):
339 |         """Stops the Sandbox.
340 |
341 |         This method stops the Sandbox and waits for it to be fully stopped.
342 |
343 |         Args:
344 |             timeout (Optional[float]): Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
345 |
346 |         Raises:
347 |             DaytonaError: If timeout is negative; If workspace fails to stop or times out
348 |
349 |         Example:
350 |             ```python
351 |             workspace = daytona.get_current_workspace("my-workspace")
352 |             workspace.stop()
353 |             print("Workspace stopped successfully")
354 |             ```
355 |         """
356 |         self.workspace_api.stop_workspace(self.id, _request_timeout=timeout or None)
357 |         self.wait_for_workspace_stop()
358 |
359 |     @intercept_errors(message_prefix="Failure during waiting for workspace to start: ")
360 |     @with_timeout(error_message=lambda self, timeout: f"Workspace {self.id} failed to become ready within the {timeout} seconds timeout period")
361 |     def wait_for_workspace_start(self, timeout: Optional[float] = 60) -> None:
362 |         """Waits for the Sandbox to reach the 'started' state.
363 |
364 |         This method polls the Sandbox status until it reaches the 'started' state
365 |         or encounters an error.
366 |
367 |         Args:
368 |             timeout (Optional[float]): Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
369 |
370 |         Raises:
371 |             DaytonaError: If timeout is negative; If workspace fails to start or times out
372 |         """
373 |         state = None
374 |         while state != "started":
375 |             response = self.workspace_api.get_workspace(self.id)
376 |             provider_metadata = json.loads(response.info.provider_metadata)
377 |             state = provider_metadata.get('state', '')
378 |
379 |             if state == "error":
380 |                 raise DaytonaError(
381 |                     f"Workspace {self.id} failed to start with state: {state}, error reason: {response.error_reason}")
382 |
383 |             time.sleep(0.1)  # Wait 100ms between checks
384 |
385 |     @intercept_errors(message_prefix="Failure during waiting for workspace to stop: ")
386 |     @with_timeout(error_message=lambda self, timeout: f"Workspace {self.id} failed to become stopped within the {timeout} seconds timeout period")
387 |     def wait_for_workspace_stop(self, timeout: Optional[float] = 60) -> None:
388 |         """Waits for the Sandbox to reach the 'stopped' state.
389 |
390 |         This method polls the Sandbox status until it reaches the 'stopped' state
391 |         or encounters an error. It will wait up to 60 seconds for the Sandbox to stop.
392 |
393 |         Args:
394 |             timeout (Optional[float]): Maximum time to wait in seconds. 0 means no timeout. Default is 60 seconds.
395 |
396 |         Raises:
397 |             DaytonaError: If timeout is negative. If Sandbox fails to stop or times out.
398 |         """
399 |         state = None
400 |         while state != "stopped":
401 |             try:
402 |                 workspace_check = self.workspace_api.get_workspace(self.id)
403 |                 provider_metadata = json.loads(
404 |                     workspace_check.info.provider_metadata)
405 |                 state = provider_metadata.get('state')
406 |
407 |                 if state == "error":
408 |                     raise DaytonaError(
409 |                         f"Workspace {self.id} failed to stop with status: {state}, error reason: {workspace_check.error_reason}")
410 |             except Exception as e:
411 |                 # If there's a validation error, continue waiting
412 |                 if "validation error" not in str(e):
413 |                     raise e
414 |
415 |             time.sleep(0.1)  # Wait 100ms between checks
416 |
417 |     @intercept_errors(message_prefix="Failed to set auto-stop interval: ")
418 |     def set_autostop_interval(self, interval: int) -> None:
419 |         """Sets the auto-stop interval for the Sandbox.
420 |
421 |         The Sandbox will automatically stop after being idle (no new events) for the specified interval.
422 |         Events include any state changes or interactions with the Sandbox through the SDK.
423 |         Interactions using Sandbox Previews are not included.
424 |
425 |         Args:
426 |             interval (int): Number of minutes of inactivity before auto-stopping.
427 |                 Set to 0 to disable auto-stop. Defaults to 15.
428 |
429 |         Raises:
430 |             DaytonaError: If interval is negative
431 |
432 |         Example:
433 |             ```python
434 |             # Auto-stop after 1 hour
435 |             workspace.set_autostop_interval(60)
436 |             # Or disable auto-stop
437 |             workspace.set_autostop_interval(0)
438 |             ```
439 |         """
440 |         if not isinstance(interval, int) or interval < 0:
441 |             raise DaytonaError(
442 |                 "Auto-stop interval must be a non-negative integer")
443 |
444 |         self.workspace_api.set_autostop_interval(self.id, interval)
445 |         self.instance.auto_stop_interval = interval
446 |
447 |     @intercept_errors(message_prefix="Failed to get preview link: ")
448 |     def get_preview_link(self, port: int) -> str:
449 |         """Gets the preview link for the workspace at a specific port. If the port is not open, it will open it and return the link.
450 |
451 |         Args:
452 |             port (int): The port to open the preview link on
453 |
454 |         Returns:
455 |             The preview link for the workspace at the specified port
456 |         """
457 |         provider_metadata = json.loads(self.instance.info.provider_metadata)
458 |         node_domain = provider_metadata.get('nodeDomain', '')
459 |         if not node_domain:
460 |             raise DaytonaError(
461 |                 "Node domain not found in provider metadata. Please contact support.")
462 |
463 |         return f"https://{port}-{self.id}.{node_domain}"
464 |
465 |     @intercept_errors(message_prefix="Failed to archive workspace: ")
466 |     def archive(self) -> None:
467 |         """Archives the workspace, making it inactive and preserving its state. When sandboxes are archived, the entire filesystem
468 |         state is moved to cost-effective object storage, making it possible to keep sandboxes available for an extended period.
469 |         The tradeoff between archived and stopped states is that starting an archived sandbox takes more time, depending on its size.
470 |         Workspace must be stopped before archiving.
471 |         """
472 |         self.workspace_api.archive_workspace(self.id)
473 |
474 |     @staticmethod
475 |     def _to_workspace_info(instance: ApiWorkspace) -> WorkspaceInfo:
476 |         """Converts an API workspace instance to a WorkspaceInfo object.
477 |
478 |         Args:
479 |             instance (ApiWorkspace): The API workspace instance to convert
480 |
481 |         Returns:
482 |             WorkspaceInfo: The converted WorkspaceInfo object
483 |         """
484 |         provider_metadata = json.loads(instance.info.provider_metadata or '{}')
485 |         resources_data = provider_metadata.get('resources', provider_metadata)
486 |
487 |         # Extract resources with defaults
488 |         resources = WorkspaceResources(
489 |             cpu=str(resources_data.get('cpu', '1')),
490 |             gpu=str(resources_data.get('gpu')
491 |                     ) if resources_data.get('gpu') else None,
492 |             memory=str(resources_data.get('memory', '2')) + 'Gi',
493 |             disk=str(resources_data.get('disk', '10')) + 'Gi'
494 |         )
495 |
496 |         enum_state = to_enum(
497 |             WorkspaceState, provider_metadata.get('state', ''))
498 |         enum_target = to_enum(WorkspaceTargetRegion, instance.target)
499 |
500 |         return WorkspaceInfo(
501 |             id=instance.id,
502 |             name=instance.name,
503 |             image=instance.image,
504 |             user=instance.user,
505 |             env=instance.env or {},
506 |             labels=instance.labels or {},
507 |             public=instance.public,
508 |             target=enum_target or instance.target,
509 |             resources=resources,
510 |             state=enum_state or provider_metadata.get('state', ''),
511 |             error_reason=instance.error_reason,
512 |             snapshot_state=provider_metadata.get('snapshotState'),
513 |             snapshot_state_created_at=datetime.fromisoformat(provider_metadata.get(
514 |                 'snapshotStateCreatedAt')) if provider_metadata.get('snapshotStateCreatedAt') else None,
515 |             node_domain=provider_metadata.get('nodeDomain', ''),
516 |             region=provider_metadata.get('region', ''),
517 |             class_name=provider_metadata.get('class', ''),
518 |             updated_at=provider_metadata.get('updatedAt', ''),
519 |             last_snapshot=provider_metadata.get('lastSnapshot'),
520 |             auto_stop_interval=provider_metadata.get('autoStopInterval', 0),
521 |             created=instance.info.created or '',
522 |             provider_metadata=instance.info.provider_metadata,
523 |         )
524 |


--------------------------------------------------------------------------------