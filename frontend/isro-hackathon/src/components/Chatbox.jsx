import React, { useState, useRef, useEffect } from 'react'
import { Send, Globe } from 'lucide-react';


function Chatbox() {
  const [messages, setMessages] = useState([
    { id: 1, text: "Welcome to MOSDAC! How can I help you explore our satellite data archive?", sender: 'bot', timestamp: new Date() }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null)

  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate API call to Flask backend
    setTimeout(() => {
      const botMessage = {
        id: messages.length + 2,
        text: "I'm processing your request about satellite data. This would connect to your Flask backend for real responses.",
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botMessage]);
      setIsLoading(false);
    }, 1500);
  };

  return (
    <div className="h-[70vh] flex flex-col bg-slate-800/50 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-500/10 backdrop-blur-sm">
      <div className="p-4 border-b border-cyan-500/30 bg-gradient-to-r from-slate-800/80 to-slate-700/80 rounded-t-xl">
        <h2 className="text-xl font-semibold text-cyan-400 flex items-center space-x-2">
          <Globe className="w-5 h-5" />
          <span>Satellite Data Assistant</span>
        </h2>
      </div>
      
      <div
        className="flex-1 overflow-y-auto p-4 space-y-4"
        style={{
            scrollbarWidth: 'none',
            msOverflowStyle: 'none',
        }}
        ref={messagesContainerRef}
      >
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-500 text-white shadow-lg shadow-cyan-500/25'
                  : 'bg-slate-700/80 text-gray-100 border border-slate-600/50 shadow-lg'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <p className="text-xs mt-1 opacity-60">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-700/80 text-gray-100 px-4 py-2 rounded-lg border border-slate-600/50 shadow-lg">
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <div className="p-4 border-t border-cyan-500/30 bg-slate-800/50 rounded-b-xl">
        <div className="flex space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask about satellite data..."
            className="flex-1 bg-slate-700/80 text-white placeholder-gray-400 px-4 py-2 rounded-lg border border-slate-600/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all duration-300"
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading}
            className="bg-gradient-to-r from-cyan-500 to-blue-500 text-white px-4 py-2 rounded-lg hover:from-cyan-600 hover:to-blue-600 transition-colors duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default Chatbox