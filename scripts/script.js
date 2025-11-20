document.addEventListener('DOMContentLoaded', () => {
    const chatIcon = document.getElementById('chat-icon');
    const chatWindow = document.getElementById('chat-window');
    const closeChatBtn = document.getElementById('close-chat-btn');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const chatMessages = document.getElementById('chat-messages');

    // Function to toggle chat window visibility
    function toggleChat() {
        chatWindow.classList.toggle('hidden');
        chatIcon.classList.toggle('hidden'); // Hide icon when window is open
    }

    // Event listeners for opening and closing chat
    chatIcon.addEventListener('click', toggleChat);
    closeChatBtn.addEventListener('click', toggleChat);

    // Function to add a message to the chat window
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
        messageDiv.innerHTML = `<p>${message}</p>`;
        chatMessages.appendChild(messageDiv);
        // Scroll to the latest message
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to handle sending a message
    function sendMessage() {
        const userMessage = chatInput.value.trim();
        if (userMessage) {
            addMessage(userMessage, 'user');
            chatInput.value = ''; // Clear input field

            // Simulate bot response (you would integrate with a real bot here)
            setTimeout(() => {
                addMessage("Thanks for your message! We'll get back to you shortly.", 'bot');
            }, 1000);
        }
    }

    // Event listeners for sending messages
    sendChatBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Ensure the chat icon is visible on page load if the window is closed
    if (chatWindow.classList.contains('hidden')) {
        chatIcon.classList.remove('hidden');
    } else {
        chatIcon.classList.add('hidden');
    }
});