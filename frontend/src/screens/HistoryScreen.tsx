import React, { useState, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, FlatList, TouchableOpacity,
  ActivityIndicator, Alert, Modal, Animated,
  TouchableWithoutFeedback, ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { Colors } from '../theme/colors';
import { getHistory, deleteReport } from '../api/api';

const TABS = ['Semua', 'Keluhan', 'Permintaan', 'Saran', 'Apresiasi', 'Darurat'];

const SENTIMENT_EMOJI: Record<string, string> = {
  positif: '😊', negatif: '😠', netral: '😐',
};
const INTENT_EMOJI: Record<string, string> = {
  keluhan: '⚠️', permintaan: '📋', saran: '💡', apresiasi: '👏', darurat: '🚨',
};
const PRIORITY_EMOJI: Record<string, string> = {
  tinggi: '🔴', sedang: '🟡', rendah: '🟢',
};

function capitalize(s: string) {
  return s ? s.charAt(0).toUpperCase() + s.slice(1) : '';
}

export default function HistoryScreen() {
  const insets = useSafeAreaInsets();
  const [activeTab, setActiveTab] = useState('Semua');
  const [reports, setReports]     = useState<any[]>([]);
  const [loading, setLoading]     = useState(true);
  const [selected, setSelected]   = useState<any | null>(null);
  const slideAnim = useRef(new Animated.Value(600)).current;

  useFocusEffect(
    useCallback(() => { loadHistory(); }, [])
  );

  const loadHistory = async () => {
    setLoading(true);
    try { setReports(await getHistory()); }
    catch { setReports([]); }
    finally { setLoading(false); }
  };

  // ── Buka bottom sheet ──────────────────────────────────
  const openDetail = (item: any) => {
    setSelected(item);
    Animated.spring(slideAnim, {
      toValue: 0,
      useNativeDriver: true,
      tension: 65,
      friction: 11,
    }).start();
  };

  // ── Tutup bottom sheet ─────────────────────────────────
  const closeDetail = () => {
    Animated.timing(slideAnim, {
      toValue: 600,
      duration: 250,
      useNativeDriver: true,
    }).start(() => setSelected(null));
  };

  // ── Hapus laporan ──────────────────────────────────────
  const handleDelete = (item: any) => {
    Alert.alert(
      'Hapus Laporan',
      `Yakin ingin menghapus laporan ini?\n\n"${item.text.length > 60 ? item.text.slice(0, 60) + '...' : item.text}"`,
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Hapus', style: 'destructive',
          onPress: async () => {
            closeDetail();
            try {
              await deleteReport(item.id);
              setReports(prev => prev.filter(r => r.id !== item.id));
            } catch {
              Alert.alert('Gagal', 'Tidak dapat menghapus laporan.');
            }
          },
        },
      ]
    );
  };

  // ── Filter berdasarkan intent ──────────────────────────
  const filtered = activeTab === 'Semua'
    ? reports
    : reports.filter(r => r.intent.toLowerCase() === activeTab.toLowerCase());

  const priorityColor = (p: string) => ({
    tinggi: Colors.priorityHigh,
    sedang: Colors.priorityMedium,
    rendah: Colors.priorityLow,
  }[p] ?? Colors.textMuted);

  const priorityBg = (p: string) => ({
    tinggi: '#FEE2E2',
    sedang: '#FEF3C7',
    rendah: '#D1FAE5',
  }[p] ?? '#F3F4F6');

  const sentimentColor = (s: string) => ({
    positif: '#10B981',
    negatif: '#EF4444',
    netral:  '#6B7280',
  }[s] ?? Colors.textMuted);

  const sentimentBg = (s: string) => ({
    positif: '#D1FAE5',
    negatif: '#FEE2E2',
    netral:  '#F3F4F6',
  }[s] ?? '#F3F4F6');

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>

      {/* ── STICKY HEADER (tidak ikut scroll) ── */}
      <View style={styles.stickyTop}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Riwayat Laporan</Text>
          <View style={styles.headerBadge}>
            <Text style={styles.headerBadgeText}>{reports.length} laporan</Text>
          </View>
        </View>
        <Text style={styles.hint}>Ketuk laporan untuk melihat detail</Text>

        {/* Tabs filter by intent */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.tabsContent}
          style={styles.tabsWrap}
        >
          {TABS.map(tab => (
            <TouchableOpacity
              key={tab}
              style={[styles.tab, activeTab === tab && styles.tabActive]}
              onPress={() => setActiveTab(tab)}
            >
              {tab !== 'Semua' && (
                <Text style={styles.tabEmoji}>
                  {INTENT_EMOJI[tab.toLowerCase()] ?? ''}
                </Text>
              )}
              <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
                {tab}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* ── LIST (flex:1 mengisi sisa layar) ── */}
      <View style={styles.listContainer}>
        {loading ? (
          <ActivityIndicator color={Colors.primary} style={{ marginTop: 40 }} />
        ) : (
          <FlatList
            data={filtered}
            keyExtractor={item => item.id.toString()}
            contentContainerStyle={{
              paddingBottom: insets.bottom + 80,
              paddingTop: 8,
              paddingHorizontal: 16,
            }}
            showsVerticalScrollIndicator={false}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.reportItem}
                onPress={() => openDetail(item)}
                activeOpacity={0.75}
              >
                {/* Kiri: emoji intent */}
                <View style={[styles.intentIcon, { backgroundColor: priorityBg(item.priority) }]}>
                  <Text style={{ fontSize: 20 }}>
                    {INTENT_EMOJI[item.intent] ?? '📄'}
                  </Text>
                </View>

                {/* Tengah: info */}
                <View style={styles.reportMain}>
                  <Text style={styles.reportTitle} numberOfLines={1}>{item.text}</Text>
                  <View style={styles.metaRow}>
                    <Text style={styles.reportIntent}>{capitalize(item.intent)}</Text>
                    <View style={styles.dot} />
                    <Text style={[styles.sentimentText, { color: sentimentColor(item.sentiment) }]}>
                      {SENTIMENT_EMOJI[item.sentiment]} {capitalize(item.sentiment)}
                    </Text>
                  </View>
                  <Text style={styles.reportDate}>{item.created_at}</Text>
                </View>

                {/* Kanan: prioritas */}
                <View style={[styles.priorityBadge, { backgroundColor: priorityBg(item.priority) }]}>
                  <Text style={[styles.priorityBadgeText, { color: priorityColor(item.priority) }]}>
                    {PRIORITY_EMOJI[item.priority]}
                  </Text>
                </View>
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.empty}>
                <Text style={{ fontSize: 48 }}>📭</Text>
                <Text style={styles.emptyTitle}>Belum ada laporan</Text>
                <Text style={styles.emptyDesc}>
                  {activeTab === 'Semua'
                    ? 'Buat laporan pertama Anda sekarang.'
                    : `Belum ada laporan dengan intent "${activeTab}".`}
                </Text>
              </View>
            }
          />
        )}
      </View>

      {/* ── BOTTOM SHEET MODAL ────────────────────────────── */}
      <Modal
        visible={!!selected}
        transparent
        animationType="none"
        onRequestClose={closeDetail}
        statusBarTranslucent
      >
        {/* Backdrop */}
        <TouchableWithoutFeedback onPress={closeDetail}>
          <View style={styles.backdrop} />
        </TouchableWithoutFeedback>

        {/* Sheet */}
        <Animated.View
          style={[
            styles.sheet,
            { paddingBottom: insets.bottom + 16 },
            { transform: [{ translateY: slideAnim }] },
          ]}
        >
          {selected && (
            <>
              {/* Handle bar */}
              <View style={styles.handleBar} />

              {/* Sheet Header */}
              <View style={styles.sheetHeader}>
                <Text style={styles.sheetTitle}>Detail Laporan #{selected.id}</Text>
                <TouchableOpacity onPress={closeDetail} style={styles.closeBtn}>
                  <Ionicons name="close" size={20} color={Colors.textPrimary} />
                </TouchableOpacity>
              </View>

              <ScrollView showsVerticalScrollIndicator={false}>

                {/* Isi laporan */}
                <View style={styles.sheetSection}>
                  <Text style={styles.sheetLabel}>Isi Laporan</Text>
                  <Text style={styles.sheetText}>{selected.text}</Text>
                </View>

                {/* Hasil analisis — 3 chip */}
                <View style={styles.sheetSection}>
                  <Text style={styles.sheetLabel}>Hasil Analisis AI</Text>
                  <View style={styles.analysisGrid}>
                    <AnalysisChip
                      label="Sentimen"
                      value={capitalize(selected.sentiment)}
                      emoji={SENTIMENT_EMOJI[selected.sentiment] ?? '😐'}
                      color={sentimentColor(selected.sentiment)}
                      bg={sentimentBg(selected.sentiment)}
                    />
                    <AnalysisChip
                      label="Intent"
                      value={capitalize(selected.intent)}
                      emoji={INTENT_EMOJI[selected.intent] ?? '🏷️'}
                      color="#3B82F6"
                      bg="#DBEAFE"
                    />
                    <AnalysisChip
                      label="Prioritas"
                      value={capitalize(selected.priority)}
                      emoji={PRIORITY_EMOJI[selected.priority] ?? '⚪'}
                      color={priorityColor(selected.priority)}
                      bg={priorityBg(selected.priority)}
                    />
                  </View>
                </View>

                {/* Sarkasme (jika terdeteksi) */}
                {selected.is_sarcasm && (
                  <View style={styles.sarcasmBanner}>
                    <Ionicons name="alert-circle" size={16} color="#92400E" />
                    <Text style={styles.sarcasmText}>
                      Terdeteksi sebagai sarkasme — dianalisis ulang sebagai keluhan negatif.
                    </Text>
                  </View>
                )}

                {/* Waktu */}
                <View style={styles.sheetSection}>
                  <Text style={styles.sheetLabel}>Waktu Kirim</Text>
                  <Text style={styles.sheetMeta}>{selected.created_at}</Text>
                </View>

                {/* Tombol Hapus */}
                <TouchableOpacity
                  style={styles.deleteBtn}
                  onPress={() => handleDelete(selected)}
                  activeOpacity={0.85}
                >
                  <Ionicons name="trash-outline" size={18} color={Colors.danger} />
                  <Text style={styles.deleteBtnText}>Hapus Laporan</Text>
                </TouchableOpacity>

              </ScrollView>
            </>
          )}
        </Animated.View>
      </Modal>
    </SafeAreaView>
  );
}

// ── Sub-komponen chip analisis ─────────────────────────
function AnalysisChip({
  label, value, emoji, color, bg,
}: {
  label: string; value: string; emoji: string; color: string; bg: string;
}) {
  return (
    <View style={[chipStyles.wrap, { backgroundColor: bg }]}>
      <Text style={chipStyles.label}>{label}</Text>
      <Text style={{ fontSize: 22, marginBottom: 4 }}>{emoji}</Text>
      <Text style={[chipStyles.value, { color }]}>{value}</Text>
    </View>
  );
}

const chipStyles = StyleSheet.create({
  wrap: {
    flex: 1,
    borderRadius: 14,
    padding: 12,
    marginRight: 8,
    alignItems: 'center',
  },
  label: {
    fontSize: 10,
    color: Colors.textMuted,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 6,
  },
  value: { fontSize: 13, fontWeight: '700' },
});

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },

  // Header + tabs sticky di atas
  stickyTop: {
    backgroundColor: Colors.background,
    paddingHorizontal: 16,
    paddingBottom: 4,
  },
  // FlatList mengisi sisa layar
  listContainer: {
    flex: 1,
  },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 4,
  },
  headerTitle: { fontSize: 22, fontWeight: '800', color: Colors.textPrimary },
  headerBadge: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  headerBadgeText: { fontSize: 12, color: Colors.primary, fontWeight: '700' },
  hint: { fontSize: 11, color: Colors.textMuted, marginBottom: 10 },

  // Tabs horizontal scroll
  tabsWrap: {
    marginBottom: 8,
  },
  tabsContent: {
    flexDirection: 'row',
    paddingBottom: 8,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.border,
    marginRight: 8,
  },
  tabActive: { backgroundColor: Colors.primary, borderColor: Colors.primary },
  tabEmoji: { fontSize: 13, marginRight: 4 },
  tabText: { fontSize: 13, color: Colors.textSecondary, fontWeight: '500' },
  tabTextActive: { color: Colors.white, fontWeight: '700' },

  // Report list item
  reportItem: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  intentIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  reportMain: { flex: 1, marginRight: 8 },
  reportTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 5,
  },
  metaRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  reportIntent: { fontSize: 12, color: Colors.textSecondary, fontWeight: '500' },
  dot: {
    width: 3,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: Colors.textMuted,
    marginHorizontal: 6,
  },
  sentimentText: { fontSize: 12, fontWeight: '500' },
  reportDate: { fontSize: 11, color: Colors.textMuted },
  priorityBadge: {
    width: 32,
    height: 32,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  priorityBadgeText: { fontSize: 16 },

  // Empty state
  empty: { alignItems: 'center', marginTop: 60, paddingHorizontal: 32 },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginTop: 12,
    marginBottom: 6,
  },
  emptyDesc: {
    fontSize: 13,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },

  // Modal
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)' },
  sheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.white,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingHorizontal: 20,
    paddingTop: 12,
    maxHeight: '80%',
    shadowColor: '#000',
    shadowOpacity: 0.15,
    shadowOffset: { width: 0, height: -4 },
    shadowRadius: 16,
    elevation: 20,
  },
  handleBar: {
    width: 40,
    height: 4,
    borderRadius: 2,
    backgroundColor: Colors.border,
    alignSelf: 'center',
    marginBottom: 16,
  },
  sheetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  sheetTitle: { fontSize: 16, fontWeight: '800', color: Colors.textPrimary },
  closeBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },

  sheetSection: { marginBottom: 20 },
  sheetLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  sheetText: { fontSize: 14, color: Colors.textPrimary, lineHeight: 22 },
  sheetMeta: { fontSize: 13, color: Colors.textSecondary },

  analysisGrid: { flexDirection: 'row' },

  sarcasmBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FEF3C7',
    borderRadius: 10,
    padding: 12,
    marginBottom: 20,
    gap: 8,
  },
  sarcasmText: {
    flex: 1,
    fontSize: 12,
    color: '#92400E',
    lineHeight: 18,
  },

  deleteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: Colors.danger,
    borderRadius: 12,
    paddingVertical: 14,
    marginBottom: 8,
    gap: 8,
  },
  deleteBtnText: { fontSize: 14, fontWeight: '700', color: Colors.danger },
});