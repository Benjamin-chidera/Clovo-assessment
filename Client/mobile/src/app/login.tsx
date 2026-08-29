import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ImageBackground,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';
import { useAuthStore } from '@/stores/useAuthStore';

export default function LoginScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { login } = useAuthStore();

  const handleLogin = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    }
    login();
    router.replace('/');
  };

  return (
    <View className="flex-1 bg-[#F8F9FD]">
      {/* Background Graphic / Image */}
      <ImageBackground
        source={{
          uri: 'https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=1200&q=80',
        }}
        style={{ paddingTop: insets.top + 20 }}
        className="flex-1 justify-between px-6 pb-10 relative"
        resizeMode="cover"
      >
        <View className="absolute inset-0 bg-gray-900/45" />

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
              Personalized Recovery & Wellness
            </Text>
          </View>
          <Text className="text-[28px] font-extrabold text-white leading-9 tracking-tight">
            Your daily rhythm for rest, recovery, and peak performance.
          </Text>
        </View>
      </ImageBackground>

      {/* Bottom Auth Action Section */}
      <View
        style={{ paddingBottom: Math.max(insets.bottom, 20) + 16 }}
        className="bg-white rounded-t-[32px] pt-8 px-6 -mt-6 shadow-2xl"
      >
        <View className="mb-7">
          <Text className="text-2xl font-extrabold text-[#111827] tracking-tight">
            Welcome Back
          </Text>
          <Text className="text-sm text-[#6B7280] mt-1.5 leading-5">
            Continue your daily recovery journey with Coach Amy.
          </Text>
        </View>

        {/* Primary Single Login Button */}
        <TouchableOpacity
          className="bg-[#3B49DF] flex-row items-center justify-center py-4 rounded-full shadow-lg shadow-[#3B49DF]/30 relative active:scale-[0.98]"
          onPress={handleLogin}
          activeOpacity={0.88}
          accessibilityRole="button"
          accessibilityLabel="Log In to Clovo"
        >
          <View className="absolute left-3 w-9 h-9 rounded-full bg-white justify-center items-center">
            <Ionicons name="arrow-forward" size={18} color="#3B49DF" />
          </View>
          <Text className="text-white text-[17px] font-bold tracking-wide">
            Log In
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
