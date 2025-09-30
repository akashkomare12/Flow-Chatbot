from flask import Flask, render_template, request, jsonify, session
import os
from dotenv import load_dotenv
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.document_loaders import TextLoader
from langchain.docstore.document import Document
from langchain.memory import ConversationBufferWindowMemory
import json
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize vector store
persist_directory = "vector_store"
embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)

# Global variable for RAG bot
rag_bot = None
flow_bot = None

def initialize_rag_system():
    """Initialize the RAG system with sample documents"""
    global rag_bot
    try:
        # Clear existing vector store
        if os.path.exists(persist_directory):
            import shutil
            shutil.rmtree(persist_directory)
        
        print("Initializing RAG system...")
        
        # Read the document directly
        with open("data/sample_documents.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        documents = [Document(page_content=content, metadata={"source": "company_handbook"})]
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )
        texts = text_splitter.split_documents(documents)
        
        print(f"Created {len(texts)} text chunks")
        
        # Create vector store
        vector_store = Chroma.from_documents(
            documents=texts,
            embedding=embeddings,
            persist_directory=persist_directory
        )
        vector_store.persist()
        print("RAG system initialized successfully!")
        
        # Initialize RAG bot after vector store is created
        rag_bot = RAGChatbot()
        
    except Exception as e:
        print(f"Error initializing RAG system: {str(e)}")
        rag_bot = None

# Flow-based chatbot logic
class FlowChatbot:
    def __init__(self):
        self.flow_steps = [
            {
                "id": "name",
                "question": "Hello! What's your name?",
                "validation": lambda x: len(x.strip()) > 0,
                "error_msg": "Please enter a valid name."
            },
            {
                "id": "email",
                "question": "Nice to meet you! What's your email address?",
                "validation": lambda x: re.match(r'^[^@]+@[^@]+\.[^@]+$', x),
                "error_msg": "Please enter a valid email address."
            },
            {
                "id": "service",
                "question": "Which service are you interested in? (Web Development, Data Analysis, AI/ML, Other)",
                "validation": lambda x: x.strip().lower() in ['web development', 'data analysis', 'ai/ml', 'other'],
                "error_msg": "Please choose from: Web Development, Data Analysis, AI/ML, or Other."
            },
            {
                "id": "budget",
                "question": "What's your approximate budget range? ($500-$1000, $1000-$5000, $5000+)",
                "validation": lambda x: x.strip().lower() in ['$500-$1000', '$1000-$5000', '$5000+'],
                "error_msg": "Please choose from: $500-$1000, $1000-$5000, or $5000+."
            },
            {
                "id": "timeline",
                "question": "What's your expected timeline? (1-2 weeks, 1 month, 2+ months)",
                "validation": lambda x: x.strip().lower() in ['1-2 weeks', '1 month', '2+ months'],
                "error_msg": "Please choose from: 1-2 weeks, 1 month, or 2+ months."
            }
        ]
    
    def get_next_question(self, current_step):
        if current_step < len(self.flow_steps):
            return self.flow_steps[current_step]
        return None
    
    def validate_answer(self, step_id, answer):
        step = next((s for s in self.flow_steps if s["id"] == step_id), None)
        if step and step["validation"](answer):
            return True, ""
        return False, step["error_msg"] if step else "Invalid step"
    
    def generate_summary(self, responses):
        summary = "Here's a summary of your information:\n\n"
        for step_id, answer in responses.items():
            step = next((s for s in self.flow_steps if s["id"] == step_id), None)
            if step:
                summary += f"• {step['question']}\n  Answer: {answer}\n\n"
        
        summary += "Thank you for providing this information! We'll get back to you soon."
        return summary

# RAG chatbot with memory
class RAGChatbot:
    def __init__(self):
        try:
            self.vector_store = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )
            # Initialize memory to remember last 3 conversations
            self.memory = ConversationBufferWindowMemory(k=3, return_messages=True)
            print("RAG chatbot with memory initialized successfully")
        except Exception as e:
            print(f"Error initializing RAG chatbot: {str(e)}")
            self.vector_store = None
            self.memory = None
    
    def get_response(self, query):
        try:
            if not self.vector_store:
                return "I apologize, but the document system is not properly initialized. Please try again later."
            
            print(f"Searching for: {query}")
            
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(query, k=3)
            print(f"Found {len(docs)} relevant documents")
            
            if not docs:
                return "I couldn't find any relevant information in the documents to answer your question. Please try asking about company policies, leave, benefits, or other topics covered in the employee handbook."
            
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Get conversation history from memory
            memory_variables = self.memory.load_memory_variables({})
            chat_history = memory_variables.get('history', [])
            
            # Format chat history for context
            history_context = ""
            if chat_history:
                history_context = "\n\nPrevious conversation:\n"
                for msg in chat_history[-6:]:  # Last 3 exchanges (user + bot)
                    role = "Human" if msg.type == "human" else "Assistant"
                    history_context += f"{role}: {msg.content}\n"
            
            # Print first 200 chars of context for debugging
            print(f"Context sample: {context[:200]}...")
            
            # Create enhanced prompt with context and memory
            prompt = f"""Based on the following context from company documents and our previous conversation, please answer the user's question.

Company Documents Context:
{context}
{history_context}

Current User Question: {query}

Please provide a helpful and accurate answer based on the company documents and our conversation history:"""
            
            # Generate response using OpenAI
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful HR assistant that answers questions based on the provided company documents and conversation history. "},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Save conversation to memory
            self.memory.save_context({"input": query}, {"output": answer})
            
            return answer
        
        except Exception as e:
            print(f"Error in RAG response: {str(e)}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"

# Initialize flow bot (doesn't depend on vector store)
flow_bot = FlowChatbot()

def initialize_app():
    """Initialize the application components"""
    global rag_bot, flow_bot
    print("Initializing application...")
    initialize_rag_system()
    print("Application initialization complete")

# Initialize the app when the module is imported
initialize_app()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/flow-chat')
def flow_chat():
    session['flow_step'] = 0
    session['flow_responses'] = {}
    return render_template('flow_chat.html')

@app.route('/rag-chat')
def rag_chat():
    return render_template('rag_chat.html')

@app.route('/api/flow/next-question', methods=['POST'])
def get_next_question():
    current_step = session.get('flow_step', 0)
    data = request.get_json()
    
    # Validate current answer if provided
    if data and 'answer' in data and 'step_id' in data:
        is_valid, error_msg = flow_bot.validate_answer(data['step_id'], data['answer'])
        if not is_valid:
            return jsonify({'error': error_msg})
        
        # Store valid response
        session['flow_responses'][data['step_id']] = data['answer']
        session['flow_step'] = current_step + 1
        current_step += 1
    
    # Get next question or generate summary
    next_question = flow_bot.get_next_question(current_step)
    if next_question:
        return jsonify({
            'step_id': next_question['id'],
            'question': next_question['question'],
            'step_number': current_step + 1,
            'total_steps': len(flow_bot.flow_steps)
        })
    else:
        # Generate final summary
        summary = flow_bot.generate_summary(session['flow_responses'])
        session.pop('flow_step', None)
        session.pop('flow_responses', None)
        return jsonify({'summary': summary})

@app.route('/api/rag/chat', methods=['POST'])
def rag_chat_api():
    global rag_bot
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message.strip():
        return jsonify({'error': 'Message cannot be empty'})
    
    # Check if RAG bot is initialized
    if rag_bot is None:
        # Try to reinitialize
        try:
            rag_bot = RAGChatbot()
        except:
            return jsonify({'error': 'RAG system is not initialized. Please restart the application.'})
    
    response = rag_bot.get_response(user_message)
    return jsonify({'response': response})

@app.route('/api/debug/rag')
def debug_rag():
    """Debug endpoint to check RAG system status"""
    global rag_bot
    try:
        debug_info = {
            'vector_store_exists': os.path.exists(persist_directory),
            'rag_bot_initialized': rag_bot is not None,
            'vector_store_available': rag_bot.vector_store is not None if rag_bot else False,
            'memory_initialized': rag_bot.memory is not None if rag_bot else False
        }
        
        if rag_bot and rag_bot.vector_store:
            test_query = "dress code"
            docs = rag_bot.vector_store.similarity_search(test_query, k=2)
            debug_info.update({
                'test_query': test_query,
                'documents_found': len(docs),
                'sample_content': docs[0].page_content[:500] if docs else "No documents found"
            })
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)