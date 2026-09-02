import React from "react";
import { View, Text } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { ChatMessage } from "@/stores/useChatStore";
import { RecoveryActivityCards } from "./RecoveryActivityCards";

interface MessageBubbleProps {
  message: ChatMessage;
  showTimestamp?: boolean;
}

const MessageBubbleComponent: React.FC<MessageBubbleProps> = ({
  message,
  showTimestamp = true,
}) => {
  const isUser = message.sender === "user";
  const isSafetyAlert = message.isSafetyAlert;
  const isCritical = message.riskLevel === "critical";

  return (
    <View className="my-2 px-4">
      {showTimestamp && (
        <View className="mb-1.5 items-start pl-1">
          <Text className="text-[11px] text-[#9CA3AF] font-medium">
            {message.timestamp}
          </Text>
        </View>
      )}

      <View className={`flex-row ${isUser ? "justify-end" : "justify-start"}`}>
        <View
          className={`${
            message.options && message.options.length > 0 ? "w-full" : "max-w-[88%]"
          }`}
        >
          {/* Safety Alert Clinical Card */}
          {isSafetyAlert ? (
            <View
              className={`p-4 rounded-2xl border ${
                isCritical
                  ? "bg-red-50 border-red-200"
                  : "bg-amber-50 border-amber-200"
              } shadow-sm`}
            >
              <View className="flex-row items-center mb-2">
                <Ionicons
                  name={isCritical ? "alert-circle" : "warning"}
                  size={18}
                  color={isCritical ? "#DC2626" : "#D97706"}
                />
                <Text
                  className={`text-xs font-bold ml-1.5 uppercase tracking-wider ${
                    isCritical ? "text-red-700" : "text-amber-800"
                  }`}
                >
                  {isCritical ? "Urgent Medical Alert" : "Clinical Safety Flag"}
                </Text>
              </View>
              <Text
                className={`text-[15px] leading-[22px] font-medium ${
                  isCritical ? "text-red-950" : "text-amber-950"
                }`}
              >
                {message.text}
              </Text>
            </View>
          ) : (
            /* Normal Chat Message Bubble */
            <View
              className={`px-4 py-3 rounded-2xl ${
                isUser
                  ? "bg-[#3B49DF] shadow-sm"
                  : "bg-white border border-gray-100 shadow-sm"
              }`}
            >
              <Text
                className={`text-[15px] leading-[22px] ${
                  isUser ? "text-white font-medium" : "text-[#1F2937] font-normal"
                }`}
              >
                {message.text}
              </Text>
            </View>
          )}

          {/* Activity Cards (Full width stacked list) */}
          {!isUser && message.options && message.options.length > 0 && (
            <RecoveryActivityCards options={message.options} />
          )}
        </View>
      </View>
    </View>
  );
};

export const MessageBubble = React.memo(MessageBubbleComponent, (prev, next) => {
  return (
    prev.message.id === next.message.id &&
    prev.showTimestamp === next.showTimestamp &&
    prev.message.text === next.message.text &&
    prev.message.isSafetyAlert === next.message.isSafetyAlert &&
    prev.message.options === next.message.options
  );
});
