from sqlalchemy.ext.asyncio import AsyncSession
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings
from app.services.document_service import DocumentService
from app.services.event_service import EventService
from app.services.responsibility_service import ResponsibilityService
from uuid import UUID

class RAGService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_service = DocumentService(session)
        self.event_service = EventService(session)
        self.resp_service = ResponsibilityService(session)
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            temperature=0,
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_model
        )

    async def answer_query(self, query: str, user_id: UUID | None = None) -> dict:
        # 1. Retrieve relevant documents (Semantic Search)
        # Using a limit of 5 to get enough context
        docs = await self.doc_service.search_documents(query, limit=5)
        doc_context = "\n\n".join([d.content for d in docs]) if docs else "No relevant documents found."
        
        # 2. Retrieve structured data (Events & Responsibilities)
        # For now, we fetch recent events if user_id is provided, else generic info
        structured_context: str = ""
        if user_id:
            events = await self.event_service.get_user_events(user_id, limit=5)
            if events:
                event_list = "\n".join([f"- {e.title} (Time: {e.start_time})" for e in events])
                structured_context += f"Upcoming Events:\n{event_list}\n\n"
                
                # Fetch high priority responsibilities attached to those events
                structured_context = str(structured_context) + "Active Responsibilities:\n"
                for e in events:
                    resps = await self.resp_service.get_event_responsibilities(e.id)
                    for r in resps:
                        structured_context = structured_context + f"- {str(r.title)} (Status: {str(r.status.value)}, Priority: {str(r.priority)})\n"  # type: ignore
        else:
            structured_context = "No user context provided (events/responsibilities unavailable)."

        # 3. Construct Prompt
        # We give the LLM the retrieved context and the user query
        system_prompt = """You are an intelligent assistant for the HRCE platform. 
Answer the user's question based ONLY on the provided context below.
If the answer is not in the context, say you don't know locally.

Context from Documents:
{doc_context}

Context from User Data:
{structured_context}
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{query}")
        ])

        # 4. Generate Answer
        chain = prompt | self.llm | StrOutputParser()
        answer = await chain.ainvoke({
            "doc_context": doc_context,
            "structured_context": structured_context,
            "query": query
        })

        return {
            "answer": answer,
            "sources": [d.title for d in docs] if docs else []
        }
