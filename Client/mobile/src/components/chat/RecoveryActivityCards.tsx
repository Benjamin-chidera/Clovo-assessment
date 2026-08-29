import React from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { ActivityCard, useChatStore } from "@/stores/useChatStore";

interface RecoveryActivityCardsProps {
  options: ActivityCard[];
}

export const RecoveryActivityCards: React.FC<RecoveryActivityCardsProps> = ({
  options,
}) => {
  const { selectedCardId, selectActivity } = useChatStore();

  const handleCardPress = (card: ActivityCard) => {
    if (Platform.OS !== "web") {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    selectActivity(card);
  };

  return (
    <View className="mt-3 flex-col gap-2.5 w-full">
      {options.map((card) => {
        const isSelected = selectedCardId === card.id;

        return (
          <TouchableOpacity
            key={card.id}
            className={`w-full bg-white rounded-2xl p-2.5 flex-row items-center border ${
              isSelected
                ? "border-[#3B49DF] bg-blue-50/20"
                : "border-gray-100 shadow-sm"
            }`}
            onPress={() => handleCardPress(card)}
            activeOpacity={0.8}
            accessibilityRole="button"
            accessibilityLabel={card.title}
          >
            {/* Square Image Thumbnail with fallback background and explicit dimensions */}
            <View
              style={{
                width: 62,
                height: 62,
                borderRadius: 14,
                overflow: "hidden",
                backgroundColor: "#F3F4F6",
              }}
            >
              <Image
                source={{ uri: card.imageUri }}
                style={{ width: 62, height: 62, borderRadius: 14 }}
                resizeMode="cover"
              />
            </View>

            {/* Details on the right */}
            <View className="flex-1 ml-3.5 justify-center">
              <Text
                className="text-[15px] font-semibold text-[#111827] leading-5"
                numberOfLines={1}
              >
                {card.title}
              </Text>

              {card.isSpecial ? (
                <Text className="text-[13px] text-[#6B7280] font-normal mt-1">
                  {card.subtitle || "Let's See What You Get"}
                </Text>
              ) : (
                <View className="flex-row items-center mt-1">
                  {/* Duration with Stopwatch icon */}
                  <View className="flex-row items-center">
                    <Ionicons
                      name="time-outline"
                      size={14}
                      color="#9CA3AF"
                      style={{ marginRight: 3 }}
                    />
                    <Text className="text-[13px] text-[#6B7280] font-normal">
                      {card.durationLabel || `${card.durationMinutes || 10} minutes`}
                    </Text>
                  </View>

                  <Text className="text-[13px] text-[#9CA3AF] mx-1.5 font-normal">
                    -
                  </Text>

                  {/* Intensity with muscle icon */}
                  <View className="flex-row items-center">
                    <Text className="text-[12px] mr-1">💪</Text>
                    <Text className="text-[13px] text-[#6B7280] font-normal">
                      {card.intensity || "Low"}
                    </Text>
                  </View>
                </View>
              )}
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};
