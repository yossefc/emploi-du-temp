import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Divider,
  CircularProgress,
  Chip
} from '@mui/material';
import { Send, SmartToy, Person } from '@mui/icons-material';

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
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, backgroundColor: 'primary.main', color: 'white' }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToy />
          {language === 'fr' ? 'Assistant IA' : 'עוזר AI'}
        </Typography>
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {messages.map((message) => (
          <Box key={message.id} sx={{ mb: 2 }}>
            <Box
              sx={{
                display: 'flex',
                justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                mb: 1
              }}
            >
              <Box
                sx={{
                  display: 'flex',
                  gap: 1,
                  flexDirection: message.sender === 'user' ? 'row-reverse' : 'row',
                  alignItems: 'flex-start',
                  maxWidth: '70%'
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: message.sender === 'user' ? 'secondary.main' : 'primary.main',
                    width: 32,
                    height: 32
                  }}
                >
                  {message.sender === 'user' ? <Person /> : <SmartToy />}
                </Avatar>
                <Paper
                  sx={{
                    p: 2,
                    backgroundColor: message.sender === 'user' ? 'secondary.light' : 'grey.100',
                    borderRadius: 2
                  }}
                >
                  <Typography variant="body2">{message.text}</Typography>
                  {message.suggestions && (
                    <Box sx={{ mt: 1, display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {message.suggestions.map((suggestion, index) => (
                        <Chip
                          key={index}
                          label={suggestion}
                          size="small"
                          onClick={() => handleSuggestionClick(suggestion)}
                          sx={{ cursor: 'pointer' }}
                        />
                      ))}
                    </Box>
                  )}
                </Paper>
              </Box>
            </Box>
          </Box>
        ))}
        {isLoading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>

      <Divider />

      <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder={placeholderText}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          disabled={isLoading}
          size="small"
          sx={{ direction: language === 'he' ? 'rtl' : 'ltr' }}
        />
        <IconButton
          color="primary"
          onClick={handleSend}
          disabled={!inputValue.trim() || isLoading}
        >
          <Send />
        </IconButton>
      </Box>
    </Paper>
  );
};

export default ChatInterface; 