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
import { useTaskStore } from "@/stores/useTaskStore";

interface RecoveryActivityCardsProps {
  options?: ActivityCard[] | null;
}

export const RecoveryActivityCards: React.FC<RecoveryActivityCardsProps> = ({
  options,
}) => {
  const { selectedCardId, selectActivity } = useChatStore();
  const { tasks } = useTaskStore();

  if (!options || !Array.isArray(options) || options.length === 0) {
    return null;
  }

  const handleCardPress = (card: ActivityCard) => {
    if (Platform.OS !== "web") {
      try {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      } catch {
        // Silently ignore — Haptics can fail during navigation transitions
      }
    }
    selectActivity(card);
  };

  return (
    <View className="mt-3 flex-col gap-2.5 w-full">
      {options.map((card) => {
        const isSelected = selectedCardId === card.id;

        // Check if task is completed via card prop or taskStore match
        const isCompleted =
          card.isCompleted ||
          tasks.some(
            (t) =>
              (t.id === String(card.recommendationId) ||
                t.title.toLowerCase() === card.title.toLowerCase()) &&
              t.isCompleted
          );

        return (
          <TouchableOpacity
            key={card.id}
            style={{
              width: '100%',
              flexDirection: 'row',
              alignItems: 'center',
              padding: 10,
              borderRadius: 16,
              borderWidth: 1,
              backgroundColor: isCompleted ? 'rgba(236, 253, 245, 0.2)' : '#FFFFFF',
              borderColor: isCompleted
                ? '#6EE7B7'
                : isSelected
                ? '#3B49DF'
                : '#F3F4F6',
            }}
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
                backgroundColor: isCompleted ? "#D1FAE5" : "#F3F4F6",
                position: "relative",
              }}
            >
              <Image
                source={{ uri: card.imageUri }}
                style={{ width: 62, height: 62, borderRadius: 14 }}
                resizeMode="cover"
              />
              {isCompleted && (
                <View className="absolute inset-0 bg-emerald-900/20 items-center justify-center">
                  <View className="w-6 h-6 rounded-full bg-emerald-500 items-center justify-center shadow-sm">
                    <Ionicons name="checkmark" size={16} color="#FFFFFF" />
                  </View>
                </View>
              )}
            </View>

            {/* Details on the right */}
            <View className="flex-1 ml-3.5 justify-center">
              <View className="flex-row items-center justify-between">
                <Text
                  className={`text-[15px] font-semibold leading-5 ${
                    isCompleted ? "text-emerald-950 font-bold" : "text-[#111827]"
                  }`}
                  numberOfLines={1}
                  style={{ flexShrink: 1 }}
                >
                  {card.title}
                </Text>

                {isCompleted && (
                  <View className="bg-emerald-100 px-2 py-0.5 rounded-full flex-row items-center ml-2">
                    <Ionicons
                      name="checkmark-circle"
                      size={12}
                      color="#059669"
                      style={{ marginRight: 3 }}
                    />
                    <Text className="text-[10px] font-bold text-emerald-700">
                      Completed
                    </Text>
                  </View>
                )}
              </View>

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
                      color={isCompleted ? "#059669" : "#9CA3AF"}
                      style={{ marginRight: 3 }}
                    />
                    <Text
                      className={`text-[13px] font-normal ${
                        isCompleted ? "text-emerald-700" : "text-[#6B7280]"
                      }`}
                    >
                      {card.durationLabel || `${card.durationMinutes || 10} minutes`}
                    </Text>
                  </View>

                  <Text className="text-[13px] text-[#9CA3AF] mx-1.5 font-normal">
                    -
                  </Text>

                  {/* Intensity with muscle icon */}
                  <View className="flex-row items-center">
                    <Text className="text-[12px] mr-1">💪</Text>
                    <Text
                      className={`text-[13px] font-normal ${
                        isCompleted ? "text-emerald-700" : "text-[#6B7280]"
                      }`}
                    >
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
