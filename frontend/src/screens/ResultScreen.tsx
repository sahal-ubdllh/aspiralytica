import React from 'react';
import {
  View, Text, StyleSheet,
  TouchableOpacity, ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../theme/colors';

interface ResultScreenProps {
  navigation: any;
  route: any;
}

export default function ResultScreen({ navigation, route }: ResultScreenProps) {
  const { result, text } = route.params ?? {};

  const sentimentConfig: Record<string, { icon: string; color: string; bg: string; label: string }> = {
    positif:  { icon: '😊', color: '#10B981', bg: '#D1FAE5', label: 'Positif'  },
    negatif:  { icon: '😔', color: '#EF4444', bg: '#FEE2E2', label: 'Negatif'  },
    netral:   { icon: '😐', color: '#6B7280', bg: '#F3F4F6', label: 'Netral'   },
  };

  const priorityConfig: Record<string, { color: string; bg: string; label: string }> = {
    tinggi: { color: Colors.priorityHigh,   bg: '#FEE2E2', label: 'Tinggi' },
    sedang: { color: Colors.priorityMedium, bg: '#FEF3C7', label: 'Sedang' },
    rendah: { color: Colors.priorityLow,    bg: '#D1FAE5', label: 'Rendah' },
  };

  const intentConfig: Record<string, { icon: keyof typeof Ionicons.glyphMap; color: string; bg: string }> = {
    keluhan:    { icon: 'warning-outline',          color: '#EF4444', bg: '#FEE2E2' },
    permintaan: { icon: 'hand-left-outline',        color: '#3B82F6', bg: '#DBEAFE' },
    saran:      { icon: 'bulb-outline',             color: '#F59E0B', bg: '#FEF3C7' },
    apresiasi:  { icon: 'heart-outline',            color: '#10B981', bg: '#D1FAE5' },
    darurat:    { icon: 'alert-circle-outline',     color: '#DC2626', bg: '#FEE2E2' },
  };

  const sent    = sentimentConfig[result?.sentiment]  ?? sentimentConfig['netral'];
  const prio    = priorityConfig[result?.priority]    ?? { color: Colors.textMuted, bg: '#F3F4F6', label: '-' };
  const intent  = intentConfig[result?.intent]        ?? { icon: 'help-circle-outline', color: Colors.textMuted, bg: '#F3F4F6' };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        style={styles.container}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 32 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => navigation.navigate('Main')}
            style={styles.backBtn}
          >
            <Ionicons name="chevron-back" size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Hasil Analisis</Text>
        </View>

        {/* Success banner */}
        <View style={styles.successBanner}>
          <Text style={styles.successIcon}>✅</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.successTitle}>Laporan Berhasil Dikirim</Text>
            <Text style={styles.successSub}>ID Laporan: #{result?.id ?? '-'}</Text>
          </View>
        </View>

        {/* Teks laporan */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Isi Laporan</Text>
          <Text style={styles.reportText}>{text ?? result?.text ?? '-'}</Text>
          <Text style={styles.reportDate}>{result?.created_at ?? ''}</Text>
        </View>

        {/* Sentimen */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Sentimen</Text>
          <View style={[styles.badgeLarge, { backgroundColor: sent.bg }]}>
            <Text style={styles.badgeEmoji}>{sent.icon}</Text>
            <Text style={[styles.badgeText, { color: sent.color }]}>{sent.label}</Text>
          </View>
        </View>

        {/* Intent & Prioritas */}
        <View style={styles.row}>
          {/* Intent */}
          <View style={[styles.card, styles.halfCard]}>
            <Text style={styles.cardLabel}>Intent</Text>
            <View style={[styles.iconCircle, { backgroundColor: intent.bg }]}>
              <Ionicons name={intent.icon} size={24} color={intent.color} />
            </View>
            <Text style={[styles.intentText, { color: intent.color }]}>
              {result?.intent
                ? result.intent.charAt(0).toUpperCase() + result.intent.slice(1)
                : '-'}
            </Text>
          </View>

          {/* Prioritas */}
          <View style={[styles.card, styles.halfCard]}>
            <Text style={styles.cardLabel}>Prioritas</Text>
            <View style={[styles.iconCircle, { backgroundColor: prio.bg }]}>
              <Ionicons name="flag" size={24} color={prio.color} />
            </View>
            <Text style={[styles.intentText, { color: prio.color }]}>{prio.label}</Text>
          </View>
        </View>

        {/* Status */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>Status Laporan</Text>
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>Menunggu ditindaklanjuti</Text>
          </View>
          <Text style={styles.statusDesc}>
            Laporan Anda telah diterima dan sedang dalam antrian untuk diproses oleh tim terkait.
          </Text>
        </View>

        {/* Tombol */}
        <TouchableOpacity
          style={styles.btnPrimary}
          onPress={() => navigation.navigate('Input')}
          activeOpacity={0.85}
        >
          <Ionicons name="add-circle-outline" size={20} color={Colors.white} />
          <Text style={styles.btnPrimaryText}>Buat Laporan Baru</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.btnSecondary}
          onPress={() => navigation.navigate('Main')}
          activeOpacity={0.8}
        >
          <Text style={styles.btnSecondaryText}>Kembali ke Beranda</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  container: { flex: 1, paddingHorizontal: 16 },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 12,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.white,
    justifyContent: 'center', alignItems: 'center',
    marginRight: 12,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: Colors.textPrimary },

  successBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#D1FAE5',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
  },
  successIcon: { fontSize: 28, marginRight: 12 },
  successTitle: { fontSize: 14, fontWeight: '700', color: '#065F46' },
  successSub: { fontSize: 12, color: '#047857', marginTop: 2 },

  card: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000', shadowOpacity: 0.04, shadowRadius: 6, elevation: 1,
  },
  cardLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  reportText: {
    fontSize: 14,
    color: Colors.textPrimary,
    lineHeight: 22,
    marginBottom: 8,
  },
  reportDate: { fontSize: 11, color: Colors.textMuted },

  badgeLarge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
  badgeEmoji: { fontSize: 20, marginRight: 8 },
  badgeText: { fontSize: 16, fontWeight: '700' },

  row: { flexDirection: 'row', justifyContent: 'space-between' },
  halfCard: { width: '48.5%' },
  iconCircle: {
    width: 48, height: 48, borderRadius: 24,
    justifyContent: 'center', alignItems: 'center',
    marginBottom: 8,
  },
  intentText: { fontSize: 14, fontWeight: '700' },

  statusRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  statusDot: {
    width: 10, height: 10, borderRadius: 5,
    backgroundColor: Colors.statusPending,
    marginRight: 8,
  },
  statusText: { fontSize: 14, fontWeight: '600', color: Colors.statusPending },
  statusDesc: { fontSize: 13, color: Colors.textSecondary, lineHeight: 20 },

  btnPrimary: {
    backgroundColor: Colors.primary,
    borderRadius: 14, paddingVertical: 16,
    flexDirection: 'row',
    justifyContent: 'center', alignItems: 'center',
    marginBottom: 10,
  },
  btnPrimaryText: { fontSize: 15, fontWeight: '700', color: Colors.white, marginLeft: 8 },

  btnSecondary: {
    borderWidth: 1.5, borderColor: Colors.border,
    borderRadius: 14, paddingVertical: 14,
    alignItems: 'center',
  },
  btnSecondaryText: { fontSize: 15, fontWeight: '600', color: Colors.textSecondary },
});