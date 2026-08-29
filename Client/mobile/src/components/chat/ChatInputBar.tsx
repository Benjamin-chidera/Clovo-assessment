import React, { useState } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  ScrollView,
  Platform,
  KeyboardAvoidingView,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useChatStore } from '@/stores/useChatStore';

export const ChatInputBar: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const insets = useSafeAreaInsets();
  const { quickReplies, sendMessage } = useChatStore();

  const handleSend = (textToSend?: string) => {
    const text = (textToSend ?? inputText).trim();
    if (!text) return;

    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    sendMessage(text, 'user');
    if (!textToSend) {
      setInputText('');
    }
  };

  const handleQuickReply = (reply: string) => {
    handleSend(reply);
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View
        style={{ paddingBottom: Math.max(insets.bottom, 12) + 6 }}
        className="bg-white border-t border-gray-100 pt-2.5"
      >
        {/* Quick Reply Chips */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 10 }}
        >
          {quickReplies.map((reply, index) => (
            <TouchableOpacity
              key={index}
              className="bg-[#EEF2FF] px-3.5 py-1.5 rounded-full border border-[#E0E7FF]"
              onPress={() => handleQuickReply(reply)}
              activeOpacity={0.75}
              accessibilityRole="button"
              accessibilityLabel={reply}
            >
              <Text className="text-[13px] font-semibold text-[#3B49DF]">
                {reply}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Input Row */}
        <View className="px-4">
          <View className="flex-row items-center bg-gray-100 rounded-3xl px-4 py-1 min-h-[48px]">
            <TextInput
              className="flex-1 text-[15px] text-[#111827] max-h-24 py-2"
              placeholder="Type your message..."
              placeholderTextColor="#9CA3AF"
              value={inputText}
              onChangeText={setInputText}
              multiline
              maxLength={400}
              accessibilityLabel="Chat input"
            />
            <TouchableOpacity
              className={`w-8.5 h-8.5 rounded-full justify-center items-center ml-2 ${
                inputText.trim() ? 'bg-[#3B49DF]' : 'bg-gray-300'
              }`}
              onPress={() => handleSend()}
              disabled={!inputText.trim()}
              activeOpacity={0.8}
              accessibilityRole="button"
              accessibilityLabel="Send message"
            >
              <Ionicons
                name="arrow-up"
                size={18}
                color={inputText.trim() ? '#FFFFFF' : '#9CA3AF'}
              />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};
