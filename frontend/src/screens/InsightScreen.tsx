import React, { useCallback, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { Colors } from '../theme/colors';
import { getHistory } from '../api/api';

interface Report {
  id: number;
  text: string;
  sentiment: string;
  intent: string;
  priority: string;
  status: string;
  created_at: string;
}

interface InsightData {
  total: number;
  sentiment: Record<string, number>;
  intent: Record<string, number>;
  priority: Record<string, number>;
  status: Record<string, number>;
}

// ── Bar item ────────────────────────────────────────────────
function BarItem({
  label, value, total, color, emoji,
}: {
  label: string; value: number; total: number; color: string; emoji: string;
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0;
  return (
    <View style={barStyles.row}>
      <View style={barStyles.labelWrap}>
        <Text style={barStyles.emoji}>{emoji}</Text>
        <Text style={barStyles.label}>{label}</Text>
      </View>
      <View style={barStyles.barBg}>
        <View style={[barStyles.barFill, { width: `${Math.max(pct, value > 0 ? 2 : 0)}%`, backgroundColor: color }]} />
      </View>
      <View style={barStyles.rightWrap}>
        <Text style={[barStyles.pct, { color }]}>{pct}%</Text>
        <Text style={barStyles.count}>({value})</Text>
      </View>
    </View>
  );
}

const barStyles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 12 },
  labelWrap: { flexDirection: 'row', alignItems: 'center', width: 95 },
  emoji: { fontSize: 14, marginRight: 4 },
  label: { fontSize: 12, color: Colors.textSecondary, fontWeight: '500', flexShrink: 1 },
  barBg: {
    flex: 1, height: 10, borderRadius: 5,
    backgroundColor: Colors.border,
    marginHorizontal: 10, overflow: 'hidden',
  },
  barFill: { height: 10, borderRadius: 5 },
  rightWrap: {
    flexDirection: 'row', alignItems: 'center',
    width: 60, justifyContent: 'flex-end',
  },
  pct: { fontSize: 12, fontWeight: '700', marginRight: 2 },
  count: { fontSize: 11, color: Colors.textMuted },
});

// ── Summary chip ────────────────────────────────────────────
function SummaryChip({
  icon, label, value, color, bg,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string; value: string | number; color: string; bg: string;
}) {
  return (
    <View style={[chipStyles.wrap, { backgroundColor: bg }]}>
      <View style={[chipStyles.iconWrap, { backgroundColor: color + '22' }]}>
        <Ionicons name={icon} size={18} color={color} />
      </View>
      <Text style={[chipStyles.value, { color }]}>{value}</Text>
      <Text style={chipStyles.label}>{label}</Text>
    </View>
  );
}

const chipStyles = StyleSheet.create({
  wrap: {
    width: '48.5%',
    borderRadius: 14, padding: 14,
    marginBottom: 10,
    alignItems: 'flex-start',
  },
  iconWrap: {
    width: 36, height: 36, borderRadius: 10,
    justifyContent: 'center', alignItems: 'center',
    marginBottom: 10,
  },
  value: { fontSize: 24, fontWeight: '800', marginBottom: 2 },
  label: { fontSize: 11, color: Colors.textSecondary, fontWeight: '500' },
});

// ── Main Screen ─────────────────────────────────────────────
export default function InsightScreen() {
  const insets = useSafeAreaInsets();
  const [data, setData]               = useState<InsightData | null>(null);
  const [loading, setLoading]         = useState(true);
  const [recentReports, setRecent]    = useState<Report[]>([]);

  useFocusEffect(
    useCallback(() => { loadData(); }, [])
  );

  const loadData = async () => {
    setLoading(true);
    try {
      const reports: Report[] = await getHistory();
      setRecent(reports.slice(0, 3));

      const insight: InsightData = {
        total: reports.length,
        sentiment: { positif: 0, negatif: 0, netral: 0 },
        intent: { keluhan: 0, permintaan: 0, saran: 0, apresiasi: 0, darurat: 0 },
        priority: { tinggi: 0, sedang: 0, rendah: 0 },
        status: { menunggu: 0, diproses: 0, selesai: 0 },
      };

      reports.forEach((r) => {
        if (r.sentiment in insight.sentiment) insight.sentiment[r.sentiment]++;
        if (r.intent    in insight.intent)    insight.intent[r.intent]++;
        if (r.priority  in insight.priority)  insight.priority[r.priority]++;
        if (r.status    in insight.status)    insight.status[r.status]++;
      });

      setData(insight);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const capitalize = (s: string) => s ? s.charAt(0).toUpperCase() + s.slice(1) : '';

  const dominantSentiment = data
    ? capitalize(Object.entries(data.sentiment).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '-')
    : '-';
  const dominantIntent = data
    ? capitalize(Object.entries(data.intent).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '-')
    : '-';

  return (
    // edges={['top']} — hanya safe area atas, bawah dihandle tab navigator
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: insets.bottom + 80 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Insight & Analitik</Text>
          <View style={styles.headerRight}>
            <View style={styles.headerBadge}>
              <Ionicons name="bar-chart" size={13} color={Colors.primary} />
              <Text style={styles.headerBadgeText}>Live</Text>
            </View>
            <TouchableOpacity onPress={loadData} style={styles.refreshBtn}>
              <Ionicons name="refresh-outline" size={20} color={Colors.primary} />
            </TouchableOpacity>
          </View>
        </View>

        {loading ? (
          <ActivityIndicator color={Colors.primary} style={{ marginTop: 60 }} />

        ) : data === null || data.total === 0 ? (
          <View style={styles.emptyWrap}>
            <Text style={{ fontSize: 52 }}>📊</Text>
            <Text style={styles.emptyTitle}>Belum ada data</Text>
            <Text style={styles.emptyDesc}>
              Kirimkan laporan pertama Anda untuk melihat insight dan analitik di sini.
            </Text>
          </View>

        ) : (
          <View style={styles.content}>

            {/* Summary chips — 2 kolom */}
            <View style={styles.chipsRow}>
              <SummaryChip
                icon="document-text" label="Total Laporan"
                value={data.total} color="#7C3AED" bg="#EDE9FE"
              />
              <SummaryChip
                icon="alert-circle" label="Prioritas Tinggi"
                value={data.priority.tinggi} color="#EF4444" bg="#FEE2E2"
              />
            </View>
            <View style={styles.chipsRow}>
              <SummaryChip
                icon="happy" label="Sentimen Dominan"
                value={dominantSentiment} color="#10B981" bg="#D1FAE5"
              />
              <SummaryChip
                icon="flag" label="Intent Terbanyak"
                value={dominantIntent} color="#F59E0B" bg="#FEF3C7"
              />
            </View>

            {/* Ringkasan teks otomatis */}
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>🤖 Ringkasan AI</Text>
              <Text style={styles.summaryText}>
                Dari <Text style={styles.bold}>{data.total} laporan</Text>, sentimen terbanyak adalah{' '}
                <Text style={styles.bold}>{dominantSentiment}</Text> dan intent dominan adalah{' '}
                <Text style={styles.bold}>{dominantIntent}</Text>.{' '}
                {data.priority.tinggi > 0
                  ? `⚠️ Terdapat ${data.priority.tinggi} laporan prioritas TINGGI yang perlu segera ditindaklanjuti.`
                  : '✅ Tidak ada laporan prioritas tinggi saat ini.'}
              </Text>
            </View>

            {/* Distribusi Sentimen */}
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Distribusi Sentimen</Text>
                <Text style={styles.cardSub}>{data.total} laporan</Text>
              </View>
              <BarItem label="Positif" value={data.sentiment.positif} total={data.total} color="#10B981" emoji="😊" />
              <BarItem label="Negatif" value={data.sentiment.negatif} total={data.total} color="#EF4444" emoji="😔" />
              <BarItem label="Netral"  value={data.sentiment.netral}  total={data.total} color="#6B7280" emoji="😐" />
            </View>

            {/* Distribusi Intent */}
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Distribusi Intent</Text>
                <Text style={styles.cardSub}>{data.total} laporan</Text>
              </View>
              <BarItem label="Keluhan"    value={data.intent.keluhan}    total={data.total} color="#EF4444" emoji="⚠️" />
              <BarItem label="Permintaan" value={data.intent.permintaan} total={data.total} color="#3B82F6" emoji="🙏" />
              <BarItem label="Saran"      value={data.intent.saran}      total={data.total} color="#F59E0B" emoji="💡" />
              <BarItem label="Apresiasi"  value={data.intent.apresiasi}  total={data.total} color="#10B981" emoji="❤️" />
              <BarItem label="Darurat"    value={data.intent.darurat}    total={data.total} color="#DC2626" emoji="🚨" />
            </View>

            {/* Distribusi Prioritas */}
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Distribusi Prioritas</Text>
              </View>
              <BarItem label="Tinggi" value={data.priority.tinggi} total={data.total} color={Colors.priorityHigh}   emoji="🔴" />
              <BarItem label="Sedang" value={data.priority.sedang} total={data.total} color={Colors.priorityMedium} emoji="🟡" />
              <BarItem label="Rendah" value={data.priority.rendah} total={data.total} color={Colors.priorityLow}    emoji="🟢" />
            </View>

            {/* Status Laporan */}
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Status Laporan</Text>
              </View>
              <BarItem label="Menunggu" value={data.status.menunggu} total={data.total} color={Colors.statusPending}   emoji="⏳" />
              <BarItem label="Diproses" value={data.status.diproses} total={data.total} color={Colors.statusProcessed} emoji="⚙️" />
              <BarItem label="Selesai"  value={data.status.selesai}  total={data.total} color={Colors.statusDone}      emoji="✅" />
            </View>

            {/* Laporan Terbaru */}
            {recentReports.length > 0 && (
              <View style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>Laporan Terbaru</Text>
                </View>
                {recentReports.map((r, i) => (
                  <View key={r.id}>
                    <View style={styles.recentItem}>
                      <View style={styles.recentLeft}>
                        <Text style={styles.recentText} numberOfLines={1}>{r.text}</Text>
                        <Text style={styles.recentMeta}>
                          {capitalize(r.intent)} • {capitalize(r.priority)} priority
                        </Text>
                      </View>
                      <View style={[
                        styles.recentBadge,
                        {
                          backgroundColor:
                            r.sentiment === 'positif' ? '#D1FAE5'
                            : r.sentiment === 'negatif' ? '#FEE2E2'
                            : '#F3F4F6',
                        },
                      ]}>
                        <Text style={{ fontSize: 16 }}>
                          {r.sentiment === 'positif' ? '😊' : r.sentiment === 'negatif' ? '😔' : '😐'}
                        </Text>
                      </View>
                    </View>
                    {i < recentReports.length - 1 && <View style={styles.divider} />}
                  </View>
                ))}
              </View>
            )}

          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },
  content: { paddingHorizontal: 16 },

  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 14,
  },
  headerTitle: { fontSize: 22, fontWeight: '800', color: Colors.textPrimary },
  headerRight: { flexDirection: 'row', alignItems: 'center' },
  headerBadge: {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: Colors.primaryLight,
    borderRadius: 20, paddingHorizontal: 10, paddingVertical: 4,
    marginRight: 8,
  },
  headerBadgeText: { fontSize: 12, color: Colors.primary, fontWeight: '700', marginLeft: 4 },
  refreshBtn: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center', alignItems: 'center',
  },

  emptyWrap: { alignItems: 'center', marginTop: 80, paddingHorizontal: 32 },
  emptyTitle: { fontSize: 18, fontWeight: '700', color: Colors.textPrimary, marginTop: 12, marginBottom: 8 },
  emptyDesc: { fontSize: 13, color: Colors.textSecondary, textAlign: 'center', lineHeight: 20 },

  // Chips — space-between agar 2 chip sejajar dengan jarak
  chipsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },

  summaryCard: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 16, padding: 16, marginBottom: 12,
  },
  summaryTitle: { fontSize: 13, fontWeight: '700', color: Colors.primary, marginBottom: 6 },
  summaryText: { fontSize: 13, color: Colors.primaryDark, lineHeight: 20 },
  bold: { fontWeight: '700' },

  card: {
    backgroundColor: Colors.white,
    borderRadius: 16, padding: 16, marginBottom: 12,
    shadowColor: '#000', shadowOpacity: 0.04,
    shadowOffset: { width: 0, height: 2 }, shadowRadius: 6, elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: 14,
  },
  cardTitle: { fontSize: 15, fontWeight: '700', color: Colors.textPrimary },
  cardSub: { fontSize: 12, color: Colors.textMuted },

  recentItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 10 },
  recentLeft: { flex: 1, marginRight: 10 },
  recentText: { fontSize: 13, fontWeight: '600', color: Colors.textPrimary, marginBottom: 3 },
  recentMeta: { fontSize: 11, color: Colors.textSecondary },
  recentBadge: {
    width: 34, height: 34, borderRadius: 17,
    justifyContent: 'center', alignItems: 'center',
  },
  divider: { height: 1, backgroundColor: Colors.border },
});