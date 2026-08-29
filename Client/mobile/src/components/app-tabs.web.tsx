import {
  Tabs,
  TabList,
  TabTrigger,
  TabSlot,
  TabTriggerSlotProps,
  TabListProps,
} from 'expo-router/ui';
import { Ionicons } from '@expo/vector-icons';
import { Pressable, View, StyleSheet, Text } from 'react-native';
import { ClovoColors, Spacing, MaxContentWidth } from '@/constants/theme';

export default function AppTabs() {
  return (
    <Tabs>
      <TabSlot style={{ height: '100%' }} />
      <TabList asChild>
        <CustomTabList>
          <TabTrigger name="home" href="/" asChild>
            <TabButton icon="home">Home</TabButton>
          </TabTrigger>
          <TabTrigger name="chat" href="/chat" asChild>
            <TabButton icon="chatbubble-ellipses">Coach Chat</TabButton>
          </TabTrigger>
        </CustomTabList>
      </TabList>
    </Tabs>
  );
}

interface TabButtonProps extends TabTriggerSlotProps {
  icon: keyof typeof Ionicons.glyphMap;
}

export function TabButton({ children, isFocused, icon, ...props }: TabButtonProps) {
  return (
    <Pressable {...props} style={({ pressed }) => pressed && styles.pressed}>
      <View
        style={[
          styles.tabButtonView,
          isFocused ? styles.tabButtonActive : styles.tabButtonInactive,
        ]}>
        <Ionicons
          name={icon}
          size={16}
          color={isFocused ? '#FFFFFF' : ClovoColors.textSecondary}
        />
        <Text
          style={[
            styles.tabText,
            isFocused ? styles.tabTextActive : styles.tabTextInactive,
          ]}>
          {children}
        </Text>
      </View>
    </Pressable>
  );
}

export function CustomTabList(props: TabListProps) {
  return (
    <View {...props} style={styles.tabListContainer}>
      <View style={styles.innerContainer}>
        <View style={styles.brandContainer}>
          <Text style={styles.brandText}>CLOVO</Text>
        </View>
        <View style={styles.buttonsRow}>{props.children}</View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  tabListContainer: {
    position: 'absolute',
    bottom: 0,
    width: '100%',
    padding: Spacing.three,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
  },
  innerContainer: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 9999,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    maxWidth: 400,
    width: '100%',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  brandContainer: {
    paddingHorizontal: 8,
  },
  brandText: {
    fontWeight: '800',
    fontSize: 13,
    color: ClovoColors.primary,
    letterSpacing: 1.5,
  },
  buttonsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  pressed: {
    opacity: 0.8,
  },
  tabButtonView: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 9999,
    gap: 6,
  },
  tabButtonActive: {
    backgroundColor: ClovoColors.primary,
  },
  tabButtonInactive: {
    backgroundColor: '#F3F4F6',
  },
  tabText: {
    fontSize: 13,
    fontWeight: '600',
  },
  tabTextActive: {
    color: '#FFFFFF',
  },
  tabTextInactive: {
    color: ClovoColors.textSecondary,
  },
});
