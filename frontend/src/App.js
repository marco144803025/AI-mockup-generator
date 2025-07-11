import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import UIRecommendationPage from "./UIRecommendationPage";

function Sidebar() {
  return (
    <div className="h-screen w-55 bg-white text-black flex flex-col p-4 space-y-4">
      <h2 className="text-2xl font-bold mb-8">Launchpad AI</h2>
      <Link to="/" className="hover:bg-purple-200 rounded px-3 py-2">Main Page</Link>
      <Link to="/chat" className="hover:bg-purple-200 rounded px-3 py-2">Chat</Link>
      <Link to="/ui-recommendation" className="hover:bg-purple-200 rounded px-3 py-2">UI Recommendation</Link>
      <Link to="/created" className="hover:bg-purple-200 rounded px-3 py-2">Created</Link>
    </div>
  );
}

function MainPage() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <h1 className="text-3xl font-bold mb-6">Welcome to Launchpad AI</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-xl">
        <Link to="/chat" className="bg-blue-500 text-white rounded-lg p-6 text-center shadow hover:bg-blue-600 transition">Go to Chat</Link>
        <Link to="/ui-recommendation" className="bg-green-500 text-white rounded-lg p-6 text-center shadow hover:bg-green-600 transition">UI Recommendations</Link>
        <Link to="/created" className="bg-purple-500 text-white rounded-lg p-6 text-center shadow hover:bg-purple-600 transition">View Created Pages</Link>
      </div>
    </div>
  );
}

function ChatPage() {
  const [messages, setMessages] = React.useState(() => {
    // Load messages from localStorage if available
    const cached = localStorage.getItem("chatMessages");
    return cached ? JSON.parse(cached) : [];
  });
  const [inputText, setInputText] = React.useState("");
  const [showImagePrompt, setShowImagePrompt] = React.useState(false);
  const chatContainerRef = React.useRef(null);

  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Cache messages to localStorage whenever they change
  React.useEffect(() => {
    localStorage.setItem("chatMessages", JSON.stringify(messages));
  }, [messages]);

  const handleSendMessage = () => {
    if (inputText.trim() !== "") {
      //this is a placeholder for the image upload button, will be replaced with the actual button once AI agent is implemented
      if (inputText.trim().toLowerCase() === "upload image") {
        setShowImagePrompt(true);
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
      //placeholder for ai response
      setTimeout(() => {
        const aiMessage = {
          id: Date.now() + 0.5,
          text: "This is a placeholder AI response.",
          sender: "ai",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prevMessages => [...prevMessages, aiMessage]);
      }, 1000);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSendMessage();
    }
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const newMessage = {
          id: Date.now(),
          image: event.target.result,
          sender: "user",
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages([...messages, newMessage]);
        setShowImagePrompt(false);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="flex flex-col h-full p-8">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>
      <div 
        ref={chatContainerRef}
        className="flex-1 bg-gray-100 rounded-lg p-4 mb-4 overflow-y-auto"
      >
        {messages.length === 0 ? (
          <div className="text-gray-500 text-center mt-8">No messages yet. Start a conversation!</div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender === "user"
                      ? "bg-blue-500 text-white rounded-br-none"
                      : "bg-white text-gray-800 rounded-bl-none border"
                  }`}
                >
                  {message.image ? (
                    <img src={message.image} alt="uploaded" className="max-w-full max-h-48 rounded mb-2" />
                  ) : (
                    <div className="text-sm">{message.text}</div>
                  )}
                  <div className={`text-xs mt-1 ${message.sender === "user" ? "text-blue-100" : "text-gray-500"}`}>
                    {message.timestamp}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {showImagePrompt && (
          <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
            <div className="bg-white p-6 rounded-lg shadow-lg flex flex-col items-center">
              <h2 className="text-lg font-semibold mb-4">Upload an Image</h2>
              <input type="file" accept="image/*" onChange={handleImageUpload} className="mb-4" />
              <button
                onClick={() => setShowImagePrompt(false)}
                className="text-red-500 hover:underline"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Type your message..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <button
          onClick={handleSendMessage}
          className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function CreatedPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Created Pages</h1>
      <div className="bg-gray-100 rounded-lg p-4">No pages created yet.</div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 bg-gray-50 overflow-auto">
          <Routes>
            <Route path="/" element={<MainPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/ui-recommendation" element={<UIRecommendationPage />} />
            <Route path="/created" element={<CreatedPage />} />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;
