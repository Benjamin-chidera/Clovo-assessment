import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ImageBackground,
  Image,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
import { useAuthStore, PRE_OP_USER, POST_OP_USER, AuthUser } from '@/stores/useAuthStore';

export default function LoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { login } = useAuthStore();
  const [selectedUser, setSelectedUser] = useState<AuthUser>(PRE_OP_USER);

  const handleSelectUser = (user: AuthUser) => {
    if (Platform.OS !== 'web') {
      Haptics.selectionAsync();
    }
    setSelectedUser(user);
  };

  const handleLogin = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    login(selectedUser);
    router.replace('/');
  };

  const isSarah = selectedUser.id === PRE_OP_USER.id;
  const isJane = selectedUser.id === POST_OP_USER.id;

  return (
    <View className="flex-1 bg-[#F8F9FD]">
      {/* Background Graphic / Image */}
      <ImageBackground
        source={{
          uri: 'https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80',
        }}
        style={{ paddingTop: insets.top + 20 }}
        className="flex-1 justify-between px-6 pb-8 relative"
        resizeMode="cover"
      >
        <View className="absolute inset-0 bg-gray-900/50" />

        {/* Top Logo / Brand Badge */}
        <View className="flex-row items-center gap-3 z-10">
          <View className="w-11 h-11 rounded-full bg-white justify-center items-center shadow-md shadow-black/15">
            <Ionicons name="sparkles" size={24} color="#3B49DF" />
          </View>
          <Text className="text-[22px] font-black text-white tracking-widest">
            CLOVO
          </Text>
        </View>

        {/* Hero Tagline */}
        <View className="z-10">
          <View className="self-start bg-white/25 px-3 py-1 rounded-full mb-3">
            <Text className="text-white text-xs font-semibold tracking-wide">
              Personalized Clinical Recovery & Care
            </Text>
          </View>
          <Text className="text-[26px] font-extrabold text-white leading-8 tracking-tight">
            Your daily rhythm for pre-op preparation and post-op rehabilitation.
          </Text>
        </View>
      </ImageBackground>

      {/* Bottom Auth Action Section */}
      <View
        style={{ paddingBottom: Math.max(insets.bottom, 20) + 16 }}
        className="bg-white rounded-t-[32px] pt-7 px-6 -mt-6 shadow-2xl"
      >
        <View className="mb-5">
          <Text className="text-2xl font-extrabold text-[#111827] tracking-tight">
            Select Patient Profile
          </Text>
          <Text className="text-sm text-[#6B7280] mt-1 leading-5">
            Choose your surgical care pathway to begin with Coach Amy.
          </Text>
        </View>

        {/* Patient Selection Cards */}
        <View className="gap-3 mb-6">
          {/* Sarah Card (Pre-Op) */}
          <TouchableOpacity
            onPress={() => handleSelectUser(PRE_OP_USER)}
            activeOpacity={0.85}
            className={`p-3.5 rounded-2xl border-2 flex-row items-center justify-between transition-all ${
              isSarah
                ? 'border-[#3B49DF] bg-[#EEF2FF]'
                : 'border-gray-200 bg-gray-50/70'
            }`}
            accessibilityRole="radio"
            accessibilityState={{ selected: isSarah }}
            accessibilityLabel="Select Sarah, Pre-Op Preparation"
          >
            <View className="flex-row items-center gap-3 flex-1 mr-2">
              <Image
                source={{ uri: PRE_OP_USER.avatarUri }}
                className="w-12 h-12 rounded-full border border-gray-200 bg-gray-200"
              />
              <View className="flex-1">
                <View className="flex-row items-center gap-2">
                  <Text className="text-base font-bold text-[#111827]">
                    Sarah
                  </Text>
                  <View className="bg-blue-100 px-2 py-0.5 rounded-full">
                    <Text className="text-[10px] font-bold text-blue-700 uppercase tracking-wider">
                      Pre-Op
                    </Text>
                  </View>
                </View>
                <Text className="text-xs text-[#6B7280] mt-0.5">
                  Knee Surgery Prep • 21 Days Away
                </Text>
              </View>
            </View>

            <View
              className={`w-6 h-6 rounded-full border-2 justify-center items-center ${
                isSarah ? 'border-[#3B49DF] bg-[#3B49DF]' : 'border-gray-300 bg-white'
              }`}
            >
              {isSarah && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
            </View>
          </TouchableOpacity>

          {/* Jane Card (Post-Op) */}
          <TouchableOpacity
            onPress={() => handleSelectUser(POST_OP_USER)}
            activeOpacity={0.85}
            className={`p-3.5 rounded-2xl border-2 flex-row items-center justify-between transition-all ${
              isJane
                ? 'border-[#3B49DF] bg-[#EEF2FF]'
                : 'border-gray-200 bg-gray-50/70'
            }`}
            accessibilityRole="radio"
            accessibilityState={{ selected: isJane }}
            accessibilityLabel="Select Jane, Post-Op Rehabilitation"
          >
            <View className="flex-row items-center gap-3 flex-1 mr-2">
              <Image
                source={{ uri: POST_OP_USER.avatarUri }}
                className="w-12 h-12 rounded-full border border-gray-200 bg-gray-200"
              />
              <View className="flex-1">
                <View className="flex-row items-center gap-2">
                  <Text className="text-base font-bold text-[#111827]">
                    Jane
                  </Text>
                  <View className="bg-emerald-100 px-2 py-0.5 rounded-full">
                    <Text className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider">
                      Post-Op
                    </Text>
                  </View>
                </View>
                <Text className="text-xs text-[#6B7280] mt-0.5">
                  Knee Replacement • Day 6 Rehabilitation
                </Text>
              </View>
            </View>

            <View
              className={`w-6 h-6 rounded-full border-2 justify-center items-center ${
                isJane ? 'border-[#3B49DF] bg-[#3B49DF]' : 'border-gray-300 bg-white'
              }`}
            >
              {isJane && <Ionicons name="checkmark" size={14} color="#FFFFFF" />}
            </View>
          </TouchableOpacity>
        </View>

        {/* Primary Dynamic Login Button */}
        <TouchableOpacity
          className="bg-[#3B49DF] flex-row items-center justify-center py-4 rounded-full shadow-lg shadow-[#3B49DF]/30 relative active:scale-[0.98]"
          onPress={handleLogin}
          activeOpacity={0.88}
          accessibilityRole="button"
          accessibilityLabel={`Log In as ${selectedUser.name}`}
        >
          <View className="absolute left-3 w-9 h-9 rounded-full bg-white justify-center items-center">
            <Ionicons name="arrow-forward" size={18} color="#3B49DF" />
          </View>
          <Text className="text-white text-[17px] font-bold tracking-wide">
            Log In as {selectedUser.name}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
