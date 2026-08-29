import React from 'react';
import { View, Text, TouchableOpacity, Image, Platform, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { ActivityCard, useChatStore } from '@/stores/useChatStore';

interface RecoveryActivityCardsProps {
  options: ActivityCard[];
}

export const RecoveryActivityCards: React.FC<RecoveryActivityCardsProps> = ({ options }) => {
  const { selectedCardId, selectActivity } = useChatStore();

  const handleCardPress = (card: ActivityCard) => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    selectActivity(card);
  };

  return (
    <View className="my-3">
      <Text className="text-xs font-semibold text-[#6B7280] mb-2 ml-1 uppercase tracking-wider">
        Recommended for you:
      </Text>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ gap: 12, paddingRight: 16, paddingVertical: 4 }}
      >
        {options.map((card) => {
          const isSelected = selectedCardId === card.id;

          if (card.isSpecial) {
            return (
              <TouchableOpacity
                key={card.id}
                className={`w-[210px] bg-pink-50 rounded-2xl overflow-hidden border-2 shadow-md shadow-pink-500/10 ${
                  isSelected ? 'border-[#3B49DF] scale-[1.02]' : 'border-transparent'
                }`}
                onPress={() => handleCardPress(card)}
                activeOpacity={0.88}
                accessibilityRole="button"
                accessibilityLabel={card.title}
              >
                <View className="w-full h-[110px] relative bg-pink-100">
                  <Image source={{ uri: card.imageUri }} className="w-full h-full" />
                  <View className="absolute inset-0 bg-pink-500/15" />
                  <View className="absolute top-2 right-2 w-7 h-7 rounded-full bg-white justify-center items-center">
                    <Text className="text-sm">🎁</Text>
                  </View>
                </View>

                <View className="p-3">
                  <Text className="text-[15px] font-bold text-pink-900 leading-5">
                    {card.title}
                  </Text>
                  <Text className="text-xs text-pink-700 mt-1 font-medium">
                    {card.subtitle}
                  </Text>
                </View>
              </TouchableOpacity>
            );
          }

          return (
            <TouchableOpacity
              key={card.id}
              className={`w-[210px] bg-white rounded-2xl overflow-hidden border-2 shadow-md shadow-black/5 ${
                isSelected ? 'border-[#3B49DF] scale-[1.02]' : 'border-transparent'
              }`}
              onPress={() => handleCardPress(card)}
              activeOpacity={0.88}
              accessibilityRole="button"
              accessibilityLabel={`${card.title}, ${card.durationLabel}`}
            >
              <View className="w-full h-[110px] relative bg-gray-200">
                <Image source={{ uri: card.imageUri }} className="w-full h-full" />
                {card.tag && (
                  <View className="absolute top-2 left-2 bg-black/60 px-2 py-0.5 rounded">
                    <Text className="text-white text-[11px] font-semibold">
                      {card.tag}
                    </Text>
                  </View>
                )}
              </View>

              <View className="p-3">
                <Text
                  className="text-sm font-bold text-[#111827] leading-[18px] h-9"
                  numberOfLines={2}
                >
                  {card.title}
                </Text>

                <View className="flex-row items-center mt-2">
                  <View className="flex-row items-center gap-1">
                    <Ionicons name="time-outline" size={13} color="#6B7280" />
                    <Text className="text-xs text-[#6B7280] font-medium">
                      {card.durationLabel}
                    </Text>
                  </View>
                  <Text className="text-xs text-[#6B7280] mx-1.5">·</Text>
                  <View className="flex-row items-center gap-1">
                    <Ionicons name="flash-outline" size={13} color="#FF6B00" />
                    <Text className="text-xs text-[#6B7280] font-medium">
                      {card.intensity}
                    </Text>
                  </View>
                </View>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};
