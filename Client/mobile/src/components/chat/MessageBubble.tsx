import React from 'react';
import { View, Text, Image } from 'react-native';
import { ChatMessage } from '@/stores/useChatStore';
import { RecoveryActivityCards } from './RecoveryActivityCards';

interface MessageBubbleProps {
  message: ChatMessage;
  showTimestamp?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  showTimestamp = false,
}) => {
  const isUser = message.sender === 'user';

  return (
    <View className="my-1.5 px-4">
      {showTimestamp && (
        <View className="items-center mb-2 mt-1">
          <Text className="text-xs text-[#6B7280] font-medium">
            {message.timestamp}
          </Text>
        </View>
      )}

      <View
        className={`flex-row items-end ${
          isUser ? 'justify-end' : 'justify-start'
        }`}
      >
        {/* Coach Avatar */}
        {!isUser && (
          <Image
            source={{
              uri: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80',
            }}
            className="w-8 h-8 rounded-full mr-2 mb-1"
          />
        )}

        <View className="max-w-[85%]">
          <View
            className={`px-4 py-3 rounded-[20px] ${
              isUser
                ? 'bg-[#3B49DF] rounded-br-[4px] shadow-sm shadow-[#3B49DF]/20'
                : 'bg-white rounded-bl-[4px] border border-gray-100 shadow-sm shadow-black/5'
            }`}
          >
            <Text
              className={`text-[15px] leading-[22px] ${
                isUser ? 'text-white font-medium' : 'text-gray-800 font-normal'
              }`}
            >
              {message.text}
            </Text>
          </View>

          {/* Interactive Activity Cards rendered inside Coach message flow */}
          {!isUser && message.options && message.options.length > 0 && (
            <RecoveryActivityCards options={message.options} />
          )}
        </View>
      </View>
    </View>
  );
};
