import React from 'react';
import { View, Text, TouchableOpacity, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useUserStore } from '@/stores/useUserStore';

interface MilestoneCardProps {
  onPress?: () => void;
}

export const MilestoneCard: React.FC<MilestoneCardProps> = ({ onPress }) => {
  const { surgeryTitle, daysAway, daysPostOp, phase, procedureName } = useUserStore();

  const isPostOp = phase === 'post-op' || daysPostOp !== undefined;
  const displayTitle = isPostOp ? 'Post-Op Rehabilitation' : surgeryTitle;
  const headline = isPostOp ? `Day ${daysPostOp || 6} Post-Op` : `${daysAway} days away`;
  const pathwaySubtitle = isPostOp
    ? `${procedureName} Recovery Pathway`
    : `${procedureName} Preparation Pathway`;
  const accentColor = isPostOp ? '#34D399' : '#38BDF8';

  const handlePress = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    onPress?.();
  };

  return (
    <View className="px-5 mt-4">
      <TouchableOpacity
        className="bg-[#1F2937] rounded-3xl py-4 px-5 flex-row items-center justify-between border border-white/10 shadow-md shadow-black/20"
        onPress={handlePress}
        activeOpacity={0.9}
        accessibilityRole="button"
        accessibilityLabel={`${displayTitle}, ${headline}`}
      >
        <View className="flex-1 pr-3.5">
          <View className="flex-row items-center mb-1">
            <View className="w-2 h-2 rounded-full mr-2" style={{ backgroundColor: accentColor }} />
            <Text className="text-xs font-bold uppercase tracking-wider text-[#9CA3AF]">
              {displayTitle}
            </Text>
          </View>
          <Text className="text-2xl font-black text-white tracking-tight">
            {headline}
          </Text>
          <Text className="text-xs text-[#9CA3AF] mt-0.5">
            {pathwaySubtitle}
          </Text>
        </View>

        <View className="w-10 h-10 rounded-full bg-white/10 justify-center items-center">
          <Ionicons
            name={isPostOp ? "medkit-outline" : "calendar-outline"}
            size={20}
            color={accentColor}
          />
        </View>
      </TouchableOpacity>
    </View>
  );
};
