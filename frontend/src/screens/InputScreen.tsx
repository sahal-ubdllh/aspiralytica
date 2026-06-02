import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput,
  TouchableOpacity, ScrollView,
  ActivityIndicator, Alert
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../theme/colors';
import { analyzeReport } from '../api/api';

export default function InputScreen({ navigation }: any) {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!text.trim()) {
      Alert.alert('Peringatan', 'Silakan tulis laporan Anda terlebih dahulu.');
      return;
    }
    if (text.trim().length < 10) {
      Alert.alert('Peringatan', 'Laporan terlalu singkat. Tulis minimal 10 karakter.');
      return;
    }
    setLoading(true);
    try {
      const result = await analyzeReport(text);
      navigation.navigate('Result', { result, text });
    } catch (e) {
      Alert.alert('Gagal Terhubung', 'Tidak dapat menghubungi server. Pastikan backend sudah berjalan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">

        {/* Header */}
        <View style={styles.header}>
          <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
            <Ionicons name="chevron-back" size={22} color={Colors.textPrimary} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Analisis Laporan</Text>
        </View>

        {/* Subtitle */}
        <Text style={styles.subTitle}>
          Ceritakan masalah, saran,{'\n'}atau permintaan Anda.
        </Text>
        <Text style={styles.subDesc}>
          AI akan menganalisis sentimen, intent, dan prioritas laporan Anda secara otomatis.
        </Text>

        {/* Info chip */}
        <View style={styles.infoRow}>
          <View style={styles.chip}>
            <Ionicons name="happy-outline" size={14} color={Colors.primary} />
            <Text style={styles.chipText}>Sentimen</Text>
          </View>
          <View style={styles.chip}>
            <Ionicons name="flag-outline" size={14} color={Colors.primary} />
            <Text style={styles.chipText}>Intent</Text>
          </View>
          <View style={styles.chip}>
            <Ionicons name="alert-circle-outline" size={14} color={Colors.primary} />
            <Text style={styles.chipText}>Prioritas</Text>
          </View>
        </View>

        {/* Text Input */}
        <View style={styles.card}>
          <TextInput
            style={styles.textArea}
            placeholder="Contoh: Jalan di depan sekolah rusak parah dan berbahaya untuk pengendara. Sudah dilaporkan berkali-kali tapi belum diperbaiki..."
            placeholderTextColor={Colors.textMuted}
            multiline
            maxLength={500}
            value={text}
            onChangeText={setText}
            textAlignVertical="top"
          />
          <View style={styles.cardFooter}>
            {text.length > 0 && (
              <TouchableOpacity onPress={() => setText('')}>
                <Text style={styles.clearText}>Hapus</Text>
              </TouchableOpacity>
            )}
            <Text style={[
              styles.charCount,
              text.length > 950 && { color: Colors.warning },
              text.length >= 1000 && { color: Colors.danger },
            ]}>
              {text.length}/1000
            </Text>
          </View>
        </View>

        {/* Tips */}
        <View style={styles.tipsCard}>
          <Text style={styles.tipsTitle}>💡 Tips agar analisis akurat:</Text>
          <Text style={styles.tipItem}>• Tulis dengan jelas dan spesifik</Text>
          <Text style={styles.tipItem}>• Sertakan lokasi atau konteks jika perlu</Text>
          <Text style={styles.tipItem}>• Minimal 10 karakter, maksimal 500 karakter</Text>
        </View>

        {/* Tombol Analisis */}
        <TouchableOpacity
          style={[styles.analyzeBtn, (loading || text.trim().length < 10) && styles.analyzeBtnDisabled]}
          onPress={handleAnalyze}
          disabled={loading || text.trim().length < 10}
          activeOpacity={0.85}
        >
          {loading ? (
            <View style={styles.btnInner}>
              <ActivityIndicator color={Colors.white} size="small" />
              <Text style={styles.analyzeBtnText}>Menganalisis...</Text>
            </View>
          ) : (
            <View style={styles.btnInner}>
              <Ionicons name="analytics-outline" size={20} color={Colors.white} />
              <Text style={styles.analyzeBtnText}>Analisis Laporan</Text>
            </View>
          )}
        </TouchableOpacity>

      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.white },
  container: { flex: 1, paddingHorizontal: 20 },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 8,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.background,
    justifyContent: 'center', alignItems: 'center',
    marginRight: 12,
  },
  headerTitle: { fontSize: 18, fontWeight: '700', color: Colors.textPrimary },

  subTitle: {
    fontSize: 22,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginTop: 16,
    marginBottom: 8,
    lineHeight: 30,
  },
  subDesc: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginBottom: 16,
  },

  infoRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.primaryLight,
    borderRadius: 20,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginRight: 8,
  },
  chipText: {
    fontSize: 12,
    color: Colors.primary,
    fontWeight: '600',
    marginLeft: 4,
  },

  card: {
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    minHeight: 180,
    backgroundColor: Colors.white,
  },
  textArea: {
    fontSize: 14,
    color: Colors.textPrimary,
    lineHeight: 22,
    minHeight: 140,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    alignItems: 'center',
    marginTop: 8,
  },
  clearText: {
    fontSize: 12,
    color: Colors.danger,
    marginRight: 12,
  },
  charCount: {
    fontSize: 12,
    color: Colors.textMuted,
  },

  tipsCard: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 12,
    padding: 14,
    marginBottom: 24,
  },
  tipsTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: Colors.primary,
    marginBottom: 6,
  },
  tipItem: {
    fontSize: 12,
    color: Colors.primaryDark,
    lineHeight: 20,
  },

  analyzeBtn: {
    backgroundColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: 'center',
    marginBottom: 32,
  },
  analyzeBtnDisabled: {
    backgroundColor: Colors.accent,
    opacity: 0.6,
  },
  btnInner: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  analyzeBtnText: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.white,
    marginLeft: 8,
  },
});