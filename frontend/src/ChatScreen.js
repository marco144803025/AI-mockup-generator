import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './ChatScreen.css';
import DebugPanel from './DebugPanel';

function ChatScreen() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showCategorySelection, setShowCategorySelection] = useState(true);
  const [aiAskedForCategory, setAiAskedForCategory] = useState(true);
  const [sessionId, setSessionId] = useState(null);
  const [useMultiAgent, setUseMultiAgent] = useState(false);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [showDebugPanel, setShowDebugPanel] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [phase, setPhase] = useState('phase1'); // 'phase1' or 'phase2'
  const messagesEndRef = useRef(null);
  const navigate = useNavigate();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    fetchCategories();
    // Initialize with AI greeting asking for category
    const initialMessage = {
      id: Date.now(),
      text: "Hello! I'm here to help you build UI. Please select a category below to get started.",
      sender: "ai",
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages([initialMessage]);
    setAiAskedForCategory(true);
    setShowCategorySelection(true);
  }, []);

  const fetchCategories = async () => {
    try {
      setCategoriesLoading(true);
      console.log("Fetching categories from backend...");
      const response = await fetch("http://localhost:8000/api/templates/categories", {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });
      console.log("Response status:", response.status);
      
      if (response.ok) {
        const data = await response.json();
        console.log("Categories data:", data);
        setCategories(data.categories);
        console.log("Categories set:", data.categories);
      } else {
        console.error("Failed to fetch categories:", response.status, response.statusText);
        const errorText = await response.text();
        console.error("Error response:", errorText);
        
        // No fallback - let the user know the API is unavailable
        console.log("API unavailable - no categories loaded");
        setCategories([]);
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
      
      // No fallback - let the user know the network is unavailable
      console.log("Network error - no categories loaded");
      setCategories([]);
    } finally {
      setCategoriesLoading(false);
    }
  };

  const handleCategorySelect = async (category) => {
    setSelectedCategory(category);
    setShowCategorySelection(false);
    setAiAskedForCategory(false);
    setUseMultiAgent(true);
    setLoading(true);

    // Add user message
    const userMessage = {
      id: Date.now(),
      text: `I want to build a ${category} UI.`,
      sender: "user",
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);


    await sendToMultiAgent(`I want to build a ${category} UI.`, userMessage);
  };

  const resetToCategorySelection = async () => {
    // First, reset the backend session
    try {
      const response = await fetch("http://localhost:8000/api/session/reset", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      
      if (response.ok) {
        console.log("Backend session reset successful");
      } else {
        console.error("Failed to reset backend session:", response.status);
      }
    } catch (error) {
      console.error("Error resetting backend session:", error);
    }
    
    // Then reset frontend state
    setMessages([]);
    setSelectedCategory(null);
    setShowCategorySelection(true);
    setAiAskedForCategory(true);
    setSessionId(null);
    setUseMultiAgent(false);
    
    // Initialize with AI greeting
    const initialMessage = {
      id: Date.now(),
      text: "Hello! I'm here to help you build UI. Please select a category below to get started.",
      sender: "ai",
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages([initialMessage]);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: "user",
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prevMessages => [...prevMessages, userMessage]);
    setInputMessage('');
    setLoading(true);

    if (useMultiAgent) {
      await sendToMultiAgent(inputMessage, userMessage);
    } else {
      await sendToClaude(inputMessage);
    }
  };

  const sendToMultiAgent = async (message, userMessage) => {
    try {
      const requestData = {
        message: message,
        session_id: sessionId
      };

      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Update session ID if provided
        if (data.session_id) {
          console.log('ChatScreen: Setting sessionId to:', data.session_id);
          setSessionId(data.session_id);
        }

        const aiMessage = {
          id: Date.now() + 0.5,
          text: data.response,
          sender: "ai",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prevMessages => [...prevMessages, aiMessage]);

        // Handle any actions from the orchestrator
        if (data.actions) {
          for (const action of data.actions) {
            if (action.action === "set_category" && action.success) {
              setSelectedCategory(action.data.category);
            }
            // Log other actions for debugging
            if (action.action !== "set_category") {
              console.log("Orchestrator action:", action);
            }
          }
        }

        // Check for phase transition signal from orchestrator
        console.log('Checking for transition data:', data.transition_data);
        console.log('Checking for intent:', data.intent);
        console.log('Full response data:', data);
        
        if (data.transition_data && data.intent === "phase_transition") {
          console.log('Phase transition detected! Navigating to editor...');
          
          // Create the complete conversation history including the latest messages
          const completeHistory = [
            ...messages,
            userMessage, // Include the user message that was just sent
            {
              id: Date.now() + 0.5,
              text: data.response,
              sender: "ai",
              timestamp: new Date().toLocaleTimeString()
            }
          ];
          
          console.log('Saving complete chat history to localStorage:', completeHistory);
          console.log('History length:', completeHistory.length);
          console.log('Last user message:', userMessage);
          console.log('Last AI message:', data.response);
          
          // Save conversation history to localStorage
          localStorage.setItem('phase1ChatHistory', JSON.stringify(completeHistory));
          
          // Navigate to editor page with transition data
          navigate('/editor', { 
            state: data.transition_data
          });
        } else {
          console.log('No phase transition detected. Intent:', data.intent, 'Transition data:', data.transition_data);
        }

        // Log session state for debugging
        if (data.session_state) {
          console.log("Session state:", data.session_state);
        }

        // Validation results are handled internally by the system
        // No need to display them to the user

      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to get response");
      }
    } catch (error) {
      console.error("Error sending message:", error);
      const aiMessage = {
        id: Date.now() + 0.5,
        text: `Error: ${error.message}. Please try again.`,
        sender: "ai",
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prevMessages => [...prevMessages, aiMessage]);
    } finally {
      setLoading(false);
    }
  };

  const checkForTemplateSelection = async (userMessage, aiResponse) => {
    // This function is no longer needed - the orchestrator handles everything
    console.log('Template selection handled by orchestrator');
  };

  const getSelectedTemplateFromSession = async () => {
    // This function is no longer needed - the orchestrator handles everything
    return null;
  };

  const transitionToPhase2 = async (selectedTemplate) => {
    // This function is no longer needed - the orchestrator handles everything
    console.log('Transition handled by orchestrator');
  };

  const sendToClaude = async (prompt) => {
    try {
      const response = await fetch("http://localhost:8000/api/claude", {
        method: "POST",
        headers: {"Content-Type": "application/json" },
        body: JSON.stringify({prompt: prompt, model: "claude-3-5-haiku-20241022"})
      });
      if (response.ok) {
        const data = await response.json();
        const aiMessage = {
          id: Date.now() + 0.5,
          text: data.response,
          sender: "ai",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prevMessages => [...prevMessages, aiMessage]);
      } else {
        const data = await response.json();
        const aiMessage = {
          id: Date.now() + 0.5,
          text: data.detail ? `Error: ${data.detail}` : "Error: Failed to get response from AI.",
          sender: "ai",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prevMessages => [...prevMessages, aiMessage]);
      }
    } catch (error) {
      const aiMessage = {
        id: Date.now() + 0.5,
        text: "Error: Unable to connect to backend.",
        sender: "ai",
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prevMessages => [...prevMessages, aiMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleImageButtonClick = () => {
    document.getElementById('imageInput').click();
  };

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Handle image upload logic here
    console.log("Image uploaded:", file.name);
  };

  return (
    <div className="chat-screen">
      <div className="chat-header">
        <h1>AI UI Generator</h1>
        <div className="header-buttons">
          <button
            onClick={() => setShowDebugPanel(!showDebugPanel)}
            className="debug-button"
            title="Toggle Debug Panel"
          >
            🐛 Debug
          </button>
          <button
            onClick={() => resetToCategorySelection()}
            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
          >
            Restart
          </button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${
              message.sender === "user" 
                ? "user-message" 
                : message.sender === "system" 
                  ? "system-message" 
                  : "ai-message"
            }`}
          >
            <div className="message-content">
              {message.text}
            </div>
            <div className="message-timestamp">{message.timestamp}</div>
          </div>
        ))}
        {loading && (
          <div className="message ai-message">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div className="text-sm text-gray-500 mt-2">
                {"Processing..."}
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {aiAskedForCategory && showCategorySelection && (
        <div className="category-selection">
          <div className="max-w-2xl mx-auto p-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4 text-center">
              Select Your UI Category
            </h3>
            <p className="text-gray-600 mb-6 text-center">
                              Choose a category to start building your UI
            </p>
            <div className="text-center mb-4">
              <p className="text-sm text-gray-500">
                Available categories: {categories.length > 0 ? categories.join(', ') : 'Loading...'}
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {categories.length > 0 ? (
                categories.map((category, index) => (
                  <div key={category} className="bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200 hover:shadow-xl transition-shadow duration-300">
                    <button
                      onClick={() => handleCategorySelect(category)}
                      className="w-full px-6 py-6 text-left hover:bg-blue-50 transition-colors duration-200 focus:outline-none focus:bg-blue-50 focus:ring-2 focus:ring-blue-500"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-lg font-medium text-gray-800 capitalize">
                          {category}
                        </span>
                        <span className="text-blue-500 text-2xl">→</span>
                      </div>
                      <p className="text-sm text-gray-500 mt-2">
                        Create a {category} interface mockup
                      </p>
                    </button>
                  </div>
                ))
              ) : (
                <div className="col-span-2 text-center py-8">
                  <div className="text-gray-500">
                    <p>Loading categories...</p>
                    <p className="text-sm mt-2">If this persists, please check the backend connection.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="chat-input">
        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={aiAskedForCategory || showCategorySelection}
            className="message-input"
          />
          <div className="input-buttons">
            <button
              onClick={handleImageButtonClick}
              disabled={aiAskedForCategory || showCategorySelection}
              className="image-button"
              title="Upload Image"
            >
              Image
            </button>
            <input
              id="imageInput"
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              style={{ display: 'none' }}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || loading || aiAskedForCategory || showCategorySelection}
              className="send-button"
            >
              Send
            </button>
          </div>
        </div>
      </div>
      
      <DebugPanel 
        sessionId={sessionId}
        isVisible={showDebugPanel}
        onClose={() => setShowDebugPanel(false)}
      />
    </div>
  );
}

export default ChatScreen; 