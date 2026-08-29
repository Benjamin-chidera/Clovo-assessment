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
      style={{ paddingTop: insets.top + 6 }}
      className="bg-white pb-3 px-4 border-b border-gray-100 shadow-sm"
    >
      <View className="flex-row items-center">
        {/* Back Button matching the blue circular button in screenshot */}
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
          <View className="w-10 h-10 rounded-full overflow-hidden mr-2.5 bg-emerald-100/60 p-0.5">
            <Image
              source={{
                uri: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80',
              }}
              className="w-full h-full rounded-full"
            />
          </View>

          <View>
            <Text className="text-[15px] font-bold text-[#111827]">
              Amy - Recovery Coach
            </Text>
            <View className="flex-row items-center mt-0.5">
              <View className="w-1.5 h-1.5 rounded-full bg-[#10B981] mr-1.5" />
              <Text className="text-xs text-[#10B981] font-semibold">Active</Text>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
};
