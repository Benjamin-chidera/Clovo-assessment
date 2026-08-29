import React from 'react';
import { View, Text, TouchableOpacity, Platform, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useTaskStore, DailyTask } from '@/stores/useTaskStore';

export const PendingTasksList: React.FC = () => {
  const { tasks, isLoading, toggleTask } = useTaskStore();

  const handleToggle = (task: DailyTask) => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    toggleTask(task.id);
  };

  const getCategoryMeta = (category: DailyTask['category']) => {
    switch (category) {
      case 'walking':
        return { name: 'walk-outline' as const, color: '#2563EB', bgClass: 'bg-blue-100' };
      case 'mindset':
        return { name: 'leaf-outline' as const, color: '#059669', bgClass: 'bg-emerald-100' };
      case 'nutrition':
      case 'hydration':
        return { name: 'nutrition-outline' as const, color: '#D97706', bgClass: 'bg-amber-100' };
      case 'recovery':
      default:
        return { name: 'body-outline' as const, color: '#7C3AED', bgClass: 'bg-purple-100' };
    }
  };

  if (tasks.length === 0 && isLoading) {
    return (
      <View className="px-5 mt-6 mb-10">
        <Text className="text-xl font-bold text-[#111827] tracking-tight mb-3.5">
          Today's preparation
        </Text>
        <View className="bg-white rounded-2xl p-6 items-center justify-center border border-gray-100">
          <ActivityIndicator color="#3B49DF" />
          <Text className="text-xs text-[#6B7280] font-medium mt-2">
            Loading preparation tasks...
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View className="px-5 mt-6 mb-10">
      <View className="flex-row items-center justify-between mb-3.5">
        <Text className="text-xl font-bold text-[#111827] tracking-tight">
          Today's preparation
        </Text>
        <Text className="text-[13px] font-semibold text-[#6B7280]">
          {tasks.filter((t) => !t.isCompleted).length} remaining
        </Text>
      </View>

      <View className="gap-3">
        {tasks.map((task) => {
          const iconMeta = getCategoryMeta(task.category);

          return (
            <TouchableOpacity
              key={task.id}
              className={`rounded-2xl p-4 flex-row items-center border shadow-sm ${
                task.isCompleted
                  ? 'bg-[#FAFAFC] border-gray-200 opacity-80'
                  : 'bg-white border-gray-100 shadow-black/5'
              }`}
              onPress={() => handleToggle(task)}
              activeOpacity={0.8}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: task.isCompleted }}
              accessibilityLabel={`${task.title}, ${task.duration}`}
            >
              {/* Category Icon Badge */}
              <View
                className={`w-10 h-10 rounded-full justify-center items-center mr-3.5 ${iconMeta.bgClass}`}
              >
                <Ionicons
                  name={iconMeta.name}
                  size={18}
                  color={iconMeta.color}
                />
              </View>

              {/* Task Details */}
              <View className="flex-1">
                <Text
                  className={`text-[15px] font-semibold mb-1 ${
                    task.isCompleted
                      ? 'text-[#6B7280] line-through'
                      : 'text-[#111827]'
                  }`}
                >
                  {task.title}
                </Text>
                <View className="flex-row items-center">
                  <Text className="text-xs font-medium text-[#6B7280]">
                    {task.categoryLabel}
                  </Text>
                  <Text className="text-xs text-[#6B7280] mx-1.5">·</Text>
                  <Text className="text-xs font-medium text-[#6B7280]">
                    {task.duration}
                  </Text>
                </View>
              </View>

              {/* Checkbox circle with ✓ / ○ */}
              <View
                className={`w-6 h-6 rounded-full border-2 justify-center items-center ml-3 ${
                  task.isCompleted
                    ? 'bg-[#3B49DF] border-[#3B49DF]'
                    : 'border-gray-300 bg-white'
                }`}
              >
                {task.isCompleted && (
                  <Ionicons name="checkmark" size={14} color="#FFFFFF" />
                )}
              </View>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
};
