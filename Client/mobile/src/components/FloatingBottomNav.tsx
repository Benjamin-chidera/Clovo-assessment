import React from 'react';
import { View, Text, Pressable, Platform, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useRouter } from 'expo-router';

interface FloatingBottomNavProps {
  activeTab: 'home' | 'chat';
}

export const FloatingBottomNav: React.FC<FloatingBottomNavProps> = ({ activeTab }) => {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const handleTabPress = (tab: 'home' | 'chat') => {
    if (tab === activeTab) return;

    if (Platform.OS !== 'web') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }

    if (tab === 'home') {
      router.replace('/');
    } else {
      router.replace('/chat');
    }
  };

  const isHome = activeTab === 'home';
  const isChat = activeTab === 'chat';

  return (
    <View
      style={[
        styles.outerContainer,
        { bottom: Math.max(insets.bottom, 16) + 4 },
      ]}
      pointerEvents="box-none"
    >
      <View style={styles.floatingCapsule}>
        {/* 1. Home Tab */}
        <Pressable
          onPress={() => handleTabPress('home')}
          style={({ pressed }) => [
            styles.tabButton,
            isHome && styles.activeTabPill,
            pressed && styles.pressedState,
          ]}
          accessibilityRole="tab"
          accessibilityState={{ selected: isHome }}
          accessibilityLabel="Home Tab"
        >
          <Ionicons
            name={isHome ? 'home' : 'home-outline'}
            size={18}
            color={isHome ? '#FFFFFF' : '#6B7280'}
            style={styles.tabIcon}
          />
          <Text
            style={[
              styles.tabLabel,
              isHome ? styles.activeLabel : styles.inactiveLabel,
            ]}
          >
            Home
          </Text>
        </Pressable>

        {/* 2. Coach Amy Tab */}
        <Pressable
          onPress={() => handleTabPress('chat')}
          style={({ pressed }) => [
            styles.tabButton,
            isChat && styles.activeChatPill,
            pressed && styles.pressedState,
          ]}
          accessibilityRole="tab"
          accessibilityState={{ selected: isChat }}
          accessibilityLabel="Coach Amy Tab"
        >
          <Ionicons
            name={isChat ? 'sparkles' : 'sparkles-outline'}
            size={18}
            color={isChat ? '#FFFFFF' : '#3B49DF'}
            style={styles.tabIcon}
          />
          <Text
            style={[
              styles.tabLabel,
              isChat ? styles.activeLabel : styles.inactiveChatLabel,
            ]}
          >
            Amy
          </Text>
        </Pressable>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  outerContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 50,
  },
  floatingCapsule: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 5,
    paddingHorizontal: 6,
    borderRadius: 9999,
    gap: 4,
    // Modern iOS elevation shadow
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.12,
    shadowRadius: 20,
    elevation: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 9,
    paddingHorizontal: 20,
    borderRadius: 9999,
  },
  activeTabPill: {
    backgroundColor: '#3B49DF',
    shadowColor: '#3B49DF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  activeChatPill: {
    backgroundColor: '#3B49DF',
    shadowColor: '#3B49DF',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  pressedState: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
  tabIcon: {
    marginRight: 6,
  },
  tabLabel: {
    fontSize: 13,
    fontWeight: '600',
    letterSpacing: 0.2,
  },
  activeLabel: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  inactiveLabel: {
    color: '#6B7280',
  },
  inactiveChatLabel: {
    color: '#3B49DF',
    fontWeight: '600',
  },
});
