# core 目录 API 详细说明

本目录为 LLM 智能体系统的核心管理层，统一管理智能体（Agent）、大语言模型（LLM）、工具（Tool）及提示词（Prompt）。本文件详细列出各核心类的所有可被外部调用的方法，包含功能、参数、返回值、用法示例和注意事项，确保开发者无遗漏、快速查阅和正确调用。

---

## 1. AgentManager（core/agent_manager.py）

### 主要功能
- 负责 LangChain AgentExecutor 的创建、缓存、流式/非流式推理、系统提示词集成、动态刷新。
- 支持流式输出、回调、系统提示词切换、强制刷新缓存。

### 所有可调用方法

#### `get_agent(agent_name, llm_model_name="gpt-4o", system_prompt_name="default", force_refresh=False, streaming=False) -> AgentExecutor`
- **功能**：获取或创建 AgentExecutor 实例，支持流式/非流式、系统提示词切换、强制刷新。
- **参数**：
  - `agent_name`：Agent 名称（settings.AVAILABLE_AGENTS 配置）
  - `llm_model_name`：LLM 模型名
  - `system_prompt_name`：系统提示词名（见 PromptManager）
  - `force_refresh`：是否强制刷新缓存
  - `streaming`：是否启用流式输出
- **返回值**：AgentExecutor 实例
- **用法**：
  ```python
  agent = AgentManager.get_agent("my_agent", "gpt-4o", system_prompt_name="creative", streaming=True)
  ```
- **注意**：缓存键包含 streaming 标志，切换流式/非流式会重新创建实例。

#### `run_agent(agent_name, user_input, llm_model_name="deepseek-chat", system_prompt_name="default") -> str`
- **功能**：非流式运行 Agent，返回完整结果。
- **参数**：同上，`user_input` 为用户输入。
- **返回值**：字符串，Agent 执行结果。
- **用法**：
  ```python
  result = AgentManager.run_agent("my_agent", "你好，查下天气")
  ```

#### `run_agent_stream(agent_name, user_input, llm_model_name="deepseek-chat", system_prompt_name="default", **kwargs) -> Generator[str, None, str]`
- **功能**：流式运行 Agent，逐块 yield 内容。
- **参数**：同上。
- **返回值**：生成器，每次 yield 一个内容块，最后返回完整结果。
- **用法**：
  ```python
  for chunk in AgentManager.run_agent_stream("my_agent", "流式测试"): print(chunk, end="")
  ```
- **注意**：如 LLM/Agent 不支持流式，将自动回退为分块输出。

#### `run_agent_stream_callback(agent_name, user_input, callback, llm_model_name="deepseek-chat", system_prompt_name="default") -> str`
- **功能**：以回调方式流式运行 Agent。
- **参数**：callback 为函数，接收每个内容块。
- **返回值**：完整结果字符串。
- **用法**：
  ```python
  AgentManager.run_agent_stream_callback("my_agent", "流式回调", lambda x: print(x, end=""))
  ```

#### `update_agent_system_prompt(agent_name, llm_model_name, new_system_prompt_name) -> bool`
- **功能**：强制刷新指定 Agent 的系统提示词。
- **返回值**：是否成功。
- **用法**：
  ```python
  AgentManager.update_agent_system_prompt("my_agent", "gpt-4o", "creative")
  ```

#### `get_available_agents_info() -> Dict[str, Any]`
- **功能**：获取所有可用 Agent 的配置信息。
- **返回值**：字典。
- **用法**：
  ```python
  info = AgentManager.get_available_agents_info()
  ```

---

## 2. LLMManager（core/llm_manager.py）

### 主要功能
- 统一管理所有 LLM，支持流式/非流式、系统提示词、历史对话、回调、模型信息获取。

### 所有可调用方法

#### `get_llm(model_name, temperature=0.7, streaming=False) -> BaseChatModel`
- **功能**：获取指定 LLM 实例，支持流式。
- **参数**：
  - `model_name`：模型名
  - `temperature`：采样温度
  - `streaming`：是否流式
- **返回值**：BaseChatModel 实例
- **用法**：
  ```python
  llm = LLMManager.get_llm("gpt-4o-mini", streaming=True)
  ```

#### `chat_with_prompt(user_message, model_name="deepseek-chat", system_prompt_name="default", temperature=0.7, **kwargs) -> str`
- **功能**：非流式对话，带系统提示词。
- **返回值**：AI 回复内容。
- **用法**：
  ```python
  reply = LLMManager.chat_with_prompt("你好", model_name="gpt-4o-mini")
  ```

#### `chat_with_prompt_stream(user_message, model_name="deepseek-chat", system_prompt_name="default", temperature=0.7, **kwargs) -> Generator[str, None, str]`
- **功能**：流式对话，带系统提示词。
- **返回值**：生成器。
- **用法**：
  ```python
  for chunk in LLMManager.chat_with_prompt_stream("你好"): print(chunk, end="")
  ```

#### `chat_with_prompt_stream_callback(user_message, callback, model_name="deepseek-chat", system_prompt_name="default", temperature=0.7) -> str`
- **功能**：回调方式流式对话。
- **参数**：callback 为函数。
- **返回值**：完整内容。
- **用法**：
  ```python
  LLMManager.chat_with_prompt_stream_callback("你好", lambda x: print(x, end=""))
  ```

#### `chat_with_history(user_message, history, model_name="deepseek-chat", system_prompt_name="default", temperature=0.7) -> str`
- **功能**：非流式历史对话。
- **参数**：history 为 BaseMessage 列表。
- **返回值**：AI 回复内容。

#### `chat_with_history_stream(user_message, history, model_name="deepseek-chat", system_prompt_name="default", temperature=0.7) -> Generator[str, None, str]`
- **功能**：流式历史对话。
- **返回值**：生成器。

#### `update_llm_system_prompt(system_prompt_name) -> bool`
- **功能**：全局切换系统提示词。
- **返回值**：是否成功。

#### `get_available_llms_info() -> Dict[str, Any]`
- **功能**：获取所有可用 LLM 配置信息。
- **返回值**：字典。

---

## 3. PromptManager（core/prompt_manager.py）

### 主要功能
- 管理系统提示词，支持增删改查、持久化、变量替换、当前提示词切换。

### 所有可调用方法

#### `initialize()`
- **功能**：初始化提示词管理器（自动加载默认和自定义提示词）。

#### `create_system_prompt(name, content, description="") -> bool`
- **功能**：创建新系统提示词。
- **返回值**：是否成功。

#### `update_system_prompt(name, content=None, description=None) -> bool`
- **功能**：更新指定系统提示词。
- **返回值**：是否成功。

#### `delete_system_prompt(name) -> bool`
- **功能**：删除指定系统提示词。
- **返回值**：是否成功。
- **注意**：不能删除 default。

#### `set_current_system_prompt(name) -> bool`
- **功能**：切换当前系统提示词。
- **返回值**：是否成功。

#### `get_current_system_prompt() -> Optional[str]`
- **功能**：获取当前系统提示词内容。
- **返回值**：字符串或 None。

#### `list_system_prompts() -> Dict[str, SystemPromptConfig]`
- **功能**：获取所有系统提示词配置。
- **返回值**：字典。

#### `get_system_prompt(name) -> Optional[SystemPromptConfig]`
- **功能**：获取指定系统提示词配置对象。
- **返回值**：SystemPromptConfig 或 None。

---

## 4. ToolManager（core/tool_manager.py）

### 主要功能
- 统一注册、初始化和管理所有可用 LangChain 工具。

### 所有可调用方法

#### `initialize_tools()`
- **功能**：初始化所有工具（只执行一次）。

#### `get_tools_by_names(tool_names: List[str]) -> List[Tool]`
- **功能**：按名称获取工具实例。
- **返回值**：工具实例列表。
- **注意**：未找到的工具会有日志警告。

#### `get_all_tools() -> List[Tool]`
- **功能**：获取所有已初始化工具实例。
- **返回值**：工具实例列表。

#### `get_available_tool_names() -> List[str]`
- **功能**：获取所有可用工具名称。
- **返回值**：名称列表。

#### `is_tool_available(tool_name: str) -> bool`
- **功能**：检查指定工具是否可用。
- **返回值**：布尔值。

#### `get_tool_info() -> Dict[str, str]`
- **功能**：获取所有工具的名称及描述。
- **返回值**：字典。

---

如需更详细的参数类型、异常说明或特殊用法，请查阅源码或联系维护者。