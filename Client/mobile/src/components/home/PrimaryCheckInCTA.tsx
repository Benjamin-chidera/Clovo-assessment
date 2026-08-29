import React from 'react';
import { View, Text, TouchableOpacity, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface PrimaryCheckInCTAProps {
  onPress: () => void;
}

export const PrimaryCheckInCTA: React.FC<PrimaryCheckInCTAProps> = ({ onPress }) => {
  const handlePress = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    onPress();
  };

  return (
    <View className="px-5 mt-5">
      <Text className="text-sm text-[#6B7280] font-medium mb-3">
        Let’s make today a good one—start your check-in now!
      </Text>

      <TouchableOpacity
        className="bg-[#3B49DF] flex-row items-center py-4 px-4 rounded-full shadow-lg shadow-[#3B49DF]/30 active:scale-[0.98]"
        onPress={handlePress}
        activeOpacity={0.88}
        accessibilityRole="button"
        accessibilityLabel="Check in with Amy"
      >
        <View className="w-8 h-8 rounded-full bg-white justify-center items-center mr-3.5">
          <Ionicons
            name="arrow-forward-outline"
            size={16}
            color="#3B49DF"
            style={{ transform: [{ rotate: '-45deg' }] }}
          />
        </View>
        <Text className="text-white text-[17px] font-bold tracking-wide">
          Check in with Amy
        </Text>
      </TouchableOpacity>
    </View>
  );
};
