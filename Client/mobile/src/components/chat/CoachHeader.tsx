import React from 'react';
import { View, Text, TouchableOpacity, Image, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface CoachHeaderProps {
  onBackPress?: () => void;
}

export const CoachHeader: React.FC<CoachHeaderProps> = ({ onBackPress }) => {
  const insets = useSafeAreaInsets();

  const handleBack = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    onBackPress?.();
  };

  return (
    <View
      style={{ paddingTop: insets.top + 8 }}
      className="bg-white pb-3.5 px-4 border-b border-gray-100 shadow-sm"
    >
      <View className="flex-row items-center justify-between">
        {/* Back Button */}
        <TouchableOpacity
          className="w-9.5 h-9.5 rounded-full bg-gray-100 justify-center items-center"
          onPress={handleBack}
          activeOpacity={0.8}
          accessibilityRole="button"
          accessibilityLabel="Go back to Home"
        >
          <Ionicons name="arrow-back" size={20} color="#111827" />
        </TouchableOpacity>

        {/* Coach Profile Info */}
        <View className="flex-row items-center flex-1 ml-3">
          <View className="relative">
            <Image
              source={{
                uri: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80',
              }}
              className="w-11 h-11 rounded-full"
            />
            {/* Active Status Badge Dot */}
            <View className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-[#10B981] border-2 border-white" />
          </View>

          <View className="ml-2.5">
            <Text className="text-base font-bold text-[#111827]">
              Amy - Recovery Coach
            </Text>
            <View className="flex-row items-center mt-0.5">
              <Text className="text-xs text-[#10B981] font-semibold">Active</Text>
            </View>
          </View>
        </View>

        {/* Right Info/Options Icon */}
        <TouchableOpacity
          className="w-9.5 h-9.5 rounded-full bg-[#EEF2FF] justify-center items-center"
          activeOpacity={0.8}
          accessibilityRole="button"
          accessibilityLabel="Coach options"
        >
          <Ionicons name="sparkles" size={18} color="#3B49DF" />
        </TouchableOpacity>
      </View>
    </View>
  );
};
