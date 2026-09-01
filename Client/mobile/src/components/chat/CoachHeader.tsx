import React, { useCallback } from 'react';
import { View, Text, TouchableOpacity, Image, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useVoiceStore } from '@/stores/useVoiceStore';

interface CoachHeaderProps {
  onBackPress?: () => void;
}

export const CoachHeader: React.FC<CoachHeaderProps> = ({ onBackPress }) => {
  const insets = useSafeAreaInsets();
  const isVoiceModeEnabled = useVoiceStore((s) => s.isVoiceModeEnabled);
  const isSpeaking = useVoiceStore((s) => s.isSpeaking);
  const isListening = useVoiceStore((s) => s.isListening);
  const phase = useVoiceStore((s) => s.phase);

  const handleBack = useCallback(() => {
    if (Platform.OS !== 'web') {
      try {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } catch {
        // ignore
      }
    }
    onBackPress?.();
  }, [onBackPress]);

  return (
    <View
      style={{ paddingTop: insets.top + 6 }}
      className="bg-white pb-3 px-4 border-b border-gray-100 shadow-sm"
    >
      <View className="flex-row items-center">
        {/* Left: Back Button */}
        <TouchableOpacity
          className="w-9 h-9 rounded-full bg-[#3B49DF] justify-center items-center mr-3"
          onPress={handleBack}
          activeOpacity={0.8}
          accessibilityRole="button"
          accessibilityLabel="Go back"
        >
          <Ionicons
            name="arrow-up"
            size={18}
            color="#FFFFFF"
            style={{ transform: [{ rotate: '-45deg' }] }}
          />
        </TouchableOpacity>

        {/* Coach Profile Avatar & Name */}
        <View className="flex-row items-center flex-1">
          <View className="w-10 h-10 rounded-full overflow-hidden mr-2.5 bg-emerald-100/60 p-0.5 border border-emerald-200/50">
            <Image
              source={{
                uri: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80',
              }}
              className="w-full h-full rounded-full"
            />
          </View>

          <View className="flex-1">
            <Text className="text-[15px] font-bold text-[#111827]" numberOfLines={1}>
              Amy - Recovery Coach
            </Text>
            <View className="flex-row items-center mt-0.5">
              {isSpeaking ? (
                <TouchableOpacity
                  onPress={() => useVoiceStore.getState().interruptAndListen()}
                  className="flex-row items-center bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200/60"
                  activeOpacity={0.7}
                  accessibilityLabel="Amy is speaking. Tap to interrupt and speak."
                >
                  <View className="w-2 h-2 rounded-full bg-[#10B981] mr-1.5" />
                  <Text className="text-xs text-[#10B981] font-semibold">🔊 Speaking (Tap to speak)</Text>
                </TouchableOpacity>
              ) : isListening ? (
                <View className="flex-row items-center">
                  <View className="w-2 h-2 rounded-full bg-[#3B49DF] mr-1.5" />
                  <Text className="text-xs text-[#3B49DF] font-semibold">🎙️ Listening...</Text>
                </View>
              ) : phase === 'processing' ? (
                <View className="flex-row items-center">
                  <View className="w-2 h-2 rounded-full bg-[#F59E0B] mr-1.5" />
                  <Text className="text-xs text-[#F59E0B] font-semibold">⏳ Processing...</Text>
                </View>
              ) : isVoiceModeEnabled ? (
                <View className="flex-row items-center">
                  <View className="w-2 h-2 rounded-full bg-[#3B49DF] mr-1.5" />
                  <Text className="text-xs text-[#3B49DF] font-semibold">Voice Mode Active</Text>
                </View>
              ) : (
                <View className="flex-row items-center">
                  <View className="w-1.5 h-1.5 rounded-full bg-[#10B981] mr-1.5" />
                  <Text className="text-xs text-[#10B981] font-semibold">Active</Text>
                </View>
              )}
            </View>
          </View>
        </View>

        {/* Right: End Voice Mode Button (when active) */}
        {isVoiceModeEnabled && (
          <TouchableOpacity
            onPress={() => useVoiceStore.getState().deactivateVoiceConversation()}
            className="bg-red-50 px-2.5 py-1 rounded-full border border-red-200 ml-2"
            activeOpacity={0.7}
            accessibilityRole="button"
            accessibilityLabel="End voice conversation"
          >
            <Text className="text-[11px] font-bold text-red-600">✕ End</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};
