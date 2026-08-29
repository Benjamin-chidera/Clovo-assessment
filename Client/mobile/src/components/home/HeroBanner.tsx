import React from 'react';
import { View, ImageBackground, TouchableOpacity, Text, Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';

interface HeroBannerProps {
  onSwitchProfile?: () => void;
}

export const HeroBanner: React.FC<HeroBannerProps> = ({ onSwitchProfile }) => {
  const insets = useSafeAreaInsets();

  const handleSwitchPress = () => {
    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
    onSwitchProfile?.();
  };

  return (
    <View className="w-full h-60 bg-[#F8F9FD]">
      <ImageBackground
        source={{
          uri: 'https://images.unsplash.com/photo-1545205597-3d9d02c29597?auto=format&fit=crop&w=1200&q=85',
        }}
        style={{ paddingTop: insets.top + 8 }}
        className="flex-1 px-5 justify-between pb-4"
        imageStyle={{
          borderBottomLeftRadius: 32,
          borderBottomRightRadius: 32,
        }}
        resizeMode="cover"
      >
        {/* Top Header Overlay with Profile Switch Action */}
        <View className="flex-row items-center justify-end">
          <TouchableOpacity
            className="w-10 h-10 rounded-full bg-black/35 justify-center items-center border border-white/25"
            onPress={handleSwitchPress}
            activeOpacity={0.8}
            accessibilityLabel="Switch profile or settings"
            accessibilityRole="button"
          >
            <Ionicons name="swap-horizontal" size={18} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </ImageBackground>
    </View>
  );
};
