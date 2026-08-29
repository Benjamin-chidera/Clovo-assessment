import React, { useState, useEffect } from 'react';
import {
  View,
  TextInput,
  TouchableOpacity,
  Text,
  ScrollView,
  Platform,
  KeyboardAvoidingView,
  Keyboard,
  NativeSyntheticEvent,
  TextInputKeyPressEventData,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useChatStore } from '@/stores/useChatStore';

export const ChatInputBar: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [isKeyboardVisible, setIsKeyboardVisible] = useState(false);
  const insets = useSafeAreaInsets();
  const { quickReplies, sendMessage } = useChatStore();

  useEffect(() => {
    const showEvent = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const hideEvent = Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide';

    const showSubscription = Keyboard.addListener(showEvent, () => {
      setIsKeyboardVisible(true);
    });
    const hideSubscription = Keyboard.addListener(hideEvent, () => {
      setIsKeyboardVisible(false);
    });

    return () => {
      showSubscription.remove();
      hideSubscription.remove();
    };
  }, []);

  const handleSend = (textToSend?: string) => {
    const text = (textToSend ?? inputText).trim();
    if (!text) return;

    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    sendMessage(text);
    if (!textToSend) {
      setInputText('');
    }
  };

  const handleKeyPress = (e: NativeSyntheticEvent<TextInputKeyPressEventData>) => {
    if (e.nativeEvent.key === 'Enter') {
      handleSend();
    }
  };

  const handleQuickReply = (reply: string) => {
    handleSend(reply);
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={0}
    >
      <View
        style={{
          paddingBottom: isKeyboardVisible ? 8 : Math.max(insets.bottom, 12),
        }}
        className="px-4 pt-2 bg-transparent"
      >
        {/* Quick Reply Chips (if any available) */}
        {quickReplies.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={{ gap: 8, paddingBottom: 8 }}
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
        )}

        {/* Input Pill Container exactly matching the design */}
        <View className="flex-row items-center bg-white rounded-full px-2 py-2 border border-[#E2E8F0] shadow-sm mb-3">
          <TextInput
            className="flex-1 text-[15px] text-[#111827] py-1.5 pr-2"
            placeholder="Type your message..."
            placeholderTextColor="#9CA3AF"
            value={inputText}
            onChangeText={setInputText}
            returnKeyType="send"
            onSubmitEditing={() => handleSend()}
            onKeyPress={handleKeyPress}
            blurOnSubmit={false}
            enablesReturnKeyAutomatically
            autoCapitalize="sentences"
            autoCorrect
            accessibilityLabel="Chat input"
          />

          {/* Right Arrow / Send Circular Button */}
          <TouchableOpacity
            className={`w-9 h-9 rounded-full justify-center items-center bg-[#3B49DF] ${
              !inputText.trim() ? 'opacity-90' : 'opacity-100'
            }`}
            onPress={() => handleSend()}
            disabled={!inputText.trim()}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel="Send message"
          >
            <Ionicons
              name="send"
              size={15}
              color="#FFFFFF"
              style={{ marginLeft: 2 }}
            />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};
