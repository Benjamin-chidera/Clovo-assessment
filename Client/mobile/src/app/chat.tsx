import React, { useRef, useEffect } from 'react';
import { View, FlatList } from 'react-native';
import { useRouter } from 'expo-router';
import { CoachHeader } from '@/components/chat/CoachHeader';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInputBar } from '@/components/chat/ChatInputBar';
import { useChatStore } from '@/stores/useChatStore';
import { useAuthStore } from '@/stores/useAuthStore';

export default function ChatScreen() {
  const router = useRouter();
  const { messages } = useChatStore();
  const { isAuthenticated } = useAuthStore();
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length]);

  const handleBack = () => {
    if (router.canGoBack()) {
      router.back();
    } else {
      router.push('/');
    }
  };

  return (
    <View className="flex-1 bg-[#F8F9FD]">
      {/* Coach Header Navigation Bar */}
      <CoachHeader onBackPress={handleBack} />

      {/* Message Thread */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item, index }) => (
          <MessageBubble
            message={item}
            showTimestamp={index === 0 || item.timestamp !== messages[index - 1]?.timestamp}
          />
        )}
        contentContainerStyle={{ paddingVertical: 16, paddingBottom: 24 }}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      />

      {/* Fixed Chat Input Bar */}
      <ChatInputBar />
    </View>
  );
}
