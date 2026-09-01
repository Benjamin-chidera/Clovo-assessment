import React, { useEffect } from 'react';
import { ScrollView, View } from 'react-native';
import { useRouter } from 'expo-router';
import { HeroBanner } from '@/components/home/HeroBanner';
import { GreetingBadges } from '@/components/home/GreetingBadges';
import { PrimaryCheckInCTA } from '@/components/home/PrimaryCheckInCTA';
import { MilestoneCard } from '@/components/home/MilestoneCard';
import { PendingTasksList } from '@/components/home/PendingTasksList';
import { ProfileModal } from '@/components/home/ProfileModal';
import { useAuthStore } from '@/stores/useAuthStore';
import { useSocketStore } from '@/stores/useSocketStore';
import { useUserStore } from '@/stores/useUserStore';
import { useTaskStore } from '@/stores/useTaskStore';

export default function HomeScreen() {
  const router = useRouter();
  const { isAuthenticated, openProfileModal } = useAuthStore();
  const { fetchUser } = useUserStore();
  const { fetchTasks } = useTaskStore();

  const { isConnected } = useSocketStore();

  useEffect(() => {
    fetchUser();
    fetchTasks();
  }, [fetchUser, fetchTasks]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.replace('/login');
    }
  }, [isAuthenticated, router]);

  const handleCheckInPress = () => {
    router.push('/chat');
  };

  const handleMilestonePress = () => {
    router.push('/chat');
  };

  const handleSwitchProfile = () => {
    openProfileModal();
  };

  return (
    <View className="flex-1 bg-[#F8F9FD]">
      <ScrollView
        className="flex-1"
        showsVerticalScrollIndicator={false}
      >
        {/* A. Hero Banner Header */}
        <HeroBanner onSwitchProfile={handleSwitchProfile} />

        {/* B. Greeting & Streak Section */}
        <GreetingBadges />

        {/* C. Primary Action CTA ("Check in with Amy") */}
        <PrimaryCheckInCTA onPress={handleCheckInPress} />

        {/* D. Milestone Announcement Dark Card */}
        <MilestoneCard onPress={handleMilestonePress} />

        {/* E. Pending Daily Tasks Section */}
        <PendingTasksList />
      </ScrollView>

      {/* Profile & Logout Action Sheet Popup Modal */}
      <ProfileModal />
    </View>
  );
}
