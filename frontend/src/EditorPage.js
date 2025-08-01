import React, { useState, useEffect, useRef } from 'react';

function EditorPage() {
  const [viewMode, setViewMode] = useState('preview'); // 'preview' or 'code'
  const [uiCodes, setUiCodes] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Chat state management
  const [chatMessages, setChatMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef(null);

  // Load chat history from localStorage on component mount
  useEffect(() => {
    const savedMessages = localStorage.getItem('editorChatHistory');
    if (savedMessages) {
      try {
        setChatMessages(JSON.parse(savedMessages));
      } catch (e) {
        console.error('Error loading chat history:', e);
        // Initialize with default welcome message
        setChatMessages([
          {
            id: Date.now(),
            type: 'ai',
            content: "I'm ready to help you edit your UI! What would you like to change?",
            timestamp: new Date().toISOString()
          }
        ]);
      }
    } else {
      // Initialize with default welcome message
      setChatMessages([
        {
          id: Date.now(),
          type: 'ai',
          content: "I'm ready to help you edit your UI! What would you like to change?",
          timestamp: new Date().toISOString()
        }
      ]);
    }
  }, []);

  // Save chat history to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('editorChatHistory', JSON.stringify(chatMessages));
  }, [chatMessages]);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Fetch UI codes from backend on component mount
  useEffect(() => {
    fetchUICodes();
  }, []);

  const fetchUICodes = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // For now, fetch the default template
      const response = await fetch('http://localhost:8000/api/ui-codes/default');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setUiCodes(data.ui_codes);
      } else {
        throw new Error(data.error || 'Failed to fetch UI codes');
      }
    } catch (err) {
      console.error('Error fetching UI codes:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isSending) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString()
    };

    // Add user message to chat
    setChatMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsSending(true);

    try {
      // Call the AI-powered UI editor chat endpoint
      const chatRequest = {
        message: inputMessage.trim(),
        session_id: "demo_session",
        current_ui_codes: uiCodes
      };

      const response = await fetch('http://localhost:8000/api/ui-editor/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatRequest)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Add AI response to chat
        const aiMessage = {
          id: Date.now() + 1,
          type: 'ai',
          content: data.response,
          timestamp: new Date().toISOString()
        };
        setChatMessages(prev => [...prev, aiMessage]);
        
        // Apply modifications if they exist
        if (data.ui_modifications && data.metadata?.intent === "modification_request") {
          await applyModifications(data.ui_modifications);
        }
      } else {
        throw new Error(data.response || 'Failed to get AI response');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: `Sorry, I encountered an error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const applyModifications = async (modifications) => {
    try {
      // Prepare modification request
      const modificationData = {
        template_id: "default",
        modification_type: modifications.type || "css_change",
        changes: modifications.changes || {},
        session_id: "demo_session"
      };

      // Call the modification endpoint
      const response = await fetch('http://localhost:8000/api/ui-codes/modify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(modificationData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Update the UI codes with the modified version
        setUiCodes(data.updated_codes);
      } else {
        throw new Error(data.message || 'Failed to apply modifications');
      }
    } catch (error) {
      console.error('Error applying modifications:', error);
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `❌ Error applying changes: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleMakeButtonRed = async () => {
    try {
      // Call the backend API to modify the button color
      const modificationData = {
        template_id: "default",
        modification_type: "css_change",
        changes: {
          ".button": {
            "background": "#ff4444",
            "color": "white"
          }
        },
        session_id: "demo_session"
      };

      const response = await fetch('http://localhost:8000/api/ui-codes/modify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(modificationData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Update the UI codes with the modified version
        setUiCodes(data.updated_codes);
        
        // Add success message to chat
        const successMessage = {
          id: Date.now(),
          type: 'ai',
          content: "✅ I've changed the button color to red! Check the preview to see the changes.",
          timestamp: new Date().toISOString()
        };
        setChatMessages(prev => [...prev, successMessage]);
      } else {
        throw new Error(data.message || 'Failed to modify UI');
      }
    } catch (error) {
      console.error('Error modifying button:', error);
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `❌ Error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleResetButton = async () => {
    try {
      // Reset the button to original green color
      const modificationData = {
        template_id: "default",
        modification_type: "css_change",
        changes: {
          ".button": {
            "background": "#4CAF50",
            "color": "white"
          }
        },
        session_id: "demo_session"
      };

      const response = await fetch('http://localhost:8000/api/ui-codes/modify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(modificationData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success) {
        // Update the UI codes with the reset version
        setUiCodes(data.updated_codes);
        
        // Add success message to chat
        const successMessage = {
          id: Date.now(),
          type: 'ai',
          content: "✅ I've reset the button back to green!",
          timestamp: new Date().toISOString()
        };
        setChatMessages(prev => [...prev, successMessage]);
      } else {
        throw new Error(data.message || 'Failed to reset UI');
      }
    } catch (error) {
      console.error('Error resetting button:', error);
      
      // Add error message to chat
      const errorMessage = {
        id: Date.now(),
        type: 'ai',
        content: `❌ Error: ${error.message}`,
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChatHistory = () => {
    setChatMessages([
      {
        id: Date.now(),
        type: 'ai',
        content: "I'm ready to help you edit your UI! What would you like to change?",
        timestamp: new Date().toISOString()
      }
    ]);
  };

  const renderPreview = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading UI preview...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-red-600 mb-4">Error loading preview: {error}</p>
            <button 
              onClick={fetchUICodes}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
            >
              Retry
            </button>
          </div>
        </div>
      );
    }

    if (!uiCodes) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-600">No UI codes available</p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow-lg h-full">
        <iframe 
          id="preview-frame"
          className="w-full h-full border-0 rounded-lg"
          title="UI Preview"
          srcDoc={uiCodes.complete_html}
        />
      </div>
    );
  };

  const renderCode = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading code...</p>
          </div>
        </div>
      );
    }

    if (error || !uiCodes) {
      return (
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-600">No code available</p>
        </div>
      );
    }

    return (
      <div className="bg-white rounded-lg shadow-lg h-full p-4">
        <div className="bg-gray-100 rounded p-4 h-full overflow-auto">
          <pre className="text-sm text-gray-700">
{`// HTML Code (html_export)
${uiCodes.html_export || uiCodes.html || ''}

// Global CSS (globals_css)
${uiCodes.globals_css || ''}

// Style CSS (style_css)
${uiCodes.style_css || uiCodes.css || ''}

// JavaScript Code
${uiCodes.js || ''}`}
          </pre>
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Chat Interface Section */}
      <div className="w-1/3 bg-white border-r border-gray-200 flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold">AI Editor Chat</h2>
            <p className="text-sm text-gray-600">Ask me to modify your UI</p>
          </div>
          <button 
            onClick={clearChatHistory}
            className="text-sm text-gray-500 hover:text-gray-700 px-2 py-1 rounded"
            title="Clear chat history"
          >
            Clear
          </button>
        </div>
        
        {/* Chat Messages Area */}
        <div className="flex-1 p-4 overflow-y-auto">
          {chatMessages.map((message) => (
            <div 
              key={message.id}
              className={`rounded-lg p-3 mb-4 ${
                message.type === 'ai' 
                  ? 'bg-blue-50' 
                  : 'bg-gray-50'
              }`}
            >
              <p className={`text-sm ${
                message.type === 'ai' 
                  ? 'text-blue-800' 
                  : 'text-gray-800'
              }`}>
                <strong>{message.type === 'ai' ? 'AI:' : 'You:'}</strong> {message.content}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))}
          {isSending && (
            <div className="bg-blue-50 rounded-lg p-3 mb-4">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                <p className="text-sm text-blue-800">AI is typing...</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Chat Input */}
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <input 
              type="text" 
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your request here..."
              disabled={isSending}
              className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button 
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isSending}
              className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>

      {/* UI Preview/Code Section */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar with Toggle Buttons */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex space-x-2">
                <button 
                  onClick={() => setViewMode('preview')}
                  className={`px-4 py-2 rounded-lg transition ${
                    viewMode === 'preview' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Preview
                </button>
                <button 
                  onClick={() => setViewMode('code')}
                  className={`px-4 py-2 rounded-lg transition ${
                    viewMode === 'code' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Code
                </button>
              </div>
              <h2 className="text-xl font-bold">UI Editor</h2>
            </div>
            
            {/* Temporary Demo Buttons */}
            <div className="flex space-x-2">
              <button 
                onClick={handleMakeButtonRed}
                className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition"
                title="Demo: Make button red"
              >
                Make Button Red
              </button>
              <button 
                onClick={handleResetButton}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition"
                title="Demo: Reset button to green"
              >
                Reset Button
              </button>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 p-4">
          {viewMode === 'preview' ? renderPreview() : renderCode()}
        </div>
      </div>
    </div>
  );
}

export default EditorPage; 