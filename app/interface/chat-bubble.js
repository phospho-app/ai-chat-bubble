const styles = `
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: 'Inter', sans-serif; /* Using a modern sans-serif font like Inter */
}

/* Chat Bubble (Floating button) */
.chat-bubble {
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 60px;
    height: 60px;
    background: #3e8ef7;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    z-index: 1000;
}

.chat-bubble:hover {
    transform: scale(1.1);
}

.chat-bubble-icon {
    font-size: 28px;
}

/* Chat Window Modal */
.chat-window {
    position: fixed;
    bottom: 90px;
    right: 20px;
    width: 350px;
    height: 450px;
    background: #1e1e1e;
    border-radius: 16px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
    display: none;
    flex-direction: column;
    z-index: 1000;
    opacity: 0;
    transform: translateY(30px);
    transition: opacity 0.3s ease, transform 0.3s ease;
}

.chat-window.active {
    display: flex;
    opacity: 1;
    transform: translateY(0);
    background: #1e1e1e;
}

/* Header */
.chat-header {
    padding: 16px;
    background: #1e1e1e;
    color: white;
    font-size: 16px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top-left-radius: 16px;
    align-self: flex-end;
    border-top-right-radius: 16px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.close-button {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 18px;
    transition: color 0.3s ease;
}

.close-button:hover {
    color: #3e8ef7;
}

/* Chat Messages Section */
.chat-messages {
    flex-grow: 1;
    padding: 20px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 14px;
    background: #1e1e1e;
}

.message {
    padding: 12px 18px;
    border-radius: 20px;
    max-width: 80%;
    word-wrap: break-word;
    font-size: 14px;
    line-height: 1.4;
}

.message.sent {
    background: #2A2A2A;
    color: white;
    align-self: flex-end;
}

.message.received {
    background: #3e8ef7;
    color: white;
    align-self: flex-start;
}

/* Chat Input Section */
.chat-input {
    display: flex;
    padding: 16px;
    gap: 12px;
    background: #1e1e1e;
}

.message-input {
    flex-grow: 1;
    padding: 12px 18px;
    border: 1px solid #e0e0e0;
    border-radius: 30px;
    outline: none;
    font-size: 14px;
    transition: border-color 0.3s ease;
}

.message-input:focus {
    border-color: #3e8ef7;
}

.send-button {
    background: #3e8ef7;
    color: white;
    border: none;
    border-radius: 30px;
    padding: 0px 16px;
    cursor: pointer;
    transition: background 0.3s ease;
    font-size: 24px;
    align-items: center;
}

.send-button:hover {
    background: #3378d1;
}

.send-button:active {
    background: #2566a0;
}


.phospho-typing-indicator {
  padding: 10px;
  display: flex;
  align-items: center;
}

.typing-dots {
  display: flex;
  align-self: flex-start;
}

.typing-dots span {
  height: 8px;
  width: 8px;
  margin: 0 4px;
  background-color: #3e8ef7;
  display: block;
  border-radius: 50%;
  opacity: 0.4;
  animation: typing 1s infinite ease-in-out;
  align-self: flex-start;
}

.typing-dots span:nth-child(1) {
  animation-delay: 0.1s;
}

.typing-dots span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-dots span:nth-child(3) {
  animation-delay: 0.3s;
}

.highlighted-link {
  text-decoration: underline;
  color: rgb(255, 255, 255);
}

/* Copy button styling */
.copy-btn {
  position: absolute;
  top: 5px;
  right: 5px;
  background-color: #444;
  color: #e6e6e6;
  border: none;
  border-radius: 3px;
  padding: 2px 5px;
  font-size: 12px;
  cursor: pointer;
}

.copy-btn:hover {
  background-color: #555;
}


/* Code block styling */
pre {
  background-color: #2b2b2b;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 10px;
  overflow-x: auto;
  position: relative;
}

code {
  font-family: 'Courier New', Courier, monospace;
  font-size: 14px;
  color: #2b2b2b;
}

/* Inline code styling */
p code {
  background-color: #2c2f33;
  color: #e6e6e6;
  padding: 2px 4px;
  border-radius: 3px;
}

/* Fade In Animation */
.chat-window.fade-in {
    animation: fadeIn 0.3s forwards;
}

@media (max-width: 767px) {
  .chat-window {
    width: 100%;
    height: 100%;
    border-radius: 0;
    bottom: 0;
    right: 0;
  }

  .chat-messages {
    max-height: 70%;
  }

  .chat-input {
    flex-wrap: wrap;
  }

  .message-input {
    flex-grow: 1;
    width: 100%;
  }

  .send-button {
    margin-top: 12px;
    font-size: 40px;
  }
}

@keyframes typing {
  0% {
    transform: translateY(0px);
    background-color: #0000ff;
  }
  28% {
    transform: translateY(-7px);
    background-color: #3e8ef7;
  }
  44% {
    transform: translateY(0px);
    background-color: #0000ff;
  }
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}`;


const apiUrl = `${process.env.SERVER_URL}/question_on_url`;

// Create and inject stylesheet
const styleSheet = document.createElement("style");
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);

// Create chat elements
const chatBubble = document.createElement("div");
chatBubble.className = "chat-bubble";
chatBubble.innerHTML = '<span class="chat-bubble-icon">💬</span>';
document.body.appendChild(chatBubble);

const chatWindow = document.createElement("div");
chatWindow.className = "chat-window";
chatWindow.innerHTML = `
  <div class="chat-header">
    <button class="close-button"></button>
  </div>
  <div class="chat-messages"></div>
  <div class="chat-input">
    <input type="text" class="message-input" placeholder="Type a message...">
    <button class="send-button">↑</button>
  </div>
`;

// Add elements to DOM

document.body.appendChild(chatWindow);

// Get references to elements
const closeButton = chatWindow.querySelector(".close-button");
const messagesContainer = chatWindow.querySelector(".chat-messages");
const messageInput = chatWindow.querySelector(".message-input");
const sendButton = chatWindow.querySelector(".send-button");

// Chat state
let isOpen = false;

addMessage("Hello! How can I assist you today?", false);

// Functions
function toggleChat() {
  isOpen = !isOpen;
  chatWindow.classList.toggle("active", isOpen);
  chatBubble.querySelector(".chat-bubble-icon").textContent = isOpen ? "⌑" : "💬";
  if (isOpen) {
    messageInput.focus();
  }
}

function closeChat() {
  isOpen = false;
  chatBubble.querySelector(".chat-bubble-icon").textContent = isOpen ? "⌑" : "💬";
  chatWindow.classList.remove("active");
}

function addMessage(text, isSent = true) {
  const message = document.createElement("div");
  message.className = `message ${isSent ? "sent" : "received"}`;
  message.textContent = text;
  messagesContainer.appendChild(message);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function updateBotMessage(text) {
  hideTypingIndicator();
  let botMessage = messagesContainer.querySelector(".message.received:last-child");
  if (!botMessage) {
    botMessage = document.createElement('div');
    botMessage.className = 'message received';
    botMessage.innerHTML = '<p></p>';
    messagesContainer.appendChild(botMessage);
  }
  const processedText = processSpecialFormats(text);
  
  botMessage.querySelector('p').innerHTML = processedText;
  addCopyButtons(botMessage);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    hideTypingIndicator(); // Remove any existing indicator first
    const typingIndicator = document.createElement("div");
    typingIndicator.className =
      "message bot typing-indicator";
    typingIndicator.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;
    messagesContainer.appendChild(typingIndicator);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}
  
function hideTypingIndicator() {
  const typingIndicator = messagesContainer.querySelector(
    ".typing-indicator"
  );
  if (typingIndicator) {
    typingIndicator.remove();
  }
}

async function handleSendMessage() {
  const text = messageInput.value.trim();
  if (text) {
    addMessage(text, true);
    messageInput.value = "";
    showTypingIndicator();

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: text }),
      });

      if (response.ok) {
        // Check if the response is a StreamingResponse (ReadableStream)
        if (response.body instanceof ReadableStream) {
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let receivedText = '';

          // Function to read chunks from the stream
          const readStream = async () => {
            const { done, value } = await reader.read();
            if (done) {
              hideTypingIndicator();
              return; // Done reading the stream
            }
            receivedText += decoder.decode(value, { stream: true });  // Append the chunk
            console.log("receivedText", receivedText);
            updateBotMessage(receivedText); // Update the bot message with the new chunk
            readStream(); // Continue reading the next chunk
          };

          await readStream(); // Start reading the stream
        } else {
          hideTypingIndicator();
          console.error("Error: Response is not a StreamingResponse");
        }
      } else {
        hideTypingIndicator();
        console.error("Error with the request:", response.statusText);
      }
    } catch (error) {
      hideTypingIndicator();
      console.error("Error:", error);
    }
  }
}

function processSpecialFormats(text) {
  // Process code blocks
  text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<pre><code class="language-${lang || ''}">${escapeHtml(code.trim())}</code></pre>`;
  });

  // Process inline code
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

  // Process LaTeX
  text = text.replace(/\$\$([\s\S]*?)\$\$/g, (match, latex) => {
    return `<div class="latex-container">${latex}</div>`;
  });

  // Simple Markdown-like parsing
  text = text
    // Headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Lists
    .replace(/^\s*\n\*/gm, '<ul>\n*')
    .replace(/^(\*\s.*)\n([^\*])/gm, '$1\n</ul>\n\n$2')
    .replace(/^\*\s(.*)/gm, '<li>$1</li>')
    // Links
    .replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" class="highlighted-link" target="_blank">$1</a>')
    // Paragraphs
    .replace(/^\s*(\n)?(.+)/gm, function(m) {
      return /\<(\/)?(h\d|ul|ol|li|blockquote|pre|img)/.test(m) ? m : '<p>'+m+'</p>';
    });

  return text;
}

function escapeHtml(unsafe) {
  return unsafe
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function addCopyButtons(container) {
  const codeBlocks = container.querySelectorAll('pre');
  codeBlocks.forEach((block) => {
    if (!block.querySelector('.copy-btn')) {
      const copyBtn = document.createElement('button');
      copyBtn.textContent = 'Copy';
      copyBtn.className = 'copy-btn';
      copyBtn.addEventListener('click', () => {
        const code = block.querySelector('code').textContent;
        navigator.clipboard.writeText(code).then(() => {
          copyBtn.textContent = 'Copied!';
          setTimeout(() => {
            copyBtn.textContent = 'Copy';
          }, 2000);
        });
      });
      block.appendChild(copyBtn);
    }
  });
}

// Event listeners
chatBubble.addEventListener("click", toggleChat);
closeButton.addEventListener("click", closeChat);
sendButton.addEventListener("click", handleSendMessage);

messageInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    handleSendMessage();
  }
});

// Close chat when clicking outside
document.addEventListener("click", (e) => {
  if (
    isOpen &&
    !chatWindow.contains(e.target) &&
    !chatBubble.contains(e.target)
  ) {
    closeChat();
  }
});

