import React from "react";

function ChatScreen() {
  const [messages, setMessages] = React.useState(() => {
    const cached = localStorage.getItem("chatMessages");
    return cached ? JSON.parse(cached) : [];
  });
  const [inputText, setInputText] = React.useState("");
  const [uploading, setUploading] = React.useState(false);
  const [categories, setCategories] = React.useState([]);
  const [showCategorySelection, setShowCategorySelection] = React.useState(false);
  const [selectedCategory, setSelectedCategory] = React.useState(null);
  const [projectState, setProjectState] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [aiAskedForCategory, setAiAskedForCategory] = React.useState(false);
  const chatContainerRef = React.useRef(null);
  const fileInputRef = React.useRef(null);

  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  React.useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  // Fetch categories on component mount and show initial AI message
  React.useEffect(() => {
    fetchCategories();
    // Show initial AI message asking for category
    const initialMessage = {
      id: Date.now(),
      text: "Hello! I'm here to help you build UI mockups. What type of UI mockup would you like to create?",
      sender: "ai",
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages([initialMessage]);
    setAiAskedForCategory(true);
  }, []);

  const fetchCategories = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/templates/categories");
      if (response.ok) {
        const data = await response.json();
        setCategories(data.categories || []);
      } else {
        console.error("Failed to fetch categories");
      }
    } catch (error) {
      console.error("Error fetching categories:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setShowCategorySelection(false);
    setAiAskedForCategory(false);
    
    // Add user message showing category selection
    const userMessage = {
      id: Date.now(),
      text: `I want to build a ${category} UI mockup.`,
      sender: "user",
      timestamp: new Date().toLocaleTimeString()
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    
    // Let the AI agent take over with the category information
    sendToClaude(`The user wants to build a ${category} UI mockup. Please help them with their requirements.`);
  };



  const resetToCategorySelection = () => {
    setShowCategorySelection(false);
    setSelectedCategory(null);
    setProjectState(null);
    setAiAskedForCategory(true);
    // Reset to initial AI message
    const initialMessage = {
      id: Date.now(),
      text: "Hello! I'm here to help you build UI mockups. What type of UI mockup would you like to create?",
      sender: "ai",
      timestamp: new Date().toLocaleTimeString()
    };
    setMessages([initialMessage]);
  };

  const handleSendMessage = async () => {
    console.log("handleSendMessage called. inputText:", inputText);
    // Prevent sending if AI hasn't asked for category yet or if category selection is shown
    if (aiAskedForCategory || showCategorySelection) {
      return;
    }
    
    if (inputText.trim() !== "") {
      if (inputText.trim().toLowerCase() === "upload image") {
        console.log("Triggering image upload pop-up");
        setInputText("");
        return;
      }

      const newMessage = {
        id: Date.now(),
        text: inputText,
        sender: "user",
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages([...messages, newMessage]);
      setInputText("");

      // Regular chat with Claude
      await sendToClaude(inputText);
    }
  };

  const startMultiAgentProject = async (userPrompt) => {
    try {
      setLoading(true);
      
      const requestData = {
        project_name: `Project_${Date.now()}`,
        user_prompt: userPrompt,
        logo_image: null // TODO: Add logo upload support
      };

      const response = await fetch("http://localhost:8001/project/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data = await response.json();
        setProjectState(data);
        
        const aiMessage = {
          id: Date.now() + 0.5,
          text: `🎯 Project started! Our AI agents are analyzing your requirements for a ${selectedCategory} website.\n\n${data.message || 'Processing your request...'}`,
          sender: "ai",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prevMessages => [...prevMessages, aiMessage]);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to start project");
      }
    } catch (error) {
      console.error("Error starting project:", error);
      const aiMessage = {
        id: Date.now() + 0.5,
        text: `❌ Error: ${error.message}. Falling back to regular chat.`,
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
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !aiAskedForCategory && !showCategorySelection) {
      handleSendMessage();
    }
  };

  const handleImageButtonClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = null; // reset file input
      fileInputRef.current.click();
    }
  };

  const handleImageUpload = async (e) => {
    // Prevent image upload if AI hasn't asked for category yet or if category selection is shown
    if (aiAskedForCategory || showCategorySelection) {
      return;
    }
    
    const file = e.target.files[0];
    if (file && file.type.startsWith("image/")) {
      setUploading(true);
      const reader = new FileReader();
      reader.onload = async (event) => {
        const base64Image = event.target.result;
        const newMessage = {
          id: Date.now(),
          image: base64Image,
          sender: "user",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages((prev) => [...prev, newMessage]);
        // setShowImagePrompt(false); // Removed
        // Send image to backend
        try {
          const response = await fetch("http://localhost:8000/api/claude", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: base64Image, model: "claude-3-5-haiku-20241022" })
          });
          if (response.ok) {
            const data = await response.json();
            const aiMessage = {
              id: Date.now() + 0.5,
              text: data.response,
              sender: "ai",
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages((prev) => [...prev, aiMessage]);
          } else {
            const data = await response.json();
            const aiMessage = {
              id: Date.now() + 0.5,
              text: data.detail ? `Error: ${data.detail}` : "Error: Failed to get response from AI.",
              sender: "ai",
              timestamp: new Date().toLocaleTimeString()
            };
            setMessages((prev) => [...prev, aiMessage]);
          }
        } catch (error) {
          const aiMessage = {
            id: Date.now() + 0.5,
            text: "Error: Unable to connect to backend.",
            sender: "ai",
            timestamp: new Date().toLocaleTimeString()
          };
          setMessages((prev) => [...prev, aiMessage]);
        } finally {
          setUploading(false);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  // Category Selection UI
  if (showCategorySelection) {
    return (
      <div className="flex flex-col h-full p-8 bg-gradient-to-br from-blue-50 to-purple-100 min-h-screen">
        <h1 className="text-3xl font-extrabold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-500 drop-shadow-lg tracking-tight">AI UI Workflow</h1>
        
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Choose Your Website Category</h2>
          <p className="text-lg text-gray-600">Select the type of website you want to create</p>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="max-w-md mx-auto">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden">
              {categories.map((category, index) => (
                <div key={category}>
                  <button
                    onClick={() => handleCategorySelect(category)}
                    className="w-full px-6 py-4 text-left hover:bg-gray-50 transition-colors duration-200 focus:outline-none focus:bg-blue-50"
                  >
                    <span className="text-lg font-medium text-gray-800 capitalize">
                      {category}
                    </span>
                  </button>
                  {index < categories.length - 1 && (
                    <div className="border-b border-gray-200"></div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Regular Chat UI
  return (
    <div className="flex flex-col h-full p-8 bg-gradient-to-br from-blue-50 to-purple-100 min-h-screen">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-500 drop-shadow-lg tracking-tight">
          AI UI Workflow - {selectedCategory}
        </h1>
        <button
          onClick={resetToCategorySelection}
          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
        >
          Restart
        </button>
      </div>
      
      <div 
        ref={chatContainerRef}
        className="flex-1 bg-white/80 rounded-2xl p-6 mb-6 overflow-y-auto shadow-xl border border-blue-100 backdrop-blur-lg"
        style={{ minHeight: 400 }}
      >
        {messages.length === 0 ? (
          <div className="text-gray-400 text-center mt-16 text-lg font-medium animate-fade-in">No messages yet. Start a conversation!</div>
        ) : (
          <div className="space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-5 py-3 rounded-2xl shadow-md transition-all duration-300 ${
                    message.sender === "user"
                      ? "bg-gradient-to-r from-blue-400 to-blue-600 text-white rounded-br-none"
                      : "bg-white text-gray-800 rounded-bl-none border border-blue-100"
                  }`}
                >
                  {message.image ? (
                    <img src={message.image} alt="uploaded" className="max-w-full max-h-60 rounded-xl mb-2 border-2 border-blue-200 shadow-lg" />
                  ) : (
                    <div className="text-base leading-relaxed whitespace-pre-line">{message.text}</div>
                  )}
                  <div className={`text-xs mt-2 ${message.sender === "user" ? "text-blue-100" : "text-gray-400"}`}>
                    {message.timestamp}
                  </div>
                </div>
              </div>
            ))}
            {uploading && (
              <div className="flex justify-center mt-4">
                <div className="flex items-center gap-2 bg-blue-100 px-4 py-2 rounded-xl shadow animate-pulse">
                  <svg className="w-5 h-5 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
                  <span className="font-medium text-blue-700">Uploading image...</span>
                </div>
              </div>
            )}
            
            {/* Show category selection button when AI asks for category */}
            {aiAskedForCategory && !showCategorySelection && (
              <div className="flex justify-center mt-4">
                <button
                  onClick={() => setShowCategorySelection(true)}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-xl font-medium shadow-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-200"
                >
                  Choose Category
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="flex gap-3 mt-2 items-center">
        <input
          className={`flex-1 border-2 rounded-xl p-4 focus:outline-none focus:ring-2 text-lg shadow transition-all duration-200 ${
            aiAskedForCategory || showCategorySelection
              ? 'border-gray-300 bg-gray-100 text-gray-500 cursor-not-allowed' 
              : 'border-blue-200 focus:ring-blue-400 bg-white/90'
          }`}
          placeholder={aiAskedForCategory || showCategorySelection ? "Please select a category first..." : "Type your message..."}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={aiAskedForCategory || showCategorySelection}
        />
        <button
          onClick={handleSendMessage}
          disabled={aiAskedForCategory || showCategorySelection}
          className={`px-8 py-4 rounded-xl font-bold text-lg shadow-lg transition-all duration-200 ${
            aiAskedForCategory || showCategorySelection
              ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-500 to-purple-500 text-white hover:from-blue-600 hover:to-purple-600'
          }`}
        >
          Send
        </button>
        <button
          onClick={handleImageButtonClick}
          disabled={aiAskedForCategory || showCategorySelection}
          className={`flex items-center gap-2 border-2 px-5 py-4 rounded-xl font-bold text-lg shadow transition-all duration-200 ${
            aiAskedForCategory || showCategorySelection
              ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed'
              : 'bg-white border-blue-300 text-blue-700 hover:bg-blue-50 hover:border-blue-400'
          }`}
          title="Upload Image"
        >
          <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2M7 10l5 5m0 0l5-5m-5 5V4" /></svg>
          Upload Image
        </button>
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          style={{ display: "none" }}
          onChange={handleImageUpload}
        />
      </div>
    </div>
  );
}



export default ChatScreen; 