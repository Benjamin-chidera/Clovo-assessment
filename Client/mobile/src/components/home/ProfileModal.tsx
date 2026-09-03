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
import { useAuthStore, PRE_OP_USER, POST_OP_USER, AuthUser } from '@/stores/useAuthStore';
import { useUserStore } from '@/stores/useUserStore';
import { useChatStore } from '@/stores/useChatStore';

export const ProfileModal: React.FC = () => {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { isProfileModalOpen, user, logout, switchUser, closeProfileModal } = useAuthStore();
  const { fetchHomeData, fetchUser } = useUserStore();
  const { fetchMessages } = useChatStore();

  if (!isProfileModalOpen) {
    return null;
  }

  const handleDismiss = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    closeProfileModal();
  };

  const handleSwitchPatient = async (targetUser: AuthUser) => {
    if (targetUser.id === user?.id) {
      return;
    }
    if (Platform.OS !== 'web') {
      Haptics.selectionAsync();
    }
    switchUser(targetUser);
    closeProfileModal();
    // Fetch data for newly switched patient
    await Promise.all([
      fetchHomeData(targetUser.id),
      fetchUser(targetUser.id),
      fetchMessages(targetUser.id === 'patient-jane' ? 2 : 1),
    ]);
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
                  Care Pathway Profiles
                </Text>

                {/* Sarah (Pre-Op) */}
                <TouchableOpacity
                  className={`flex-row items-center justify-between py-3 px-3.5 rounded-2xl mb-2 border ${
                    user?.id === PRE_OP_USER.id
                      ? 'bg-[#EEF2FF] border-[#E0E7FF]'
                      : 'bg-gray-50 border-gray-100'
                  }`}
                  activeOpacity={0.8}
                  onPress={() => handleSwitchPatient(PRE_OP_USER)}
                >
                  <View className="flex-row items-center flex-1 mr-2">
                    <Image
                      source={{ uri: PRE_OP_USER.avatarUri }}
                      className="w-9 h-9 rounded-full mr-3 border border-gray-200"
                    />
                    <View className="flex-1">
                      <View className="flex-row items-center gap-1.5">
                        <Text className="text-sm font-semibold text-[#111827]">
                          Sarah
                        </Text>
                        <View className="bg-blue-100 px-1.5 py-0.5 rounded-full">
                          <Text className="text-[9px] font-bold text-blue-700 uppercase">
                            Pre-Op
                          </Text>
                        </View>
                      </View>
                      <Text className="text-xs text-[#6B7280] mt-0.5">
                        Knee Surgery • 21 Days Away
                      </Text>
                    </View>
                  </View>
                  {user?.id === PRE_OP_USER.id ? (
                    <Ionicons name="checkmark-circle" size={20} color="#3B49DF" />
                  ) : (
                    <Ionicons name="radio-button-off" size={18} color="#9CA3AF" />
                  )}
                </TouchableOpacity>

                {/* Jane (Post-Op) */}
                <TouchableOpacity
                  className={`flex-row items-center justify-between py-3 px-3.5 rounded-2xl mb-2 border ${
                    user?.id === POST_OP_USER.id
                      ? 'bg-[#EEF2FF] border-[#E0E7FF]'
                      : 'bg-gray-50 border-gray-100'
                  }`}
                  activeOpacity={0.8}
                  onPress={() => handleSwitchPatient(POST_OP_USER)}
                >
                  <View className="flex-row items-center flex-1 mr-2">
                    <Image
                      source={{ uri: POST_OP_USER.avatarUri }}
                      className="w-9 h-9 rounded-full mr-3 border border-gray-200"
                    />
                    <View className="flex-1">
                      <View className="flex-row items-center gap-1.5">
                        <Text className="text-sm font-semibold text-[#111827]">
                          Jane
                        </Text>
                        <View className="bg-emerald-100 px-1.5 py-0.5 rounded-full">
                          <Text className="text-[9px] font-bold text-emerald-800 uppercase">
                            Post-Op
                          </Text>
                        </View>
                      </View>
                      <Text className="text-xs text-[#6B7280] mt-0.5">
                        Knee Replacement • Day 6 Rehab
                      </Text>
                    </View>
                  </View>
                  {user?.id === POST_OP_USER.id ? (
                    <Ionicons name="checkmark-circle" size={20} color="#3B49DF" />
                  ) : (
                    <Ionicons name="radio-button-off" size={18} color="#9CA3AF" />
                  )}
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
