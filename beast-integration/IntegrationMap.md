=== AGENT INTEGRATION MAP ===

📁 AGENT_PATTERNS
   Source: agent-patterns/autogen-agentchat/src/autogen_agentchat/
   Extract to: unified/agents/
   Key files:
     • agents/assistant_agent.py
     • agents/chat_completion_client.py
     • teams/_group_chat/group_chat.py
     • base/_chat_agent.py
     • messages/_message.py
   Patterns to extract:
     - Agent conversation patterns
     - Multi-agent handoff logic
     - Message routing and handling
     - LLM integration patterns

📁 AGENT_CORE
   Source: agent-patterns/autogen-core/src/autogen_core/
   Extract to: unified/core/
   Key files:
     • _agent_runtime.py
     • _agent_proxy.py
     • _routed_agent.py
     • _agent_type.py
     • tool_agent/
   Patterns to extract:
     - Agent runtime management
     - Inter-agent communication
     - Tool integration framework
     - Agent type definitions

📁 ROLE_SYSTEM
   Source: role-system/
   Extract to: unified/roles/
   Key files:
     • agent.py
     • crew.py
     • task.py
     • agents/cache_handler.py
     • tools/
   Patterns to extract:
     - Role definition and capabilities
     - Task delegation system
     - Team coordination logic
     - Skill-based agent matching

📁 STATE_MACHINE
   Source: state-machine/langgraph/
   Extract to: unified/workflows/
   Key files:
     • graph/graph.py
     • pregel/
     • channels/
     • runtime.py
     • types.py
   Patterns to extract:
     - State machine implementation
     - Conditional workflow routing
     - Node/edge graph definitions
     - Workflow execution engine

📁 MEMORY
   Source: memory/chromadb/
   Extract to: unified/memory/
   Key files:
     • api/client.py
     • api/models/
     • utils/embedding_functions.py
     • db/
     • segment/
   Patterns to extract:
     - Vector similarity search
     - Embedding storage/retrieval
     - Collection management
     - Memory segmentation

📁 EXECUTION_INTERPRETER
   Source: execution/interpreter/
   Extract to: unified/tools/interpreter/
   Key files:
     • core/
     • computer/
     • terminal/
   Patterns to extract:
     - Code execution sandboxing
     - Language detection/parsing
     - Output capture/error handling
     - System integration

📁 EXECUTION_BROWSER
   Source: execution/browser/
   Extract to: unified/tools/browser/
   Key files:
     • server/
     • page/
     • locator/
     • screenshot/
   Patterns to extract:
     - Page interaction primitives
     - Element selection strategies
     - Screenshot/content extraction
     - Browser automation

=== UNIFIED ARCHITECTURE TARGET ===

🎯 unified/core/
   Core agent runtime and communication
   Key classes to implement:
     • AgentRuntime
     • AgentProxy
     • MessageRouter
     • ToolFramework

🎯 unified/agents/
   Agent implementations and patterns
   Key classes to implement:
     • BaseAgent
     • ConversationAgent
     • GroupChatManager
     • RoleAgent
     • SkillMatcher

🎯 unified/roles/
   Role-based system and team coordination
   Key classes to implement:
     • Role
     • Crew
     • TaskManager
     • TeamCoordinator

🎯 unified/workflows/
   State machines and workflow orchestration
   Key classes to implement:
     • WorkflowGraph
     • StateManager
     • ConditionalRouter
     • ExecutionEngine

🎯 unified/memory/
   Memory management and retrieval
   Key classes to implement:
     • VectorStore
     • EmbeddingEngine
     • MemoryManager
     • ConversationHistory

🎯 unified/tools/
   Tool execution and integration
   Key classes to implement:
     • CodeExecutor
     • BrowserController
     • ToolRegistry
     • ExecutionSandbox

=== EXTRACTION PRIORITY ORDER ===
1. agent_core
2. state_machine
3. agent_patterns
4. role_system
5. memory
6. execution_interpreter
7. execution_browser

# YOU ARE HERE #
LIBR8/beast-integration$  ls -R
.:
agent-patterns  integration-map.py  role-system    unified
execution       memory              state-machine

./agent-patterns:
autogen-agentchat  autogen-core

./agent-patterns/autogen-agentchat:
src

./agent-patterns/autogen-agentchat/src:
autogen_agentchat

./agent-patterns/autogen-agentchat/src/autogen_agentchat:
__init__.py  base        messages.py  state  tools  utils
agents       conditions  py.typed     teams  ui

./agent-patterns/autogen-agentchat/src/autogen_agentchat/agents:
__init__.py          _code_executor_agent.py    _user_proxy_agent.py
_assistant_agent.py  _message_filter_agent.py
_base_chat_agent.py  _society_of_mind_agent.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/base:
__init__.py     _handoff.py  _team.py
_chat_agent.py  _task.py     _termination.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/conditions:
__init__.py  _terminations.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/state:
__init__.py  _states.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/teams:
__init__.py  _group_chat

./agent-patterns/autogen-agentchat/src/autogen_agentchat/teams/_group_chat:
__init__.py                  _magentic_one
_base_group_chat.py          _round_robin_group_chat.py
_base_group_chat_manager.py  _selector_group_chat.py
_chat_agent_container.py     _sequential_routed_agent.py
_events.py                   _swarm_group_chat.py
_graph

./agent-patterns/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_graph:
__init__.py  _digraph_group_chat.py  _graph_builder.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_magentic_one:
__init__.py                  _magentic_one_orchestrator.py
_magentic_one_group_chat.py  _prompts.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/tools:
__init__.py  _agent.py  _task_runner_tool.py  _team.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/ui:
__init__.py  _console.py

./agent-patterns/autogen-agentchat/src/autogen_agentchat/utils:
__init__.py  _utils.py

./agent-patterns/autogen-core:
src

./agent-patterns/autogen-core/src:
autogen_core

./agent-patterns/autogen-core/src/autogen_core:
__init__.py                  _routed_agent.py
_agent.py                    _runtime_impl_helpers.py
_agent_id.py                 _serialization.py
_agent_instantiation.py      _single_threaded_agent_runtime.py
_agent_metadata.py           _subscription.py
_agent_proxy.py              _subscription_context.py
_agent_runtime.py            _telemetry
_agent_type.py               _topic.py
_base_agent.py               _type_helpers.py
_cache_store.py              _type_prefix_subscription.py
_cancellation_token.py       _type_subscription.py
_closure_agent.py            _types.py
_component_config.py         code_executor
_constants.py                exceptions.py
_default_subscription.py     logging.py
_default_topic.py            memory
_function_utils.py           model_context
_image.py                    models
_intervention.py             py.typed
_message_context.py          tool_agent
_message_handler_context.py  tools
_queue.py                    utils

./agent-patterns/autogen-core/src/autogen_core/_telemetry:
__init__.py    _genai.py        _tracing.py
_constants.py  _propagation.py  _tracing_config.py

./agent-patterns/autogen-core/src/autogen_core/code_executor:
__init__.py  _base.py  _func_with_reqs.py

./agent-patterns/autogen-core/src/autogen_core/memory:
__init__.py  _base_memory.py  _list_memory.py

./agent-patterns/autogen-core/src/autogen_core/model_context:
__init__.py
_buffered_chat_completion_context.py
_chat_completion_context.py
_head_and_tail_chat_completion_context.py
_token_limited_chat_completion_context.py
_unbounded_chat_completion_context.py

./agent-patterns/autogen-core/src/autogen_core/models:
__init__.py  _model_client.py  _types.py

./agent-patterns/autogen-core/src/autogen_core/tool_agent:
__init__.py  _caller_loop.py  _tool_agent.py

./agent-patterns/autogen-core/src/autogen_core/tools:
__init__.py  _function_tool.py     _workbench.py
_base.py     _static_workbench.py

./agent-patterns/autogen-core/src/autogen_core/utils:
__init__.py  _json_to_pydantic.py  _load_json.py

./execution:
browser  interpreter

./execution/browser:
DEPS.list             inProcessFactory.ts  third_party
androidServerImpl.ts  inprocess.ts         utils
browserServerImpl.ts  outofprocess.ts      utils.ts
cli                   protocol             utilsBundle.ts
client                remote               zipBundle.ts
common                server

./execution/browser/cli:
DEPS.list  driver.ts  program.ts  programWithTestStub.ts

./execution/browser/client:
DEPS.list                 dialog.ts         network.ts
accessibility.ts          download.ts       page.ts
android.ts                electron.ts       platform.ts
api.ts                    elementHandle.ts  playwright.ts
artifact.ts               errors.ts         selectors.ts
browser.ts                eventEmitter.ts   stream.ts
browserContext.ts         events.ts         timeoutSettings.ts
browserType.ts            fetch.ts          tracing.ts
cdpSession.ts             fileChooser.ts    types.ts
channelOwner.ts           fileUtils.ts      video.ts
clientHelper.ts           frame.ts          waiter.ts
clientInstrumentation.ts  harRouter.ts      webError.ts
clientStackTrace.ts       input.ts          webSocket.ts
clock.ts                  jsHandle.ts       worker.ts
connection.ts             jsonPipe.ts       writableStream.ts
consoleMessage.ts         localUtils.ts
coverage.ts               locator.ts

./execution/browser/common:
DEPS.list

./execution/browser/protocol:
DEPS.list  serializers.ts  validator.ts  validatorPrimitives.ts

./execution/browser/remote:
DEPS.list  playwrightConnection.ts  playwrightServer.ts

./execution/browser/server:
DEPS.list                     frames.ts
accessibility.ts              har
android                       harBackend.ts
artifact.ts                   helper.ts
bidi                          index.ts
browser.ts                    input.ts
browserContext.ts             instrumentation.ts
browserType.ts                javascript.ts
callLog.ts                    launchApp.ts
chromium                      localUtils.ts
clock.ts                      macEditingCommands.ts
codegen                       network.ts
console.ts                    page.ts
cookieStore.ts                pipeTransport.ts
debugController.ts            playwright.ts
debugger.ts                   progress.ts
deviceDescriptors.ts          protocolError.ts
deviceDescriptorsSource.json  recorder
dialog.ts                     recorder.ts
dispatchers                   registry
dom.ts                        screenshotter.ts
download.ts                   selectors.ts
electron                      socksClientCertificatesInterceptor.ts
errors.ts                     socksInterceptor.ts
fetch.ts                      trace
fileChooser.ts                transport.ts
fileUploadUtils.ts            types.ts
firefox                       usKeyboardLayout.ts
formData.ts                   utils
frameSelectors.ts             webkit

./execution/browser/server/android:
DEPS.list  android.ts  backendAdb.ts  driver

./execution/browser/server/android/driver:
app           gradle             gradlew      settings.gradle
build.gradle  gradle.properties  gradlew.bat

./execution/browser/server/android/driver/app:
build.gradle  proguard-rules.pro  src

./execution/browser/server/android/driver/app/src:
androidTest  main

./execution/browser/server/android/driver/app/src/androidTest:
java

./execution/browser/server/android/driver/app/src/androidTest/java:
com

./execution/browser/server/android/driver/app/src/androidTest/java/com:
microsoft

./execution/browser/server/android/driver/app/src/androidTest/java/com/microsoft:
playwright

./execution/browser/server/android/driver/app/src/androidTest/java/com/microsoft/playwright:
androiddriver

./execution/browser/server/android/driver/app/src/androidTest/java/com/microsoft/playwright/androiddriver:
InstrumentedTest.java

./execution/browser/server/android/driver/app/src/main:
AndroidManifest.xml  res

./execution/browser/server/android/driver/app/src/main/res:
drawable  drawable-v24  mipmap-anydpi-v26

./execution/browser/server/android/driver/app/src/main/res/drawable:
ic_launcher_background.xml

./execution/browser/server/android/driver/app/src/main/res/drawable-v24:
ic_launcher_foreground.xml

./execution/browser/server/android/driver/app/src/main/res/mipmap-anydpi-v26:
ic_launcher.xml  ic_launcher_round.xml

./execution/browser/server/android/driver/gradle:
wrapper

./execution/browser/server/android/driver/gradle/wrapper:
gradle-wrapper.jar  gradle-wrapper.properties

./execution/browser/server/bidi:
DEPS.list          bidiExecutionContext.ts  bidiOverCdp.ts
bidiBrowser.ts     bidiFirefox.ts           bidiPage.ts
bidiChromium.ts    bidiInput.ts             bidiPdf.ts
bidiConnection.ts  bidiNetworkManager.ts    third_party

./execution/browser/server/bidi/third_party:
bidiCommands.d.ts    bidiProtocol.ts             bidiSerializer.ts
bidiDeserializer.ts  bidiProtocolCore.ts         firefoxPrefs.ts
bidiKeyboard.ts      bidiProtocolPermissions.ts

./execution/browser/server/chromium:
appIcon.png          crDevTools.ts          crProtocolHelper.ts
chromium.ts          crDragDrop.ts          crServiceWorker.ts
chromiumSwitches.ts  crExecutionContext.ts  defaultFontFamilies.ts
crAccessibility.ts   crInput.ts             protocol.d.ts
crBrowser.ts         crNetworkManager.ts    videoRecorder.ts
crConnection.ts      crPage.ts
crCoverage.ts        crPdf.ts

./execution/browser/server/codegen:
DEPS.list  java.ts        jsonl.ts     languages.ts  types.ts
csharp.ts  javascript.ts  language.ts  python.ts

./execution/browser/server/dispatchers:
DEPS.list                     frameDispatcher.ts
androidDispatcher.ts          jsHandleDispatcher.ts
artifactDispatcher.ts         jsonPipeDispatcher.ts
browserContextDispatcher.ts   localUtilsDispatcher.ts
browserDispatcher.ts          networkDispatchers.ts
browserTypeDispatcher.ts      pageDispatcher.ts
cdpSessionDispatcher.ts       playwrightDispatcher.ts
debugControllerDispatcher.ts  streamDispatcher.ts
dialogDispatcher.ts           tracingDispatcher.ts
dispatcher.ts                 webSocketRouteDispatcher.ts
electronDispatcher.ts         writableStreamDispatcher.ts
elementHandlerDispatcher.ts

./execution/browser/server/electron:
DEPS.list  electron.ts  loader.ts

./execution/browser/server/firefox:
ffAccessibility.ts  ffExecutionContext.ts  ffPage.ts
ffBrowser.ts        ffInput.ts             firefox.ts
ffConnection.ts     ffNetworkManager.ts    protocol.d.ts

./execution/browser/server/har:
harRecorder.ts  harTracer.ts

./execution/browser/server/recorder:
DEPS.list       recorderRunner.ts           throttledFile.ts
chat.ts         recorderSignalProcessor.ts
recorderApp.ts  recorderUtils.ts

./execution/browser/server/registry:
browserFetcher.ts  index.ts       oopDownloadBrowserMain.ts
dependencies.ts    nativeDeps.ts

./execution/browser/server/trace:
recorder  viewer

./execution/browser/server/trace/recorder:
DEPS.list  snapshotter.ts  snapshotterInjected.ts  tracing.ts

./execution/browser/server/trace/viewer:
DEPS.list  traceViewer.ts

./execution/browser/server/utils:
DEPS.list       eventsHelper.ts   linuxUtils.ts       spawnAsync.ts
ascii.ts        expectUtils.ts    network.ts          task.ts
comparators.ts  fileUtils.ts      nodePlatform.ts     userAgent.ts
crypto.ts       happyEyeballs.ts  pipeTransport.ts    wsServer.ts
debug.ts        hostPlatform.ts   processLauncher.ts  zipFile.ts
debugLogger.ts  httpServer.ts     profiler.ts         zones.ts
env.ts          image_tools       socksProxy.ts

./execution/browser/server/utils/image_tools:
colorUtils.ts  compare.ts  imageChannel.ts  stats.ts

./execution/browser/server/webkit:
protocol.d.ts       wkConnection.ts            wkPage.ts
webkit.ts           wkExecutionContext.ts      wkProvisionalPage.ts
wkAccessibility.ts  wkInput.ts                 wkWorkers.ts
wkBrowser.ts        wkInterceptableRequest.ts

./execution/browser/third_party:
pixelmatch.js

./execution/browser/utils:
isomorphic

./execution/browser/utils/isomorphic:
DEPS.list             protocolFormatter.ts
ariaSnapshot.ts       protocolMetainfo.ts
assert.ts             rtti.ts
colors.ts             selectorParser.ts
cssParser.ts          semaphore.ts
cssTokenizer.ts       stackTrace.ts
headers.ts            stringUtils.ts
locatorGenerators.ts  time.ts
locatorParser.ts      timeoutRunner.ts
locatorUtils.ts       traceUtils.ts
manualPromise.ts      types.ts
mimeType.ts           urlMatch.ts
multimap.ts           utilityScriptSerializers.ts

./execution/interpreter:
__init__.py           computer                   render_message.py
archived_server_1.py  core.py                    respond.py
archived_server_2.py  default_system_message.py  utils
async_core.py         llm

./execution/interpreter/computer:
__init__.py  clipboard    docs      mouse   terminal
ai           computer.py  files     os      utils
browser      contacts     keyboard  skills  vision
calendar     display      mail      sms

./execution/interpreter/computer/ai:
__init__.py  ai.py

./execution/interpreter/computer/browser:
__init__.py  browser.py  browser_next.py

./execution/interpreter/computer/calendar:
__init__.py  calendar.py

./execution/interpreter/computer/clipboard:
__init__.py  clipboard.py

./execution/interpreter/computer/contacts:
__init__.py  contacts.py

./execution/interpreter/computer/display:
__init__.py  display.py  point

./execution/interpreter/computer/display/point:
point.py

./execution/interpreter/computer/docs:
__init__.py  docs.py

./execution/interpreter/computer/files:
__init__.py  files.py

./execution/interpreter/computer/keyboard:
__init__.py  keyboard.py

./execution/interpreter/computer/mail:
__init__.py  mail.py

./execution/interpreter/computer/mouse:
__init__.py  mouse.py

./execution/interpreter/computer/os:
__init__.py  os.py

./execution/interpreter/computer/skills:
skills.py

./execution/interpreter/computer/sms:
__init__.py  sms.py

./execution/interpreter/computer/terminal:
__init__.py  base_language.py  languages  terminal.py

./execution/interpreter/computer/terminal/languages:
__init__.py     javascript.py        r.py      subprocess_language.py
applescript.py  jupyter_language.py  react.py
html.py         powershell.py        ruby.py
java.py         python.py            shell.py

./execution/interpreter/computer/utils:
computer_vision.py    html_to_png_base64.py  run_applescript.py
get_active_window.py  recipient_utils.py

./execution/interpreter/computer/vision:
__init__.py  vision.py

./execution/interpreter/llm:
__init__.py  run_function_calling_llm.py  run_tool_calling_llm.py
llm.py       run_text_llm.py              utils

./execution/interpreter/llm/utils:
convert_to_openai_messages.py  merge_deltas.py  parse_partial_json.py

./execution/interpreter/utils:
__init__.py     system_debug_info.py  truncate_output.py
lazy_import.py  telemetry.py
scan_code.py    temporary_file.py

./memory:
chromadb

./memory/chromadb:
__init__.py                 config.py       logservice  serde.py
api                         db              migrations  server
app.py                      errors.py       proto       telemetry
auth                        execution       py.typed    types.py
base_types.py               experimental    quota       utils
chromadb_rust_bindings.pyi  ingest          rate_limit
cli                         log_config.yml  segment

./memory/chromadb/api:
__init__.py                  configuration.py
async_api.py                 fastapi.py
async_client.py              models
async_fastapi.py             rust.py
base_http_client.py          segment.py
client.py                    shared_system_client.py
collection_configuration.py  types.py

./memory/chromadb/api/models:
AsyncCollection.py  Collection.py  CollectionCommon.py

./memory/chromadb/auth:
__init__.py  basic_authn  simple_rbac_authz  token_authn  utils

./memory/chromadb/auth/basic_authn:
__init__.py

./memory/chromadb/auth/simple_rbac_authz:
__init__.py

./memory/chromadb/auth/token_authn:
__init__.py

./memory/chromadb/auth/utils:
__init__.py

./memory/chromadb/cli:
__init__.py  cli.py  utils.py

./memory/chromadb/db:
__init__.py  base.py  impl  migrations.py  mixins  system.py

./memory/chromadb/db/impl:
__init__.py  grpc  sqlite.py  sqlite_pool.py

./memory/chromadb/db/impl/grpc:
client.py  server.py

./memory/chromadb/db/mixins:
embeddings_queue.py  sysdb.py

./memory/chromadb/execution:
__init__.py  executor  expression

./memory/chromadb/execution/executor:
abstract.py  distributed.py  local.py

./memory/chromadb/execution/expression:
operator.py  plan.py

./memory/chromadb/experimental:
density_relevance.ipynb

./memory/chromadb/ingest:
__init__.py  impl

./memory/chromadb/ingest/impl:
utils.py

./memory/chromadb/logservice:
logservice.py

./memory/chromadb/migrations:
__init__.py  embeddings_queue  metadb  sysdb

./memory/chromadb/migrations/embeddings_queue:
00001-embeddings.sqlite.sql  00002-embeddings-queue-config.sqlite.sql

./memory/chromadb/migrations/metadb:
00001-embedding-metadata.sqlite.sql
00002-embedding-metadata.sqlite.sql
00003-full-text-tokenize.sqlite.sql
00004-metadata-indices.sqlite.sql
00005-max-seq-id-int.sqlite.sql

./memory/chromadb/migrations/sysdb:
00001-collections.sqlite.sql
00002-segments.sqlite.sql
00003-collection-dimension.sqlite.sql
00004-tenants-databases.sqlite.sql
00005-remove-topic.sqlite.sql
00006-collection-segment-metadata.sqlite.sql
00007-collection-config.sqlite.sql
00008-maintenance-log.sqlite.sql
00009-segment-collection-not-null.sqlite.sql

./memory/chromadb/proto:
__init__.py  convert.py  utils.py

./memory/chromadb/quota:
__init__.py  simple_quota_enforcer

./memory/chromadb/quota/simple_quota_enforcer:
__init__.py

./memory/chromadb/rate_limit:
__init__.py  simple_rate_limit

./memory/chromadb/rate_limit/simple_rate_limit:
__init__.py

./memory/chromadb/segment:
__init__.py  distributed  impl

./memory/chromadb/segment/distributed:
__init__.py

./memory/chromadb/segment/impl:
__init__.py  distributed  manager  metadata  vector

./memory/chromadb/segment/impl/distributed:
segment_directory.py

./memory/chromadb/segment/impl/manager:
__init__.py  cache  distributed.py  local.py

./memory/chromadb/segment/impl/manager/cache:
__init__.py  cache.py

./memory/chromadb/segment/impl/metadata:
sqlite.py

./memory/chromadb/segment/impl/vector:
batch.py              hnsw_params.py  local_persistent_hnsw.py
brute_force_index.py  local_hnsw.py

./memory/chromadb/server:
__init__.py  fastapi

./memory/chromadb/server/fastapi:
__init__.py  types.py

./memory/chromadb/telemetry:
__init__.py  opentelemetry  product

./memory/chromadb/telemetry/opentelemetry:
__init__.py  fastapi.py  grpc.py

./memory/chromadb/telemetry/product:
__init__.py  events.py  posthog.py

./memory/chromadb/utils:
__init__.py       directory.py           messageid.py
async_to_sync.py  distance_functions.py  read_write_lock.py
batch_utils.py    embedding_functions    rendezvous_hash.py
data_loaders.py   fastapi.py             results.py
delete_file.py    lru_cache.py

./memory/chromadb/utils/embedding_functions:
__init__.py
amazon_bedrock_embedding_function.py
baseten_embedding_function.py
chroma_langchain_embedding_function.py
cloudflare_workers_ai_embedding_function.py
cohere_embedding_function.py
google_embedding_function.py
huggingface_embedding_function.py
instructor_embedding_function.py
jina_embedding_function.py
mistral_embedding_function.py
morph_embedding_function.py
ollama_embedding_function.py
onnx_mini_lm_l6_v2.py
open_clip_embedding_function.py
openai_embedding_function.py
roboflow_embedding_function.py
schemas
sentence_transformer_embedding_function.py
text2vec_embedding_function.py
together_ai_embedding_function.py
voyageai_embedding_function.py

./memory/chromadb/utils/embedding_functions/schemas:
__init__.py  registry.py  schema_utils.py

./role-system:
__init__.py  crews          llm.py      rag        tools
agent.py     experimental   llms        security   translations
agents       flow           memory      task.py    types
cli          knowledge      process.py  tasks      utilities
crew.py      lite_agent.py  project     telemetry

./role-system/agents:
__init__.py     cache                   tools_handler.py
agent_adapters  crew_agent_executor.py
agent_builder   parser.py

./role-system/agents/agent_adapters:
__init__.py            base_converter_adapter.py  langgraph
base_agent_adapter.py  base_tool_adapter.py       openai_agents

./role-system/agents/agent_adapters/langgraph:
__init__.py           langgraph_tool_adapter.py
langgraph_adapter.py  structured_output_converter.py

./role-system/agents/agent_adapters/openai_agents:
__init__.py        openai_agent_tool_adapter.py
openai_adapter.py  structured_output_converter.py

./role-system/agents/agent_builder:
__init__.py  base_agent.py  base_agent_executor_mixin.py  utilities

./role-system/agents/agent_builder/utilities:
__init__.py  base_output_converter.py  base_token_process.py

./role-system/agents/cache:
__init__.py  cache_handler.py

./role-system/cli:
__init__.py          enterprise                 run_crew.py
add_crew_to_flow.py  evaluate_crew.py           settings
authentication       git.py                     shared
cli.py               install_crew.py            templates
command.py           kickoff_flow.py            tools
config.py            organization               train_crew.py
constants.py         plot_flow.py               update_crew.py
create_crew.py       plus_api.py                utils.py
create_flow.py       provider.py                version.py
crew_chat.py         replay_from_task.py
deploy               reset_memories_command.py

./role-system/cli/authentication:
__init__.py  constants.py  main.py  providers  token.py  utils.py

./role-system/cli/authentication/providers:
auth0.py  base_provider.py  okta.py  workos.py

./role-system/cli/deploy:
__init__.py  main.py

./role-system/cli/enterprise:
__init__.py  main.py

./role-system/cli/organization:
__init__.py  main.py

./role-system/cli/settings:
__init__.py  main.py

./role-system/cli/shared:
__init__.py  token_manager.py

./role-system/cli/templates:
__init__.py  crew  flow  tool

./role-system/cli/templates/crew:
__init__.py  config  crew.py  knowledge  main.py  tools

./role-system/cli/templates/crew/config:
agents.yaml  tasks.yaml

./role-system/cli/templates/crew/knowledge:

./role-system/cli/templates/crew/tools:
__init__.py  custom_tool.py

./role-system/cli/templates/flow:
__init__.py  crews  main.py  tools

./role-system/cli/templates/flow/crews:
poem_crew

./role-system/cli/templates/flow/crews/poem_crew:
__init__.py  config  poem_crew.py

./role-system/cli/templates/flow/crews/poem_crew/config:
agents.yaml  tasks.yaml

./role-system/cli/templates/flow/tools:
__init__.py  custom_tool.py

./role-system/cli/templates/tool:
src

./role-system/cli/templates/tool/src:
{{folder_name}}

./role-system/cli/templates/tool/src/{{folder_name}}:
__init__.py  tool.py

./role-system/cli/tools:
__init__.py  main.py

./role-system/crews:
__init__.py  crew_output.py

./role-system/experimental:
__init__.py  evaluation

./role-system/experimental/evaluation:
__init__.py         evaluation_display.py   json_parser.py
agent_evaluator.py  evaluation_listener.py  metrics
base_evaluator.py   experiment              testing.py

./role-system/experimental/evaluation/experiment:
__init__.py  result.py  result_display.py  runner.py

./role-system/experimental/evaluation/metrics:
__init__.py      reasoning_metrics.py         tools_metrics.py
goal_metrics.py  semantic_quality_metrics.py

./role-system/flow:
__init__.py        flow_visualizer.py        types.py
assets             html_template_handler.py  utils.py
config.py          legend_generator.py       visualization_utils.py
flow.py            path_utils.py
flow_trackable.py  persistence

./role-system/flow/assets:
crewai_flow_visual_template.html  crewai_logo.svg

./role-system/flow/persistence:
__init__.py  base.py  decorators.py  sqlite.py

./role-system/knowledge:
__init__.py   knowledge_config.py  storage
knowledge.py  source               utils

./role-system/knowledge/source:
__init__.py                    excel_knowledge_source.py
base_file_knowledge_source.py  json_knowledge_source.py
base_knowledge_source.py       pdf_knowledge_source.py
crew_docling_source.py         string_knowledge_source.py
csv_knowledge_source.py        text_file_knowledge_source.py

./role-system/knowledge/storage:
__init__.py  base_knowledge_storage.py  knowledge_storage.py

./role-system/knowledge/utils:
__init__.py  knowledge_utils.py

./role-system/llms:
__init__.py  base_llm.py  third_party

./role-system/llms/third_party:
__init__.py  ai_suite.py

./role-system/memory:
__init__.py  entity    long_term  short_term
contextual   external  memory.py  storage

./role-system/memory/contextual:
__init__.py  contextual_memory.py

./role-system/memory/entity:
__init__.py  entity_memory.py  entity_memory_item.py

./role-system/memory/external:
__init__.py  external_memory.py  external_memory_item.py

./role-system/memory/long_term:
__init__.py  long_term_memory.py  long_term_memory_item.py

./role-system/memory/short_term:
__init__.py  short_term_memory.py  short_term_memory_item.py

./role-system/memory/storage:
__init__.py   kickoff_task_outputs_storage.py  mem0_storage.py
interface.py  ltm_sqlite_storage.py            rag_storage.py

./role-system/project:
__init__.py  annotations.py  crew_base.py  utils.py

./role-system/rag:
__init__.py  chromadb  core  embeddings  storage  types.py

./role-system/rag/chromadb:
__init__.py  client.py  types.py  utils.py

./role-system/rag/core:
__init__.py  base_client.py  base_provider.py

./role-system/rag/embeddings:
__init__.py  configurator.py  factory.py  types.py

./role-system/rag/storage:
__init__.py  base_rag_storage.py

./role-system/security:
__init__.py  fingerprint.py  security_config.py

./role-system/tasks:
__init__.py          hallucination_guardrail.py  output_format.py
conditional_task.py  llm_guardrail.py            task_output.py

./role-system/telemetry:
__init__.py  constants.py  telemetry.py

./role-system/tools:
__init__.py  base_tool.py  structured_tool.py  tool_types.py
agent_tools  cache_tools   tool_calling.py     tool_usage.py

./role-system/tools/agent_tools:
__init__.py        agent_tools.py        base_agent_tools.py
add_image_tool.py  ask_question_tool.py  delegate_work_tool.py

./role-system/tools/cache_tools:
__init__.py  cache_tools.py

./role-system/translations:
en.json

./role-system/types:
__init__.py  crew_chat.py  hitl.py  usage_metrics.py

./role-system/utilities:
__init__.py                     llm_utils.py
agent_utils.py                  logger.py
chromadb.py                     parser.py
config.py                       paths.py
constants.py                    planning_handler.py
converter.py                    printer.py
crew                            prompts.py
crew_json_encoder.py            pydantic_schema_parser.py
crew_pydantic_output_parser.py  reasoning_handler.py
errors.py                       rpm_controller.py
evaluators                      serialization.py
events                          string_utils.py
exceptions                      task_output_storage_handler.py
file_handler.py                 token_counter_callback.py
formatter.py                    tool_utils.py
guardrail.py                    training_converter.py
i18n.py                         training_handler.py
internal_instructor.py

./role-system/utilities/crew:
__init__.py  crew_context.py  models.py

./role-system/utilities/evaluators:
__init__.py  crew_evaluator_handler.py  task_evaluator.py

./role-system/utilities/events:
__init__.py             event_types.py           reasoning_events.py
agent_events.py         flow_events.py           task_events.py
base_event_listener.py  knowledge_events.py      third_party
base_events.py          listeners                tool_usage_events.py
crew_events.py          llm_events.py            utils
crewai_event_bus.py     llm_guardrail_events.py
event_listener.py       memory_events.py

./role-system/utilities/events/listeners:
memory_listener.py  tracing

./role-system/utilities/events/listeners/tracing:
__init__.py             trace_listener.py  utils.py
trace_batch_manager.py  types.py

./role-system/utilities/events/third_party:
__init__.py

./role-system/utilities/events/utils:
__init__.py  console_formatter.py

./role-system/utilities/exceptions:
__init__.py  context_window_exceeding_exception.py

./state-machine:
langgraph

./state-machine/langgraph:
_internal  constants.py  graph    py.typed    typing.py   warnings.py
channels   errors.py     managed  runtime.py  utils
config.py  func          pregel   types.py    version.py

./state-machine/langgraph/_internal:
__init__.py  _constants.py  _pydantic.py  _runnable.py
_cache.py    _fields.py     _queue.py     _scratchpad.py
_config.py   _future.py     _retry.py     _typing.py

./state-machine/langgraph/channels:
__init__.py   binop.py            named_barrier_value.py
any_value.py  ephemeral_value.py  topic.py
base.py       last_value.py       untracked_value.py

./state-machine/langgraph/func:
__init__.py

./state-machine/langgraph/graph:
__init__.py  _branch.py  _node.py  message.py  state.py  ui.py

./state-machine/langgraph/managed:
__init__.py  base.py  is_last_step.py

./state-machine/langgraph/pregel:
__init__.py     _draw.py      _messages.py  _validate.py  remote.py
_algo.py        _executor.py  _read.py      _write.py     types.py
_call.py        _io.py        _retry.py     debug.py
_checkpoint.py  _log.py       _runner.py    main.py
_config.py      _loop.py      _utils.py     protocol.py

./state-machine/langgraph/utils:
__init__.py  config.py  runnable.py