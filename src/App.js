import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";

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
  const [messages, setMessages] = React.useState([]);
  const [inputText, setInputText] = React.useState("");
  const chatContainerRef = React.useRef(null);

  // Auto-scroll to bottom when messages change
  React.useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (inputText.trim() !== "") {
      const newMessage = {
        id: Date.now(),
        text: inputText,
        sender: "user",
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages([...messages, newMessage]);
      setInputText("");
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSendMessage();
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
                  <div className="text-sm">{message.text}</div>
                  <div className={`text-xs mt-1 ${message.sender === "user" ? "text-blue-100" : "text-gray-500"}`}>
                    {message.timestamp}
                  </div>
                </div>
              </div>
            ))}
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

function UIRecommendationPage() {
  // Placeholder images, replace with real UI recommendations later
  const images = [
    "https://via.placeholder.com/300x180?text=UI+1",
    "https://via.placeholder.com/300x180?text=UI+2",
    "https://via.placeholder.com/300x180?text=UI+3",
    "https://via.placeholder.com/300x180?text=UI+4",
  ];
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">UI Recommendations</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {images.map((src, idx) => (
          <div key={idx} className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer">
            <img src={src} alt={`UI ${idx + 1}`} className="rounded-t-lg w-full h-40 object-cover" />
            <div className="p-4 text-center">UI Template {idx + 1}</div>
          </div>
        ))}
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
