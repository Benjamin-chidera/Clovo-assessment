import React from 'react';
import {
  View,
  Text,
  Modal,
  TouchableOpacity,
  TouchableWithoutFeedback,
  Image,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
import { useAuthStore } from '@/stores/useAuthStore';

export const ProfileModal: React.FC = () => {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { isProfileModalOpen, user, logout, closeProfileModal } = useAuthStore();

  if (!isProfileModalOpen) {
    return null;
  }

  const handleDismiss = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    closeProfileModal();
  };

  const handleLogout = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    logout();
    router.replace('/login');
  };

  return (
    <Modal
      transparent
      visible={isProfileModalOpen}
      animationType="fade"
      onRequestClose={handleDismiss}
    >
      <TouchableWithoutFeedback onPress={handleDismiss}>
        <View className="flex-1 bg-black/45 justify-end">
          <TouchableWithoutFeedback>
            <View
              style={{ paddingBottom: Math.max(insets.bottom, 20) + 12 }}
              className="bg-white rounded-t-[28px] pt-3 px-5 shadow-2xl"
            >
              {/* Sheet Handle */}
              <View className="w-10 h-1 rounded-full bg-gray-300 self-center mb-4" />

              {/* Profile Header */}
              <View className="flex-row items-center pb-4.5 border-b border-gray-100">
                <Image
                  source={{
                    uri:
                      user?.avatarUri ||
                      'https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=200&q=80',
                  }}
                  className="w-14 h-14 rounded-full border-2 border-[#EEF2FF]"
                />
                <View className="ml-3.5 flex-1">
                  <View className="flex-row items-center">
                    <Text className="text-xl font-bold text-[#111827]">
                      {user?.name || 'Jen'}
                    </Text>
                    <View className="bg-[#EEF2FF] px-2 py-0.5 rounded-full ml-2">
                      <Text className="text-[11px] font-bold text-[#3B49DF]">
                        {user?.plan || 'Active'}
                      </Text>
                    </View>
                  </View>
                  <Text className="text-[13px] text-[#6B7280] mt-0.5">
                    {user?.email || 'jen@clovo.app'}
                  </Text>
                </View>
              </View>

              {/* Profile Switch Section */}
              <View className="mt-4">
                <Text className="text-xs font-bold text-[#6B7280] uppercase tracking-wider mb-2.5">
                  Profiles
                </Text>

                <TouchableOpacity
                  className="flex-row items-center justify-between py-3 px-3.5 rounded-2xl bg-[#EEF2FF] mb-2 border border-[#E0E7FF]"
                  activeOpacity={0.8}
                >
                  <View className="flex-row items-center">
                    <View className="w-8.5 h-8.5 rounded-full bg-white justify-center items-center mr-3">
                      <Ionicons name="person" size={16} color="#3B49DF" />
                    </View>
                    <View>
                      <Text className="text-sm font-semibold text-[#111827]">
                        Personal Space
                      </Text>
                      <Text className="text-xs text-[#6B7280] mt-0.5">
                        Daily recovery & streak
                      </Text>
                    </View>
                  </View>
                  <Ionicons name="checkmark-circle" size={20} color="#3B49DF" />
                </TouchableOpacity>

                <TouchableOpacity
                  className="flex-row items-center justify-between py-3 px-3.5 rounded-2xl bg-gray-50 mb-2 border border-gray-100"
                  activeOpacity={0.8}
                  onPress={() => {
                    if (Platform.OS !== 'web') {
                      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    }
                  }}
                >
                  <View className="flex-row items-center">
                    <View className="w-8.5 h-8.5 rounded-full bg-gray-200 justify-center items-center mr-3">
                      <Ionicons name="people-outline" size={16} color="#6B7280" />
                    </View>
                    <View>
                      <Text className="text-sm font-semibold text-[#111827]">
                        Family & Friends
                      </Text>
                      <Text className="text-xs text-[#6B7280] mt-0.5">
                        Shared accountability
                      </Text>
                    </View>
                  </View>
                  <Ionicons name="chevron-forward" size={18} color="#9CA3AF" />
                </TouchableOpacity>
              </View>

              {/* Logout Action Button */}
              <View className="mt-4 gap-2.5">
                <TouchableOpacity
                  className="flex-row items-center justify-center bg-red-100 py-3.5 rounded-2xl gap-2 active:bg-red-200"
                  onPress={handleLogout}
                  activeOpacity={0.85}
                  accessibilityRole="button"
                  accessibilityLabel="Log out of Clovo"
                >
                  <Ionicons name="log-out-outline" size={20} color="#EF4444" />
                  <Text className="text-base font-bold text-red-500">Log Out</Text>
                </TouchableOpacity>

                {/* Cancel / Dismiss Button */}
                <TouchableOpacity
                  className="items-center py-3"
                  onPress={handleDismiss}
                  activeOpacity={0.8}
                  accessibilityRole="button"
                  accessibilityLabel="Cancel and close menu"
                >
                  <Text className="text-[15px] font-semibold text-[#6B7280]">
                    Cancel
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};
