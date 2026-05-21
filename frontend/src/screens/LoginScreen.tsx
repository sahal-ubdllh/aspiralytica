import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Image,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaView } from "react-native-safe-area-context";
import { Colors } from "../theme/colors";
import { loginUser } from "../api/auth";

export default function LoginScreen({ navigation }: any) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert("Peringatan", "Email dan password wajib diisi.");
      return;
    }
    setLoading(true);
    try {
      await loginUser(email.trim(), password);
      navigation.replace("Main");
    } catch (e: any) {
      Alert.alert("Login Gagal", e.message || "Email atau password salah.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.container}
          keyboardShouldPersistTaps="handled"
        >
          {/* Logo */}
          <View style={styles.logoArea}>
            <Image
              source={require("../../assets/icon.png")}
              style={styles.logoImage}
            />
            <Text style={styles.appName}>Aspiralytica</Text>
            <Text style={styles.tagline}>Masuk ke akun Anda</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <Text style={styles.label}>Email</Text>
            <View style={styles.inputWrap}>
              <Ionicons
                name="mail-outline"
                size={18}
                color={Colors.textMuted}
                style={styles.inputIcon}
              />
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
              <Ionicons
                name="lock-closed-outline"
                size={18}
                color={Colors.textMuted}
                style={styles.inputIcon}
              />
              <TextInput
                style={styles.input}
                placeholder="Masukkan password"
                placeholderTextColor={Colors.textMuted}
                value={password}
                onChangeText={setPassword}
                secureTextEntry={!showPass}
              />
              <TouchableOpacity
                onPress={() => setShowPass(!showPass)}
                style={styles.eyeBtn}
              >
                <Ionicons
                  name={showPass ? "eye-off-outline" : "eye-outline"}
                  size={18}
                  color={Colors.textMuted}
                />
              </TouchableOpacity>
            </View>

            <TouchableOpacity style={styles.forgotBtn}>
              <Text style={styles.forgotText}>Lupa password?</Text>
            </TouchableOpacity>

            {/* Tombol Login */}
            <TouchableOpacity
              style={[styles.btnPrimary, loading && { opacity: 0.7 }]}
              onPress={handleLogin}
              disabled={loading}
              activeOpacity={0.85}
            >
              <Text style={styles.btnPrimaryText}>
                {loading ? "Memproses..." : "Masuk"}
              </Text>
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>Belum punya akun? </Text>
            <TouchableOpacity onPress={() => navigation.navigate("Register")}>
              <Text style={styles.footerLink}>Daftar sekarang</Text>
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

  logoArea: { alignItems: "center", paddingTop: 40, paddingBottom: 32 },
  logoCircle: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  logoLetter: { fontSize: 36, fontWeight: "800", color: Colors.white },
  appName: {
    fontSize: 26,
    fontWeight: "800",
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  logoImage: {
    width: 72,
    height: 72,
    borderRadius: 20,
  },
  tagline: { fontSize: 14, color: Colors.textSecondary },

  form: { flex: 1 },
  label: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.textPrimary,
    marginBottom: 8,
  },
  inputWrap: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 12,
    paddingHorizontal: 12,
    marginBottom: 16,
    backgroundColor: Colors.white,
  },
  inputIcon: { marginRight: 8 },
  input: {
    flex: 1,
    paddingVertical: 14,
    fontSize: 14,
    color: Colors.textPrimary,
  },
  eyeBtn: { padding: 4 },

  forgotBtn: { alignSelf: "flex-end", marginBottom: 24, marginTop: -8 },
  forgotText: { fontSize: 13, color: Colors.primary, fontWeight: "600" },

  btnPrimary: {
    backgroundColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginBottom: 16,
  },
  btnPrimaryText: { fontSize: 16, fontWeight: "700", color: Colors.white },

  divider: { flexDirection: "row", alignItems: "center", marginBottom: 16 },
  dividerLine: { flex: 1, height: 1, backgroundColor: Colors.border },
  dividerText: { fontSize: 13, color: Colors.textMuted, marginHorizontal: 12 },

  btnGuest: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1.5,
    borderColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 14,
  },
  btnGuestText: {
    fontSize: 14,
    fontWeight: "600",
    color: Colors.primary,
    marginLeft: 6,
  },

  footer: { flexDirection: "row", justifyContent: "center", paddingTop: 24 },
  footerText: { fontSize: 14, color: Colors.textSecondary },
  footerLink: { fontSize: 14, color: Colors.primary, fontWeight: "700" },
});
