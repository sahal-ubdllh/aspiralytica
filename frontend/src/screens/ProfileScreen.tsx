import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  ScrollView, Alert, TextInput, Switch,
  Modal, Animated, Dimensions, KeyboardAvoidingView,
  Platform, ActivityIndicator
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../theme/colors';
import { getHistory } from '../api/api';
import { getCurrentUser, logoutUser } from '../api/auth';

const { height: SCREEN_HEIGHT } = Dimensions.get('window');

// ─── Types ─────────────────────────────────────────────────────────────────
type PanelType =
  | 'editProfile'
  | 'notifications'
  | 'privacy'
  | 'help'
  | 'about'
  | null;

interface MenuItem {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  panel: PanelType;
  color?: string;
  badge?: string;
}

// ─── Bottom Sheet Panel ─────────────────────────────────────────────────────
function BottomPanel({
  visible,
  onClose,
  title,
  children,
}: {
  visible: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  const slideAnim = useRef(new Animated.Value(SCREEN_HEIGHT)).current;
  const backdropAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
          tension: 65,
          friction: 11,
        }),
        Animated.timing(backdropAnim, {
          toValue: 1,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(slideAnim, {
          toValue: SCREEN_HEIGHT,
          duration: 280,
          useNativeDriver: true,
        }),
        Animated.timing(backdropAnim, {
          toValue: 0,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <Modal transparent animationType="none" visible={visible} onRequestClose={onClose}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Backdrop */}
        <Animated.View
          style={[styles.backdrop, { opacity: backdropAnim }]}
        >
          <TouchableOpacity style={{ flex: 1 }} onPress={onClose} activeOpacity={1} />
        </Animated.View>

        {/* Panel */}
        <Animated.View
          style={[styles.panel, { transform: [{ translateY: slideAnim }] }]}
        >
          {/* Handle */}
          <View style={styles.panelHandle} />

          {/* Panel Header */}
          <View style={styles.panelHeader}>
            <Text style={styles.panelTitle}>{title}</Text>
            <TouchableOpacity onPress={onClose} style={styles.panelCloseBtn} activeOpacity={0.7}>
              <Ionicons name="close" size={20} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>

          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={{ paddingBottom: 40 }}
            keyboardShouldPersistTaps="handled"
          >
            {children}
          </ScrollView>
        </Animated.View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

// ─── Edit Profile Panel ─────────────────────────────────────────────────────
function EditProfilePanel({
  user,
  onClose,
  onSave,
}: {
  user: any;
  onClose: () => void;
  onSave: (name: string, email: string, bio: string) => void;
}) {
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [loading, setLoading] = useState(false);

  const handleSave = async () => {
    if (!name.trim()) {
      Alert.alert('Peringatan', 'Nama tidak boleh kosong.');
      return;
    }
    setLoading(true);
    await new Promise((r) => setTimeout(r, 800)); // simulate API
    setLoading(false);
    onSave(name.trim(), email.trim(), bio.trim());
    Alert.alert('Berhasil', 'Profil berhasil diperbarui!');
    onClose();
  };

  return (
    <View style={styles.panelBody}>
      {/* Avatar Preview */}
      <View style={styles.editAvatarWrap}>
        <View style={styles.editAvatarCircle}>
          <Text style={styles.editAvatarText}>
            {name ? name.charAt(0).toUpperCase() : '?'}
          </Text>
        </View>
        <TouchableOpacity style={styles.editAvatarBadge} activeOpacity={0.8}
          onPress={() => Alert.alert('Info', 'Fitur ganti foto akan segera hadir.')}>
          <Ionicons name="camera" size={14} color={Colors.white} />
        </TouchableOpacity>
      </View>

      {/* Fields */}
      <Text style={styles.fieldLabel}>Nama Lengkap</Text>
      <View style={styles.inputWrap}>
        <Ionicons name="person-outline" size={18} color={Colors.textMuted} style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          value={name}
          onChangeText={setName}
          placeholder="Masukkan nama lengkap"
          placeholderTextColor={Colors.textMuted}
        />
      </View>

      <Text style={styles.fieldLabel}>Email</Text>
      <View style={styles.inputWrap}>
        <Ionicons name="mail-outline" size={18} color={Colors.textMuted} style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          value={email}
          onChangeText={setEmail}
          placeholder="Masukkan email"
          placeholderTextColor={Colors.textMuted}
          keyboardType="email-address"
          autoCapitalize="none"
        />
      </View>

      <Text style={styles.fieldLabel}>Bio</Text>
      <View style={[styles.inputWrap, { alignItems: 'flex-start', paddingTop: 10 }]}>
        <Ionicons name="create-outline" size={18} color={Colors.textMuted} style={[styles.inputIcon, { marginTop: 2 }]} />
        <TextInput
          style={[styles.input, { height: 80, textAlignVertical: 'top' }]}
          value={bio}
          onChangeText={setBio}
          placeholder="Ceritakan sedikit tentang diri Anda..."
          placeholderTextColor={Colors.textMuted}
          multiline
        />
      </View>

      <TouchableOpacity
        style={[styles.saveBtn, loading && { opacity: 0.7 }]}
        onPress={handleSave}
        activeOpacity={0.85}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color={Colors.white} size="small" />
        ) : (
          <>
            <Ionicons name="checkmark" size={18} color={Colors.white} />
            <Text style={styles.saveBtnText}>Simpan Perubahan</Text>
          </>
        )}
      </TouchableOpacity>
    </View>
  );
}

// ─── Notifications Panel ────────────────────────────────────────────────────
function NotificationsPanel() {
  const [settings, setSettings] = useState({
    newReport: true,
    aiUpdate: false,
    weeklyDigest: true,
    security: true,
    marketing: false,
    email: true,
    push: true,
    inApp: true,
  });

  const toggle = (key: keyof typeof settings) =>
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));

  const sections = [
    {
      title: 'Aktivitas',
      items: [
        { key: 'newReport', label: 'Laporan baru diproses', desc: 'Notifikasi saat laporan Anda selesai dianalisis' },
        { key: 'aiUpdate', label: 'Pembaruan AI', desc: 'Update model & fitur AI terbaru' },
        { key: 'weeklyDigest', label: 'Ringkasan Mingguan', desc: 'Rekap aktivitas setiap Senin pagi' },
      ],
    },
    {
      title: 'Keamanan',
      items: [
        { key: 'security', label: 'Peringatan Keamanan', desc: 'Login baru atau aktivitas mencurigakan' },
      ],
    },
    {
      title: 'Saluran',
      items: [
        { key: 'push', label: 'Push Notification', desc: 'Notifikasi langsung ke perangkat' },
        { key: 'email', label: 'Email', desc: 'Kirim notifikasi ke email terdaftar' },
        { key: 'inApp', label: 'Dalam Aplikasi', desc: 'Tampilkan di dalam aplikasi' },
        { key: 'marketing', label: 'Promosi & Promo', desc: 'Penawaran dan info produk baru' },
      ],
    },
  ];

  return (
    <View style={styles.panelBody}>
      {sections.map((section) => (
        <View key={section.title} style={{ marginBottom: 24 }}>
          <Text style={styles.sectionLabel}>{section.title}</Text>
          <View style={styles.settingCard}>
            {section.items.map((item, i) => (
              <React.Fragment key={item.key}>
                <View style={styles.settingRow}>
                  <View style={{ flex: 1, marginRight: 8 }}>
                    <Text style={styles.settingRowLabel}>{item.label}</Text>
                    <Text style={styles.settingRowDesc}>{item.desc}</Text>
                  </View>
                  <Switch
                    value={settings[item.key as keyof typeof settings]}
                    onValueChange={() => toggle(item.key as keyof typeof settings)}
                    trackColor={{ false: Colors.border, true: Colors.primary }}
                    thumbColor={Colors.white}
                  />
                </View>
                {i < section.items.length - 1 && <View style={styles.menuDivider} />}
              </React.Fragment>
            ))}
          </View>
        </View>
      ))}
    </View>
  );
}

// ─── Privacy Panel ──────────────────────────────────────────────────────────
function PrivacyPanel() {
  const [privacy, setPrivacy] = useState({
    dataCollection: true,
    analytics: false,
    locationAccess: false,
    shareStats: false,
    twoFactor: false,
  });

  const toggle = (key: keyof typeof privacy) =>
    setPrivacy((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleChangePassword = () =>
    Alert.alert('Ganti Kata Sandi', 'Link reset kata sandi akan dikirim ke email Anda.', [
      { text: 'Batal', style: 'cancel' },
      { text: 'Kirim', onPress: () => Alert.alert('Terkirim', 'Cek email Anda.') },
    ]);

  const handleDeleteAccount = () =>
    Alert.alert(
      '⚠️ Hapus Akun',
      'Tindakan ini permanen. Semua data Anda akan dihapus dan tidak dapat dipulihkan.',
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Hapus Akun',
          style: 'destructive',
          onPress: () => Alert.alert('Info', 'Silakan hubungi support untuk melanjutkan.'),
        },
      ]
    );

  return (
    <View style={styles.panelBody}>
      <Text style={styles.sectionLabel}>Keamanan Akun</Text>
      <View style={styles.settingCard}>
        <View style={styles.settingRow}>
          <View style={{ flex: 1, marginRight: 8 }}>
            <Text style={styles.settingRowLabel}>Autentikasi Dua Faktor</Text>
            <Text style={styles.settingRowDesc}>Tambahkan lapisan keamanan ekstra</Text>
          </View>
          <Switch
            value={privacy.twoFactor}
            onValueChange={() => toggle('twoFactor')}
            trackColor={{ false: Colors.border, true: Colors.primary }}
            thumbColor={Colors.white}
          />
        </View>
        <View style={styles.menuDivider} />
        <TouchableOpacity style={styles.settingActionRow} onPress={handleChangePassword} activeOpacity={0.7}>
          <View style={{ flex: 1 }}>
            <Text style={styles.settingRowLabel}>Ganti Kata Sandi</Text>
            <Text style={styles.settingRowDesc}>Ubah kata sandi akun Anda</Text>
          </View>
          <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
        </TouchableOpacity>
      </View>

      <Text style={styles.sectionLabel}>Data & Privasi</Text>
      <View style={styles.settingCard}>
        {[
          { key: 'dataCollection', label: 'Pengumpulan Data', desc: 'Izinkan pengumpulan data untuk meningkatkan layanan' },
          { key: 'analytics', label: 'Analitik Penggunaan', desc: 'Bantu kami memahami pola penggunaan aplikasi' },
          { key: 'locationAccess', label: 'Akses Lokasi', desc: 'Untuk fitur berbasis lokasi' },
          { key: 'shareStats', label: 'Bagikan Statistik', desc: 'Kontribusi data anonim untuk penelitian publik' },
        ].map((item, i, arr) => (
          <React.Fragment key={item.key}>
            <View style={styles.settingRow}>
              <View style={{ flex: 1, marginRight: 8 }}>
                <Text style={styles.settingRowLabel}>{item.label}</Text>
                <Text style={styles.settingRowDesc}>{item.desc}</Text>
              </View>
              <Switch
                value={privacy[item.key as keyof typeof privacy]}
                onValueChange={() => toggle(item.key as keyof typeof privacy)}
                trackColor={{ false: Colors.border, true: Colors.primary }}
                thumbColor={Colors.white}
              />
            </View>
            {i < arr.length - 1 && <View style={styles.menuDivider} />}
          </React.Fragment>
        ))}
      </View>

      <Text style={styles.sectionLabel}>Zona Berbahaya</Text>
      <TouchableOpacity style={styles.dangerBtn} onPress={handleDeleteAccount} activeOpacity={0.8}>
        <Ionicons name="trash-outline" size={18} color={Colors.danger} />
        <Text style={styles.dangerBtnText}>Hapus Akun Saya</Text>
      </TouchableOpacity>
    </View>
  );
}

// ─── Help Panel ─────────────────────────────────────────────────────────────
const FAQ_ITEMS = [
  {
    q: 'Apa itu Aspiralytica?',
    a: 'Aspiralytica adalah aplikasi berbasis AI yang membantu menganalisis aspirasi dan laporan masyarakat secara otomatis menggunakan teknologi kecerdasan buatan.',
  },
  {
    q: 'Bagaimana cara membuat laporan?',
    a: 'Buka tab "Buat Laporan", isi formulir dengan detail aspirasi Anda, lalu kirim. AI kami akan menganalisis dan memproses laporan dalam hitungan detik.',
  },
  {
    q: 'Apakah data saya aman?',
    a: 'Ya, seluruh data dienkripsi dan disimpan dengan standar keamanan tinggi. Kami tidak pernah menjual data pengguna kepada pihak ketiga.',
  },
  {
    q: 'Berapa lama proses analisis AI?',
    a: 'Analisis biasanya selesai dalam 5–30 detik tergantung kompleksitas laporan. Anda akan mendapat notifikasi saat selesai.',
  },
  {
    q: 'Bisakah saya mengedit laporan yang sudah dikirim?',
    a: 'Saat ini laporan yang sudah dikirim tidak dapat diedit. Anda dapat membuat laporan baru atau hubungi tim support kami.',
  },
];

function HelpPanel() {
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <View style={styles.panelBody}>
      {/* Contact */}
      <Text style={styles.sectionLabel}>Hubungi Kami</Text>
      <View style={styles.settingCard}>
        {[
          { icon: 'mail-outline' as const, label: 'Email Support', value: 'support@aspiralytica.id' },
          { icon: 'logo-whatsapp' as const, label: 'WhatsApp', value: '+62 812 3456 7890' },
          { icon: 'time-outline' as const, label: 'Jam Operasional', value: 'Sen–Jum, 08.00–17.00 WIB' },
        ].map((c, i, arr) => (
          <React.Fragment key={c.label}>
            <View style={styles.contactRow}>
              <View style={styles.contactIconWrap}>
                <Ionicons name={c.icon} size={18} color={Colors.primary} />
              </View>
              <View>
                <Text style={styles.contactLabel}>{c.label}</Text>
                <Text style={styles.contactValue}>{c.value}</Text>
              </View>
            </View>
            {i < arr.length - 1 && <View style={styles.menuDivider} />}
          </React.Fragment>
        ))}
      </View>

      {/* FAQ */}
      <Text style={styles.sectionLabel}>FAQ</Text>
      <View style={styles.settingCard}>
        {FAQ_ITEMS.map((faq, i) => (
          <React.Fragment key={i}>
            <TouchableOpacity
              style={styles.faqRow}
              onPress={() => setExpanded(expanded === i ? null : i)}
              activeOpacity={0.7}
            >
              <Text style={styles.faqQ} numberOfLines={expanded === i ? undefined : 1}>
                {faq.q}
              </Text>
              <Ionicons
                name={expanded === i ? 'chevron-up' : 'chevron-down'}
                size={16}
                color={Colors.textMuted}
              />
            </TouchableOpacity>
            {expanded === i && (
              <Text style={styles.faqA}>{faq.a}</Text>
            )}
            {i < FAQ_ITEMS.length - 1 && <View style={styles.menuDivider} />}
          </React.Fragment>
        ))}
      </View>
    </View>
  );
}

// ─── About Panel ─────────────────────────────────────────────────────────────
function AboutPanel() {
  return (
    <View style={styles.panelBody}>
      <View style={styles.aboutLogoWrap}>
        <View style={styles.aboutLogo}>
          <Ionicons name="bar-chart" size={36} color={Colors.white} />
        </View>
        <Text style={styles.aboutAppName}>Aspiralytica</Text>
        <Text style={styles.aboutTagline}>AI-Powered Public Insight</Text>
        <View style={styles.versionBadge}>
          <Text style={styles.versionBadgeText}>Versi 1.0.0</Text>
        </View>
      </View>

      <Text style={styles.sectionLabel}>Tentang</Text>
      <View style={styles.settingCard}>
        <Text style={styles.aboutDesc}>
          Aspiralytica adalah aplikasi tugas akhir mahasiswa Informatika yang memanfaatkan
          kecerdasan buatan untuk menganalisis aspirasi dan laporan masyarakat secara
          otomatis, cepat, dan akurat.
        </Text>
      </View>

      <Text style={styles.sectionLabel}>Teknologi</Text>
      <View style={styles.settingCard}>
        {[
          { label: 'Platform', value: 'React Native + Expo' },
          { label: 'Backend', value: 'Node.js / REST API' },
          { label: 'AI Engine', value: 'Large Language Model' },
          { label: 'Dikembangkan oleh', value: 'Tim Informatika' },
          { label: 'Lisensi', value: 'MIT License' },
        ].map((item, i, arr) => (
          <React.Fragment key={item.label}>
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>{item.label}</Text>
              <Text style={styles.infoValue}>{item.value}</Text>
            </View>
            {i < arr.length - 1 && <View style={styles.menuDivider} />}
          </React.Fragment>
        ))}
      </View>

      <Text style={styles.aboutFooter}>
        © 2026 Aspiralytica. Dibuat dengan ❤️ untuk masyarakat.
      </Text>
    </View>
  );
}

// ─── Main Profile Screen ─────────────────────────────────────────────────────
export default function ProfileScreen({ navigation }: any) {
  const [reportCount, setReportCount] = useState(0);
  const [activePanel, setActivePanel] = useState<PanelType>(null);
  const [userInfo, setUserInfo] = useState(getCurrentUser());

  useEffect(() => {
    loadCount();
  }, []);

  const loadCount = async () => {
    try {
      const data = await getHistory();
      setReportCount(data.length);
    } catch {}
  };

  const handleLogout = () => {
    Alert.alert(
      'Keluar',
      'Apakah Anda yakin ingin keluar?',
      [
        { text: 'Batal', style: 'cancel' },
        {
          text: 'Keluar',
          style: 'destructive',
          onPress: () => {
            logoutUser();
            navigation.replace('Login');
          },
        },
      ]
    );
  };

  const menuItems: MenuItem[] = [
    { icon: 'person-outline', label: 'Edit Profil', panel: 'editProfile' },
    { icon: 'notifications-outline', label: 'Notifikasi', panel: 'notifications' },
    { icon: 'shield-checkmark-outline', label: 'Privasi & Keamanan', panel: 'privacy' },
    { icon: 'help-circle-outline', label: 'Bantuan & FAQ', panel: 'help' },
    { icon: 'information-circle-outline', label: 'Tentang Aplikasi', panel: 'about' },
  ];

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingBottom: 32 }}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Akun</Text>
        </View>

        {/* Avatar & Info */}
        <View style={styles.profileCard}>
          <TouchableOpacity
            onPress={() => setActivePanel('editProfile')}
            activeOpacity={0.85}
            style={{ alignItems: 'center' }}
          >
            <View style={styles.avatarCircle}>
              <Text style={styles.avatarText}>
                {userInfo?.name ? userInfo.name.charAt(0).toUpperCase() : '?'}
              </Text>
              <View style={styles.avatarEditBadge}>
                <Ionicons name="pencil" size={10} color={Colors.white} />
              </View>
            </View>
          </TouchableOpacity>
          <Text style={styles.profileName}>{userInfo?.name || 'Pengguna Tamu'}</Text>
          <Text style={styles.profileEmail}>{userInfo?.email || 'Belum login'}</Text>
          {userInfo?.bio ? (
            <Text style={styles.profileBio}>{userInfo.bio}</Text>
          ) : null}

          {/* Stats */}
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{reportCount}</Text>
              <Text style={styles.statLabel}>Laporan</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>AI</Text>
              <Text style={styles.statLabel}>Analisis</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>v1.0</Text>
              <Text style={styles.statLabel}>Versi</Text>
            </View>
          </View>
        </View>

        {/* Menu */}
        <View style={styles.menuCard}>
          {menuItems.map((item, index) => (
            <React.Fragment key={item.label}>
              <TouchableOpacity
                style={styles.menuItem}
                onPress={() => setActivePanel(item.panel)}
                activeOpacity={0.7}
              >
                <View style={styles.menuIconWrap}>
                  <Ionicons name={item.icon} size={20} color={item.color || Colors.primary} />
                </View>
                <Text style={[styles.menuLabel, item.color && { color: item.color }]}>
                  {item.label}
                </Text>
                {item.badge && (
                  <View style={styles.badgeWrap}>
                    <Text style={styles.badgeText}>{item.badge}</Text>
                  </View>
                )}
                <Ionicons name="chevron-forward" size={16} color={Colors.textMuted} />
              </TouchableOpacity>
              {index < menuItems.length - 1 && <View style={styles.menuDivider} />}
            </React.Fragment>
          ))}
        </View>

        {/* Logout */}
        <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.85}>
          <Ionicons name="log-out-outline" size={20} color={Colors.danger} />
          <Text style={styles.logoutText}>Keluar</Text>
        </TouchableOpacity>

        <Text style={styles.version}>Aspiralytica v1.0.0 • AI-Powered Public Insight</Text>
      </ScrollView>

      {/* ── Edit Profil Panel ── */}
      <BottomPanel
        visible={activePanel === 'editProfile'}
        onClose={() => setActivePanel(null)}
        title="Edit Profil"
      >
        <EditProfilePanel
          user={userInfo}
          onClose={() => setActivePanel(null)}
          onSave={(name, email, bio) =>
            setUserInfo((prev: any) => ({ ...prev, name, email, bio }))
          }
        />
      </BottomPanel>

      {/* ── Notifikasi Panel ── */}
      <BottomPanel
        visible={activePanel === 'notifications'}
        onClose={() => setActivePanel(null)}
        title="Pengaturan Notifikasi"
      >
        <NotificationsPanel />
      </BottomPanel>

      {/* ── Privasi Panel ── */}
      <BottomPanel
        visible={activePanel === 'privacy'}
        onClose={() => setActivePanel(null)}
        title="Privasi & Keamanan"
      >
        <PrivacyPanel />
      </BottomPanel>

      {/* ── Bantuan Panel ── */}
      <BottomPanel
        visible={activePanel === 'help'}
        onClose={() => setActivePanel(null)}
        title="Bantuan & FAQ"
      >
        <HelpPanel />
      </BottomPanel>

      {/* ── Tentang Panel ── */}
      <BottomPanel
        visible={activePanel === 'about'}
        onClose={() => setActivePanel(null)}
        title="Tentang Aplikasi"
      >
        <AboutPanel />
      </BottomPanel>
    </SafeAreaView>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.background },

  // Header
  header: { paddingHorizontal: 16, paddingTop: 16, paddingBottom: 12 },
  headerTitle: { fontSize: 22, fontWeight: '800', color: Colors.textPrimary },

  // Profile Card
  profileCard: {
    backgroundColor: Colors.white,
    marginHorizontal: 16,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    marginBottom: 14,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 2,
  },
  avatarCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarText: { fontSize: 32, fontWeight: '800', color: Colors.white },
  avatarEditBadge: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: Colors.primary,
    borderWidth: 2,
    borderColor: Colors.white,
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileName: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  profileEmail: { fontSize: 13, color: Colors.textSecondary, marginBottom: 4 },
  profileBio: {
    fontSize: 12,
    color: Colors.textMuted,
    textAlign: 'center',
    marginBottom: 8,
    fontStyle: 'italic',
  },

  // Stats
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.background,
    borderRadius: 12,
    padding: 14,
    width: '100%',
    marginTop: 8,
  },
  statItem: { flex: 1, alignItems: 'center' },
  statValue: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.primary,
    marginBottom: 2,
  },
  statLabel: { fontSize: 11, color: Colors.textSecondary },
  statDivider: { width: 1, height: 30, backgroundColor: Colors.border },

  // Menu Card
  menuCard: {
    backgroundColor: Colors.white,
    marginHorizontal: 16,
    borderRadius: 16,
    paddingHorizontal: 16,
    marginBottom: 14,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 8,
    elevation: 2,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
  },
  menuIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  menuLabel: { flex: 1, fontSize: 14, fontWeight: '500', color: Colors.textPrimary },
  menuDivider: { height: 1, backgroundColor: Colors.border },
  badgeWrap: {
    backgroundColor: Colors.primary,
    borderRadius: 10,
    paddingHorizontal: 7,
    paddingVertical: 2,
    marginRight: 6,
  },
  badgeText: { fontSize: 10, color: Colors.white, fontWeight: '700' },

  // Logout
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 16,
    backgroundColor: Colors.white,
    borderRadius: 14,
    paddingVertical: 16,
    borderWidth: 1.5,
    borderColor: Colors.danger,
    marginBottom: 16,
  },
  logoutText: { fontSize: 15, fontWeight: '700', color: Colors.danger, marginLeft: 8 },
  version: { textAlign: 'center', fontSize: 12, color: Colors.textMuted },

  // Bottom Panel
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(0,0,0,0.45)',
  },
  panel: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: Colors.white,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: SCREEN_HEIGHT * 0.88,
    paddingBottom: Platform.OS === 'ios' ? 20 : 0,
  },
  panelHandle: {
    width: 40,
    height: 4,
    backgroundColor: Colors.border,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 12,
    marginBottom: 4,
  },
  panelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  panelTitle: {
    flex: 1,
    fontSize: 17,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  panelCloseBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  panelBody: { paddingHorizontal: 20, paddingTop: 20 },

  // Section label
  sectionLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  settingCard: {
    backgroundColor: Colors.background,
    borderRadius: 14,
    paddingHorizontal: 14,
    marginBottom: 20,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
  },
  settingActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
  },
  settingRowLabel: { fontSize: 14, fontWeight: '600', color: Colors.textPrimary, marginBottom: 2 },
  settingRowDesc: { fontSize: 12, color: Colors.textMuted },

  // Edit Profile
  editAvatarWrap: { alignSelf: 'center', marginBottom: 24 },
  editAvatarCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  editAvatarText: { fontSize: 36, fontWeight: '800', color: Colors.white },
  editAvatarBadge: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: Colors.primary,
    borderWidth: 2,
    borderColor: Colors.white,
    justifyContent: 'center',
    alignItems: 'center',
  },
  fieldLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: Colors.textSecondary,
    marginBottom: 6,
    marginLeft: 2,
  },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.background,
    borderRadius: 12,
    marginBottom: 16,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  inputIcon: { marginRight: 8 },
  input: {
    flex: 1,
    fontSize: 14,
    color: Colors.textPrimary,
    paddingVertical: 13,
  },
  saveBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 15,
    marginTop: 4,
    gap: 8,
  },
  saveBtnText: { fontSize: 15, fontWeight: '700', color: Colors.white },

  // Danger Zone
  dangerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.white,
    borderRadius: 14,
    paddingVertical: 15,
    borderWidth: 1.5,
    borderColor: Colors.danger,
    marginBottom: 8,
    gap: 8,
  },
  dangerBtnText: { fontSize: 15, fontWeight: '700', color: Colors.danger },

  // Help Panel
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 13,
    gap: 12,
  },
  contactIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
  },
  contactLabel: { fontSize: 12, color: Colors.textMuted, marginBottom: 1 },
  contactValue: { fontSize: 14, fontWeight: '600', color: Colors.textPrimary },
  faqRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    gap: 8,
  },
  faqQ: { flex: 1, fontSize: 14, fontWeight: '600', color: Colors.textPrimary },
  faqA: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
    paddingBottom: 12,
    paddingTop: 2,
  },

  // About
  aboutLogoWrap: { alignItems: 'center', marginBottom: 24 },
  aboutLogo: {
    width: 80,
    height: 80,
    borderRadius: 22,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  aboutAppName: { fontSize: 22, fontWeight: '800', color: Colors.textPrimary, marginBottom: 4 },
  aboutTagline: { fontSize: 13, color: Colors.textSecondary, marginBottom: 10 },
  versionBadge: {
    backgroundColor: Colors.primaryLight,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 20,
  },
  versionBadgeText: { fontSize: 12, fontWeight: '700', color: Colors.primary },
  aboutDesc: {
    fontSize: 13,
    color: Colors.textSecondary,
    lineHeight: 20,
    paddingVertical: 14,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
  },
  infoLabel: { fontSize: 13, color: Colors.textSecondary },
  infoValue: { fontSize: 13, fontWeight: '600', color: Colors.textPrimary },
  aboutFooter: {
    textAlign: 'center',
    fontSize: 12,
    color: Colors.textMuted,
    marginTop: 4,
    marginBottom: 8,
  },
});