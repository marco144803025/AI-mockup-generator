import React, { useState, useEffect, useRef } from 'react';
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
  const messagesEndRef = useRef(null);

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
      text: "Hello! I'm here to help you build UI mockups using our advanced multi-agent system. Please select a category below to get started with your UI mockup creation.",
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
        
        // Fallback to default categories if API fails
        console.log("Using fallback categories...");
        setCategories(['landing', 'login', 'signup', 'profile', 'about', 'portfolio']);
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
      
      // Fallback to default categories if network error
      console.log("Using fallback categories due to network error...");
      setCategories(['landing', 'login', 'signup', 'profile', 'about', 'portfolio']);
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
      text: `I want to build a ${category} UI mockup.`,
      sender: "user",
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages(prevMessages => [...prevMessages, userMessage]);

    // Multi-agent system is activated silently

    // Create predefined prompt for the orchestrator
    const predefinedPrompt = `I want to create a ${category} UI mockup.  Fetch the templates from the database from mongoDB, the . Use the currently available template that suits the user's request the most then further modify it as user requests.`;
    
    // Send to multi-agent system with the predefined prompt
    await sendToMultiAgent(predefinedPrompt);
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
      text: "Hello! I'm here to help you build UI mockups. Please select a category below to get started with your UI mockup creation.",
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
      await sendToMultiAgent(inputMessage);
    } else {
      await sendToClaude(inputMessage);
    }
  };

  const sendToMultiAgent = async (message) => {
    try {
      const requestData = {
        message: message,
        session_id: sessionId,
        context: {
          selected_category: selectedCategory,
          current_phase: selectedCategory ? "requirements_gathering" : "initial",
          user_intent: "create_ui_mockup",
          category_type: selectedCategory,
          project_type: "ui_mockup_generation"
        }
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

  const sendToClaude = async (prompt) => {
    try {
      // Add database constraints context if we have a selected category
      let enhancedPrompt = prompt;
      if (selectedCategory) {
        // Get category-specific constraints from backend
        try {
          const constraintsResponse = await fetch(`http://localhost:8000/api/templates/category-constraints/${selectedCategory}`);
          if (constraintsResponse.ok) {
            const constraints = await constraintsResponse.json();
            enhancedPrompt = `Context: The user wants to build a ${selectedCategory} UI mockup. 

CATEGORY-SPECIFIC CONSTRAINTS for "${selectedCategory}":
- Available Templates: ${constraints.templates_count} templates
- Available Design Tags for this category: ${constraints.category_tags.join(', ')}
- Available Styles: ${constraints.styles.join(', ')}
- Available Features: ${constraints.features.join(', ')}

IMPORTANT: Only suggest design elements that exist for ${selectedCategory} pages. If the user requests something not available for this category, suggest the closest alternative from the available options above.

User Request: ${prompt}

Please respond as a helpful UI design assistant, asking questions within these ${selectedCategory}-specific constraints.`;
          } else {
            // Fallback to general constraints
            enhancedPrompt = `Context: The user wants to build a ${selectedCategory} UI mockup. 

Database Constraints - You can ONLY work with these available options:
- Available Categories: profile, sign-up, signup, login, About me, landing
- Available Design Tags: modern, minimal, dark theme, light theme, colorful, clean, professional, user-friendly, interactive, sleek design, flat design, card-based, minimalist aesthetic, modern dark, tech, bold typography, social authentication, user registration, form-centric, dashboard, analytics, portfolio, business, SaaS, community, networking, gallery, hero section, call-to-action, and many more...

IMPORTANT: Only suggest categories and design elements that exist in the database. If the user requests something not available, suggest the closest alternative from the available options.

User Request: ${prompt}

Please respond as a helpful UI design assistant, asking questions within these database constraints.`;
          }
        } catch (error) {
          console.error("Error fetching category constraints:", error);
          // Fallback to general constraints
          enhancedPrompt = `Context: The user wants to build a ${selectedCategory} UI mockup. 

Database Constraints - You can ONLY work with these available options:
- Available Categories: profile, sign-up, signup, login, About me, landing
- Available Design Tags: modern, minimal, dark theme, light theme, colorful, clean, professional, user-friendly, interactive, sleek design, flat design, card-based, minimalist aesthetic, modern dark, tech, bold typography, social authentication, user registration, form-centric, dashboard, analytics, portfolio, business, SaaS, community, networking, gallery, hero section, call-to-action, and many more...

IMPORTANT: Only suggest categories and design elements that exist in the database. If the user requests something not available, suggest the closest alternative from the available options.

User Request: ${prompt}

Please respond as a helpful UI design assistant, asking questions within these database constraints.`;
        }
      }
      
      const response = await fetch("http://localhost:8000/api/claude", {
        method: "POST",
        headers: {"Content-Type": "application/json" },
        body: JSON.stringify({prompt: enhancedPrompt, model: "claude-3-5-haiku-20241022"})
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
        <h1>AI UI Mockup Generator</h1>
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
                {useMultiAgent ? "Multi-agent system is processing..." : "AI is thinking..."}
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
              Select Your UI Mockup Category
            </h3>
            <p className="text-gray-600 mb-6 text-center">
              Choose a category to start building your UI mockup with our multi-agent system
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