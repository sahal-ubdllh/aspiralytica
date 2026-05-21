import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Colors } from '../theme/colors';

interface HistoryItemProps {
  item: {
    id: number;
    text: string;
    intent: string;
    priority: string;
    status: string;
    created_at: string;
  };
  onPress?: () => void;
}

const PRIORITY_COLOR: Record<string, string> = {
  tinggi: Colors.priorityHigh,
  sedang: Colors.priorityMedium,
  rendah: Colors.priorityLow,
};

const STATUS_COLOR: Record<string, string> = {
  menunggu: Colors.statusPending,
  diproses: Colors.statusProcessed,
  selesai: Colors.statusDone,
};

function capitalize(str: string) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export default function HistoryItem({ item, onPress }: HistoryItemProps) {
  const priorityColor = PRIORITY_COLOR[item.priority] ?? Colors.textMuted;
  const statusColor = STATUS_COLOR[item.status] ?? Colors.textMuted;

  return (
    <TouchableOpacity style={styles.container} onPress={onPress} activeOpacity={0.7}>
      {/* Kiri */}
      <View style={styles.left}>
        <Text style={styles.title} numberOfLines={1}>
          {item.text}
        </Text>
        <View style={styles.metaRow}>
          <Text style={styles.intent}>{capitalize(item.intent)}</Text>
          <Text style={styles.dotSeparator}> • </Text>
          <View style={[styles.dot2, { backgroundColor: priorityColor }]} />
          <Text style={[styles.priorityText, { color: priorityColor }]}>
            {' '}{capitalize(item.priority)}
          </Text>
        </View>
        <Text style={styles.date}>{item.created_at}</Text>
      </View>

      {/* Kanan */}
      <View style={styles.right}>
        <Text style={[styles.status, { color: statusColor }]}>
          {capitalize(item.status)}
        </Text>
        <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  left: {
    flex: 1,
    marginRight: 12,
  },
  title: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 4,
  },
  intent: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  dotSeparator: {
    fontSize: 12,
    color: Colors.textMuted,
  },
  dot2: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
  },
  date: {
    fontSize: 11,
    color: Colors.textMuted,
  },
  right: {
    alignItems: 'flex-end',
  },
  status: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
});