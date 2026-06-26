import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

load_dotenv()

DA_PROVIDER = os.getenv("DA_PROVIDER", "ollama").lower()

if DA_PROVIDER == "anthropic":
    from langchain_anthropic import ChatAnthropic
else:
    from langchain_ollama import ChatOllama


class ChatbotService:
    DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant. Answer questions clearly."

    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        if DA_PROVIDER == "anthropic":
            self.allowed_models = {"claude-sonnet-4-5", "claude-opus-4-5", "claude-haiku-4-5"}
            default_model = os.getenv("DA_MODEL", "claude-sonnet-4-5")
        else:
            self.allowed_models = {"qwen3:14b"}
            default_model = os.getenv("DA_MODEL", "qwen3:14b")

        if default_model not in self.allowed_models:
            default_model = next(iter(self.allowed_models))

        self.model_name = None
        self.model = None
        self._initialize_model(default_model)

        self.workflow = StateGraph(state_schema=MessagesState)
        self.workflow.add_edge(START, "model")
        self.workflow.add_node("model", self._call_model)

        self.memory = MemorySaver()
        self.app = self.workflow.compile(checkpointer=self.memory)

        self.default_system_prompt = system_prompt
        self.current_system_prompt = system_prompt
        self.set_system_prompt(system_prompt)

    def _initialize_model(self, model_name: str):
        """Initialize or update the LLM based on the configured provider."""
        is_update = self.model_name is not None
        self.model_name = model_name

        if DA_PROVIDER == "anthropic":
            self.model = ChatAnthropic(
                model=self.model_name,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=1.0,
            )
        else:
            self.model = ChatOllama(
                model=self.model_name,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=1.0,
            )

        action = "updated" if is_update else "initialized"
        print(f"[ChatbotService] ✅ Model {action}: {self.model_name} (provider: {DA_PROVIDER})")

    def _call_model(self, state: MessagesState):
        prompt = self.prompt_template.invoke(state)
        response = self.model.invoke(prompt)
        return {"messages": response}

    def set_system_prompt(self, system_prompt: str):
        self.current_system_prompt = system_prompt
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

    def set_model(self, model_name: str):
        """Validate model name and re-initialize if needed."""
        if model_name not in self.allowed_models:
            raise ValueError(f"Unsupported model: {model_name}")
        if model_name != self.model_name:
            self._initialize_model(model_name)

    def chat(
        self,
        message: str,
        thread_id: str = "default",
        system_prompt: str = None,
        model: str = None,
    ) -> str:
        if model:
            self.set_model(model)
        try:
            if system_prompt and system_prompt.strip():
                self.set_system_prompt(system_prompt)

            config = {"configurable": {"thread_id": thread_id}}
            output = self.app.invoke({"messages": [HumanMessage(content=message)]}, config)
            return output["messages"][-1].content

        except Exception as e:
            return f"Error: {str(e)}"

    async def stream_chat(
        self, message: str, thread_id: str = "default", model: str = None
    ):
        if model:
            self.set_model(model)
        try:
            config = {"configurable": {"thread_id": thread_id}}
            async for chunk, metadata in self.app.astream(
                {"messages": [HumanMessage(content=message)]}, config, stream_mode="messages"
            ):
                if isinstance(chunk, AIMessage):
                    yield chunk.content

        except Exception as e:
            yield f"Error: {str(e)}"

    def get_conversation_history(self, thread_id: str):
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)
        messages = state.values.get("messages", [])
        conversation_text = ""

        for message in messages:
            if isinstance(message, HumanMessage):
                role = "Bot B"
            elif isinstance(message, AIMessage):
                role = "Bot A"
            elif isinstance(message, SystemMessage):
                continue
            else:
                role = "Unknown"
            conversation_text += f"{role}:\n{message.content}\n\n"

        return conversation_text
