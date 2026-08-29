import React from 'react';
import { View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useUserStore } from '@/stores/useUserStore';

export const GreetingBadges: React.FC = () => {
  const { name, greeting, streakCount, badges } = useUserStore();

  return (
    <View className="px-5 mt-4">
      {/* Top row: Greeting on the left, Overlapping Achievement stack on the right */}
      <View className="flex-row items-center justify-between">
        <View className="flex-1">
          <Text className="text-base text-[#434190] font-medium">{greeting},</Text>
          <Text className="text-[34px] font-extrabold text-[#111827] tracking-tight mt-0.5">
            {name}
          </Text>
        </View>

        {/* Milestone Badge Stack */}
        <View className="flex-row items-center">
          {badges.map((badge, index) => (
            <View
              key={badge.id}
              style={{
                backgroundColor: badge.bgGradient[0],
                marginLeft: index === 0 ? 0 : -12,
                zIndex: badges.length - index,
              }}
              className="w-9 h-9 rounded-full border-2 border-white justify-center items-center shadow-sm"
            >
              <Ionicons
                name={badge.iconName as any}
                size={16}
                color={badge.color}
              />
            </View>
          ))}
          {/* +3 Additional Counter Badge */}
          <View
            style={{ marginLeft: -12, zIndex: 0 }}
            className="w-9 h-9 rounded-full bg-[#374151] border-2 border-white justify-center items-center shadow-sm"
          >
            <Text className="text-white text-[11px] font-bold">+3</Text>
          </View>
        </View>
      </View>

      {/* Streak Capsule Pill */}
      <View className="mt-2.5 flex-row">
        <View className="flex-row items-center bg-[#EEF2FF] px-3 py-1.5 rounded-full">
          <Text className="text-sm mr-1.5">🔥</Text>
          <Text className="text-[13px] font-bold text-[#3B49DF]">
            {streakCount} day streak
          </Text>
        </View>
      </View>
    </View>
  );
};
