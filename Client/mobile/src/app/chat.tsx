import React, { useRef, useEffect, useMemo, useCallback } from 'react';
import { View, FlatList, ActivityIndicator, Text } from 'react-native';
import { useRouter } from 'expo-router';
import { CoachHeader } from '@/components/chat/CoachHeader';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInputBar } from '@/components/chat/ChatInputBar';
import { useChatStore, ChatMessage } from '@/stores/useChatStore';
import { useAuthStore } from '@/stores/useAuthStore';
import { socketService } from '@/services/socketService';

export default function ChatScreen() {
  const router = useRouter();
  const { messages, isLoading, isTyping, fetchMessages } = useChatStore();
  const { isAuthenticated, user } = useAuthStore();
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    } else {
      const patientId = user?.id || 'patient-sarah';
      socketService.connect(patientId);
      fetchMessages();
    }
  }, [isAuthenticated, user?.id]);

  const handleBack = () => {
    if (router.canGoBack()) {
      router.back();
    } else {
      router.push('/');
    }
  };

  // Reverse messages so newest message is index 0 for inverted bottom-anchored rendering
  const reversedMessages = useMemo(() => [...messages].reverse(), [messages]);

  const renderItem = useCallback(
    ({ item, index }: { item: ChatMessage; index: number }) => (
      <MessageBubble
        message={item}
        showTimestamp={
          index === reversedMessages.length - 1 ||
          item.timestamp !== reversedMessages[index + 1]?.timestamp
        }
      />
    ),
    [reversedMessages]
  );

  return (
    <View className="flex-1 bg-[#F8F9FD]">
      {/* Coach Header Navigation Bar */}
      <CoachHeader onBackPress={handleBack} />

      {/* Message Thread (Inverted so messages naturally anchor to the bottom) */}
      {isLoading && messages.length === 0 ? (
        <View className="flex-1 items-center justify-center">
          <ActivityIndicator size="large" color="#3B49DF" />
          <Text className="text-sm text-gray-500 font-medium mt-3">Connecting with Coach Amy...</Text>
        </View>
      ) : (
        <FlatList
          ref={flatListRef}
          data={reversedMessages}
          inverted
          keyExtractor={(item) => item.id}
          renderItem={renderItem}
          initialNumToRender={15}
          maxToRenderPerBatch={10}
          windowSize={7}
          removeClippedSubviews={false}
          ListHeaderComponent={
            isTyping ? (
              <View className="px-4 py-2 flex-row items-center">
                <View className="bg-white border border-gray-100 px-3.5 py-2 rounded-2xl shadow-sm flex-row items-center">
                  <ActivityIndicator size="small" color="#3B49DF" style={{ marginRight: 6 }} />
                  <Text className="text-xs text-gray-500 font-medium">Coach Amy is writing...</Text>
                </View>
              </View>
            ) : null
          }
          contentContainerStyle={{ paddingVertical: 16 }}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Fixed Chat Input Bar */}
      <ChatInputBar />
    </View>
  );
}
