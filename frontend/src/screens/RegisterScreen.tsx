import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TextInput,
  TouchableOpacity, ScrollView, Alert,
  KeyboardAvoidingView, Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../theme/colors';
import { registerUser } from '../api/auth';

export default function RegisterScreen({ navigation }: any) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPass, setConfirmPass] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name.trim() || !email.trim() || !password.trim()) {
      Alert.alert('Peringatan', 'Semua field wajib diisi.');
      return;
    }
    if (password !== confirmPass) {
      Alert.alert('Peringatan', 'Password dan konfirmasi password tidak sama.');
      return;
    }
    if (password.length < 6) {
      Alert.alert('Peringatan', 'Password minimal 6 karakter.');
      return;
    }
    setLoading(true);
    try {
      await registerUser(name.trim(), email.trim(), password);
      Alert.alert('Berhasil!', 'Akun berhasil dibuat. Silakan login.', [
        { text: 'Login', onPress: () => navigation.replace('Login') },
      ]);
    } catch (e: any) {
      Alert.alert('Pendaftaran Gagal', e.message || 'Terjadi kesalahan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">

          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
              <Ionicons name="chevron-back" size={22} color={Colors.textPrimary} />
            </TouchableOpacity>
            <View>
              <Text style={styles.headerTitle}>Buat Akun</Text>
              <Text style={styles.headerSub}>Daftar untuk mulai menggunakan Aspiralytica</Text>
            </View>
          </View>

          {/* Form */}
          <View style={styles.form}>

            <Text style={styles.label}>Nama Lengkap</Text>
            <View style={styles.inputWrap}>
              <Ionicons name="person-outline" size={18} color={Colors.textMuted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Nama lengkap Anda"
                placeholderTextColor={Colors.textMuted}
                value={name}
                onChangeText={setName}
                autoCapitalize="words"
              />
            </View>

            <Text style={styles.label}>Email</Text>
            <View style={styles.inputWrap}>
              <Ionicons name="mail-outline" size={18} color={Colors.textMuted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="nama@email.com"
                placeholderTextColor={Colors.textMuted}
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
              />
            </View>

            <Text style={styles.label}>Password</Text>
            <View style={styles.inputWrap}>
              <Ionicons name="lock-closed-outline" size={18} color={Colors.textMuted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Minimal 6 karakter"
                placeholderTextColor={Colors.textMuted}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPass}
              />
              <TouchableOpacity onPress={() => setShowPass(!showPass)} style={styles.eyeBtn}>
                <Ionicons name={showPass ? 'eye-off-outline' : 'eye-outline'} size={18} color={Colors.textMuted} />
              </TouchableOpacity>
            </View>

            <Text style={styles.label}>Konfirmasi Password</Text>
            <View style={[
              styles.inputWrap,
              confirmPass.length > 0 && confirmPass !== password && { borderColor: Colors.danger },
            ]}>
              <Ionicons name="lock-closed-outline" size={18} color={Colors.textMuted} style={styles.inputIcon} />
              <TextInput
                style={styles.input}
                placeholder="Ulangi password"
                placeholderTextColor={Colors.textMuted}
                value={confirmPass}
                onChangeText={setConfirmPass}
                secureTextEntry={!showConfirm}
              />
              <TouchableOpacity onPress={() => setShowConfirm(!showConfirm)} style={styles.eyeBtn}>
                <Ionicons name={showConfirm ? 'eye-off-outline' : 'eye-outline'} size={18} color={Colors.textMuted} />
              </TouchableOpacity>
            </View>
            {confirmPass.length > 0 && confirmPass !== password && (
              <Text style={styles.errorText}>Password tidak sama</Text>
            )}

            <TouchableOpacity
              style={[styles.btnPrimary, loading && { opacity: 0.7 }]}
              onPress={handleRegister}
              disabled={loading}
              activeOpacity={0.85}
            >
              <Text style={styles.btnPrimaryText}>
                {loading ? 'Mendaftar...' : 'Daftar'}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>Sudah punya akun? </Text>
            <TouchableOpacity onPress={() => navigation.navigate('Login')}>
              <Text style={styles.footerLink}>Masuk</Text>
            </TouchableOpacity>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.white },
  container: { flexGrow: 1, paddingHorizontal: 24, paddingBottom: 32 },

  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 24,
  },
  backBtn: {
    width: 36, height: 36, borderRadius: 10,
    backgroundColor: Colors.background,
    justifyContent: 'center', alignItems: 'center',
    marginRight: 12,
  },
  headerTitle: { fontSize: 20, fontWeight: '800', color: Colors.textPrimary },
  headerSub: { fontSize: 13, color: Colors.textSecondary, marginTop: 2 },

  form: { flex: 1 },
  label: { fontSize: 14, fontWeight: '600', color: Colors.textPrimary, marginBottom: 8 },
  inputWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 12,
    marginBottom: 16,
  },
  inputIcon: { marginRight: 8 },
  input: { flex: 1, paddingVertical: 14, fontSize: 14, color: Colors.textPrimary },
  eyeBtn: { padding: 4 },
  errorText: { fontSize: 12, color: Colors.danger, marginTop: -12, marginBottom: 12 },

  btnPrimary: {
    backgroundColor: Colors.primary,
    borderRadius: 14, paddingVertical: 16,
    alignItems: 'center', marginTop: 8,
  },
  btnPrimaryText: { fontSize: 16, fontWeight: '700', color: Colors.white },

  footer: { flexDirection: 'row', justifyContent: 'center', paddingTop: 24 },
  footerText: { fontSize: 14, color: Colors.textSecondary },
  footerLink: { fontSize: 14, color: Colors.primary, fontWeight: '700' },
});