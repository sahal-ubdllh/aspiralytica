import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { Colors } from '../theme/colors';
import { getHistory } from '../api/api';
import StatCard from '../components/StatCard';

interface Stats {
  total: number;
  menunggu: number;
  diproses: number;
  selesai: number;
}

export default function HomeScreen({ navigation }: any) {
  const [stats, setStats] = useState<Stats>({
    total: 0,
    menunggu: 0,
    diproses: 0,
    selesai: 0,
  });

  useFocusEffect(
    useCallback(() => {
      loadStats();
    }, [])
  );

  const loadStats = async () => {
    try {
      const data = await getHistory();
      setStats({
        total: data.length,
        menunggu: data.filter((r: any) => r.status === 'menunggu').length,
        diproses: data.filter((r: any) => r.status === 'diproses').length,
        selesai: data.filter((r: any) => r.status === 'selesai').length,
      });
    } catch {
      // server belum nyala, biarkan default 0
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        style={styles.container}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 32 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Beranda</Text>
          <TouchableOpacity style={styles.notifBtn}>
            <Ionicons
              name="notifications-outline"
              size={22}
              color={Colors.textPrimary}
            />
          </TouchableOpacity>
        </View>

        {/* Welcome Banner */}
        <View style={styles.banner}>
          <Text style={styles.bannerTitle}>Halo, Selamat Datang! 👋</Text>
          <Text style={styles.bannerSubtitle}>
            Bersama Aspiralytica, wujudkan{'\n'}layanan publik yang lebih baik.
          </Text>
        </View>

        {/* Kirim Laporan Card */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Kirim Laporan</Text>
          <TouchableOpacity
            style={styles.newReportBtn}
            onPress={() => navigation.navigate('Input')}
            activeOpacity={0.8}
          >
            <View style={styles.newReportIcon}>
              <Ionicons name="add" size={28} color={Colors.white} />
            </View>
            <View style={styles.newReportText}>
              <Text style={styles.newReportTitle}>Buat Laporan Baru</Text>
              <Text style={styles.newReportSub}>
                Sampaikan keluhan, saran, atau permintaan Anda di sini.
              </Text>
            </View>
          </TouchableOpacity>
        </View>

        {/* Ringkasan */}
        <View style={styles.card}>
          <View style={styles.summaryHeader}>
            <Text style={styles.sectionTitle}>Ringkasan Hari Ini</Text>
            <TouchableOpacity onPress={() => navigation.navigate('Riwayat')}>
              <Text style={styles.viewAll}>Lihat Semua ›</Text>
            </TouchableOpacity>
          </View>

          {/* Pakai justifyContent: 'space-between' — tidak perlu gap */}
          <View style={styles.statsGrid}>
            <StatCard
              value={stats.total}
              label="Total Laporan"
              icon="document-text"
              iconColor="#7C3AED"
              iconBg="#EDE9FE"
            />
            <StatCard
              value={stats.menunggu}
              label="Menunggu"
              icon="time"
              iconColor="#F59E0B"
              iconBg="#FEF3C7"
            />
          </View>
          <View style={styles.statsGrid}>
            <StatCard
              value={stats.diproses}
              label="Diproses"
              icon="sync"
              iconColor="#3B82F6"
              iconBg="#DBEAFE"
            />
            <StatCard
              value={stats.selesai}
              label="Selesai"
              icon="checkmark-circle"
              iconColor="#10B981"
              iconBg="#D1FAE5"
            />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 14,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.textPrimary,
  },
  notifBtn: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: Colors.white,
    justifyContent: 'center',
    alignItems: 'center',
  },
  banner: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 20,
    marginBottom: 14,
  },
  bannerTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.white,
    marginBottom: 6,
  },
  bannerSubtitle: {
    fontSize: 13,
    color: '#DDD6FE',
    lineHeight: 20,
  },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 12,
  },
  newReportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.background,
    borderRadius: 12,
    padding: 14,
  },
  newReportIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  newReportText: {
    flex: 1,
  },
  newReportTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  newReportSub: {
    fontSize: 12,
    color: Colors.textSecondary,
    lineHeight: 16,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  viewAll: {
    fontSize: 13,
    color: Colors.primary,
    fontWeight: '600',
  },
  // 2 card per baris, pakai space-between — tanpa gap
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
});