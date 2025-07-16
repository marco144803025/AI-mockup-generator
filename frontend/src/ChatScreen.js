import React from "react";

function ChatScreen() {
  const [messages, setMessages] = React.useState(() => {
    const cached = localStorage.getItem("chatMessages");
    return cached ? JSON.parse(cached) : [];
  });
  const [inputText, setInputText] = React.useState("");
  const [uploading, setUploading] = React.useState(false);
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

  const handleSendMessage = async () => {
    console.log("handleSendMessage called. inputText:", inputText);
    if (inputText.trim() !== "") {
      if (inputText.trim().toLowerCase() === "upload image") {
        console.log("Triggering image upload pop-up");
        // setShowImagePrompt(true); // Removed
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
      // response backend LLM API
      try {
        const response = await fetch("http://localhost:8000/api/claude", {
          method: "POST",
          headers: {"Content-Type": "application/json" },
          body: JSON.stringify({ prompt: inputText, model: "claude-3-5-haiku-20241022" })
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
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
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

  return (
    <div className="flex flex-col h-full p-8 bg-gradient-to-br from-blue-50 to-purple-100 min-h-screen">
      <h1 className="text-3xl font-extrabold mb-6 text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-500 drop-shadow-lg tracking-tight">Claude Chat</h1>
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
          </div>
        )}
      </div>
      <div className="flex gap-3 mt-2 items-center">
        <input
          className="flex-1 border-2 border-blue-200 rounded-xl p-4 focus:outline-none focus:ring-2 focus:ring-blue-400 bg-white/90 text-lg shadow"
          placeholder="Type your message..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button
          onClick={handleSendMessage}
          className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-8 py-4 rounded-xl font-bold text-lg shadow-lg hover:from-blue-600 hover:to-purple-600 transition-all duration-200"
        >
          Send
        </button>
        <button
          onClick={handleImageButtonClick}
          className="flex items-center gap-2 bg-white border-2 border-blue-300 text-blue-700 px-5 py-4 rounded-xl font-bold text-lg shadow hover:bg-blue-50 hover:border-blue-400 transition-all duration-200"
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