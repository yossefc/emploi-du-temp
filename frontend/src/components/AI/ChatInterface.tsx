import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, CpuChipIcon, UserIcon } from '@heroicons/react/24/outline';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  suggestions?: string[];
}

interface ChatInterfaceProps {
  onSendMessage: (message: string) => Promise<any>;
  language?: 'fr' | 'he';
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onSendMessage, language = 'fr' }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await onSendMessage(inputValue);
      
      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.message,
        sender: 'ai',
        timestamp: new Date(),
        suggestions: response.suggestions
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: language === 'fr' 
          ? "Désolé, une erreur s'est produite. Veuillez réessayer."
          : "מצטערים, אירעה שגיאה. אנא נסה שוב.",
        sender: 'ai',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputValue(suggestion);
  };

  const placeholderText = language === 'fr'
    ? "Tapez votre message ici..."
    : "הקלד את ההודעה שלך כאן...";

  return (
    <div className="h-full flex flex-col bg-white rounded-lg shadow-md">
      <div className="p-4 bg-indigo-600 text-white rounded-t-lg">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <CpuChipIcon className="w-6 h-6" />
          {language === 'fr' ? 'Assistant IA' : 'עוזר AI'}
        </h3>
      </div>

      <div className="flex-1 overflow-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className="flex flex-col">
            <div
              className={`flex ${
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              } mb-1`}
            >
              <div
                className={`flex gap-2 ${
                  message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
                } items-start max-w-[70%]`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${
                    message.sender === 'user' ? 'bg-green-500' : 'bg-indigo-500'
                  }`}
                >
                  {message.sender === 'user' ? (
                    <UserIcon className="w-4 h-4" />
                  ) : (
                    <CpuChipIcon className="w-4 h-4" />
                  )}
                </div>
                <div
                  className={`p-3 rounded-lg shadow-sm ${
                    message.sender === 'user' 
                      ? 'bg-green-100 text-green-900' 
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  {message.suggestions && (
                    <div className="mt-2 flex gap-1 flex-wrap">
                      {message.suggestions.map((suggestion, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded-full hover:bg-indigo-200 transition-colors cursor-pointer"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-center p-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200">
        <div className="p-4 flex gap-2">
          <input
            type="text"
            className={`flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ${
              language === 'he' ? 'text-right' : 'text-left'
            }`}
            placeholder={placeholderText}
            value={inputValue}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInputValue(e.target.value)}
            onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface; 