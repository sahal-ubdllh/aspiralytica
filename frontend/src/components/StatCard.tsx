import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme/colors';

interface StatCardProps {
  value: number;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  iconColor: string;
  iconBg: string;
}

export default function StatCard({
  value,
  label,
  icon,
  iconColor,
  iconBg,
}: StatCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.value}>{value}</Text>
      <View style={styles.bottom}>
        <Text style={styles.label}>{label}</Text>
        <View style={[styles.iconWrap, { backgroundColor: iconBg }]}>
          <Ionicons name={icon} size={16} color={iconColor} />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    // Pakai width 48% dan margin 1% di setiap sisi → total 2% per card = 4% jarak antar 2 card
    // Hasilnya mirip gap: 10 tapi tanpa pakai gap
    width: '48%',
    backgroundColor: Colors.background,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
  },
  value: {
    fontSize: 28,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginBottom: 6,
  },
  bottom: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  label: {
    fontSize: 12,
    color: Colors.textSecondary,
    flexShrink: 1,
    marginRight: 4,
  },
  iconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
});