class ChatInterface {
    constructor() {
        this.currentMode = null;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Mode selection (only on home page)
        const flowModeBtn = document.getElementById('flowMode');
        const ragModeBtn = document.getElementById('ragMode');
        
        if (flowModeBtn) {
            flowModeBtn.addEventListener('click', () => this.startFlowChat());
        }
        if (ragModeBtn) {
            ragModeBtn.addEventListener('click', () => this.startRagChat());
        }
        
        // Back buttons (only on chat pages)
        const backToHome = document.getElementById('backToHome');
        const backToHomeRag = document.getElementById('backToHomeRag');
        
        if (backToHome) {
            backToHome.addEventListener('click', () => this.showHome());
        }
        if (backToHomeRag) {
            backToHomeRag.addEventListener('click', () => this.showHome());
        }
        
        // Chat input (only on respective chat pages)
        const sendFlowMessage = document.getElementById('sendFlowMessage');
        const sendRagMessage = document.getElementById('sendRagMessage');
        const flowInput = document.getElementById('flowInput');
        const ragInput = document.getElementById('ragInput');
        
        if (sendFlowMessage) {
            sendFlowMessage.addEventListener('click', () => this.sendFlowMessage());
        }
        if (sendRagMessage) {
            sendRagMessage.addEventListener('click', () => this.sendRagMessage());
        }
        if (flowInput) {
            flowInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendFlowMessage();
            });
        }
        if (ragInput) {
            ragInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') this.sendRagMessage();
            });
        }
    }

    showHome() {
        // Navigate back to home page
        window.location.href = '/';
    }

    startFlowChat() {
        // Navigate to flow chat page
        window.location.href = '/flow-chat';
    }

    startRagChat() {
        // Navigate to RAG chat page
        window.location.href = '/rag-chat';
    }

    initializeFlowChat() {
        // This method is called when on the flow-chat page
        this.currentMode = 'flow';
        this.clearChat('flowMessages');
        this.getNextFlowQuestion();
    }

    initializeRagChat() {
        // This method is called when on the rag-chat page
        this.currentMode = 'rag';
        // Welcome message is already in the template, so no need to add it here
    }

    async getNextFlowQuestion(answer = null, stepId = null) {
        const data = {};
        if (answer !== null && stepId !== null) {
            data.answer = answer;
            data.step_id = stepId;
        }

        try {
            const response = await fetch('/api/flow/next-question', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.error) {
                this.showError('flowError', result.error);
                return;
            }

            this.hideError('flowError');

            if (result.summary) {
                this.addMessage('flowMessages', 'bot', result.summary, true);
                // Hide input when summary is shown
                const inputContainer = document.querySelector('.chat-input');
                if (inputContainer) {
                    inputContainer.style.display = 'none';
                }
            } else {
                this.addMessage('flowMessages', 'bot', result.question);
                this.updateProgress(result.step_number, result.total_steps);
                this.currentStepId = result.step_id;
            }

            this.scrollToBottom('flowMessages');
        } catch (error) {
            this.showError('flowError', 'Failed to get next question. Please try again.');
        }
    }

    async sendFlowMessage() {
        const input = document.getElementById('flowInput');
        const message = input.value.trim();

        if (!message) return;

        this.addMessage('flowMessages', 'user', message);
        input.value = '';
        this.setLoading(true);

        try {
            await this.getNextFlowQuestion(message, this.currentStepId);
        } finally {
            this.setLoading(false);
        }
    }

    async sendRagMessage() {
        const input = document.getElementById('ragInput');
        const message = input.value.trim();

        if (!message) return;

        this.addMessage('ragMessages', 'user', message);
        input.value = '';
        this.setLoading(true, 'rag');

        try {
            const response = await fetch('/api/rag/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    history: [] // In a real app, you might want to maintain chat history
                })
            });

            const result = await response.json();

            if (result.error) {
                this.addMessage('ragMessages', 'bot', `Error: ${result.error}`);
            } else {
                this.addMessage('ragMessages', 'bot', result.response);
            }

            this.scrollToBottom('ragMessages');
        } catch (error) {
            this.addMessage('ragMessages', 'bot', 'Sorry, I encountered an error. Please try again.');
        } finally {
            this.setLoading(false, 'rag');
        }
    }

    addMessage(containerId, sender, message, isSummary = false) {
        const container = document.getElementById(containerId);
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = `message-content ${isSummary ? 'summary' : ''}`;
        contentDiv.textContent = message;

        messageDiv.appendChild(contentDiv);
        container.appendChild(messageDiv);
    }

    clearChat(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = '';
        }
    }

    updateProgress(current, total) {
        const progressBar = document.querySelector('.progress');
        const stepInfo = document.querySelector('.step-info');
        
        if (progressBar && stepInfo) {
            const percentage = (current / total) * 100;
            progressBar.style.width = `${percentage}%`;
            stepInfo.textContent = `Step ${current} of ${total}`;
        }
    }

    showError(elementId, message) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    hideError(elementId) {
        const errorElement = document.getElementById(elementId);
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    setLoading(loading, mode = 'flow') {
        const input = mode === 'flow' ? document.getElementById('flowInput') : document.getElementById('ragInput');
        const button = mode === 'flow' ? document.getElementById('sendFlowMessage') : document.getElementById('sendRagMessage');
        
        if (input && button) {
            if (loading) {
                input.disabled = true;
                button.disabled = true;
                button.textContent = 'Sending...';
            } else {
                input.disabled = false;
                button.disabled = false;
                button.textContent = 'Send';
            }
        }
    }

    scrollToBottom(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }
}

// Initialize the chat interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const chatInterface = new ChatInterface();
    
    // Check which page we're on and initialize accordingly
    const currentPath = window.location.pathname;
    
    if (currentPath === '/flow-chat') {
        chatInterface.initializeFlowChat(); // <--- Correct initialization
    } else if (currentPath === '/rag-chat') {
        chatInterface.initializeRagChat(); // <--- Correct initialization
    }
    // If on home page ('/'), no additional initialization needed
});