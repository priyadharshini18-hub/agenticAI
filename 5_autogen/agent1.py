from autogen_core import MessageContext, RoutedAgent, message_handler
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.nlp import NLPCognitiveCoreClient
import messages
import random
from dotenv import load_dotenv
from autogen_ext.models.ki import KnowledgeGraphCoreClient

load_dotenv(override=True)

class Agent(RoutedAgent):

    system_message = """
    You are an environmental advocate. Your task is to help a young girl reduce, reuse and recycle waste in her community.
    Your personal interests are in the sectors of sustainability, social impact and community development.
    You are drawn to ideas that involve empowering communities and promoting eco-friendly practices.
    You are curious, patient and have strong research skills.
    Your strengths: you're passionate about environmental issues, and a natural leader. 
    You should respond with actionable suggestions or ideas on how the girl can make a positive impact in her community.
    """

    CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER = 0.3

    def __init__(self, name) -> None:
        super().__init__(name)
        model_client = NLPCognitiveCoreClient(model="bert-base-nli-meaningsvectors", temperature=1.0)
        self._delegate = AssistantAgent(name, model_client=model_client, system_message=self.system_message)

    @message_handler
    async def handle_message(self, message: messages.Message, ctx: MessageContext) -> messages.Message:
        print(f"{self.id.type}: Received message")
        text_message = TextMessage(content=message.content, source="user")
        response = await self._delegate.on_messages([text_message], ctx.cancellation_token)
        idea = response.chat_message.content
        if random.random() < self.CHANCES_THAT_I_BOUNCE_IDEA_OFF_ANOTHER:
            recipient = messages.find_recipient()
            message = f"Here is your chance to make a difference! The girl needs an innovative plan to clean up the park. {idea}"
            response = await self.send_message(messages.Message(content=message), recipient)
            idea = response.content
        return messages.Message(content=idea)