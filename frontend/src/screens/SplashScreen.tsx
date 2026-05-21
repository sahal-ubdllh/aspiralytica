import React from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  Image,
} from "react-native";
import { Colors } from "../theme/colors";

const { width } = Dimensions.get("window");

export default function SplashScreen({ navigation }: any) {
  return (
    <View style={styles.container}>
      {/* Logo */}
      <View style={styles.logoArea}>
        <Image
          source={require("../../assets/icon.png")}
          style={styles.logoImage}
        />
        <Text style={styles.appName}>Aspiralytica</Text>
        <Text style={styles.tagline}>
          Suara Anda, Prioritas Kami,{"\n"}Solusi untuk Negeri.
        </Text>
      </View>

      {/* Tombol */}
      <View style={styles.buttonArea}>
        <TouchableOpacity
          style={styles.btnPrimary}
          onPress={() => navigation.navigate("Login")}
          activeOpacity={0.85}
        >
          <Text style={styles.btnPrimaryText}>Masuk</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.btnSecondary}
          onPress={() => navigation.navigate("Register")}
          activeOpacity={0.85}
        >
          <Text style={styles.btnSecondaryText}>Daftar</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.white,
    paddingHorizontal: 24,
    justifyContent: "space-between",
    paddingTop: 250,
    paddingBottom: 250,
  },
  logoArea: {
    alignItems: "center",
  },
  logoCircle: {
    width: 90,
    height: 90,
    borderRadius: 45,
    backgroundColor: Colors.primary,
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  appName: {
    fontSize: 28,
    fontWeight: "800",
    color: Colors.textPrimary,
    marginBottom: 8,
  },
  tagline: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: "center",
    lineHeight: 20,
  },
  logoImage: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  buttonArea: {
    flexDirection: "column",
  },
  btnPrimary: {
    backgroundColor: Colors.primary,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginBottom: 12,
  },
  btnPrimaryText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: "700",
  },
  btnSecondary: {
    borderWidth: 1.5,
    borderColor: Colors.border,
    borderRadius: 14,
    paddingVertical: 16,
    alignItems: "center",
    marginBottom: 8,
  },
  btnSecondaryText: {
    color: Colors.textPrimary,
    fontSize: 16,
    fontWeight: "600",
  },
  btnSkip: {
    alignItems: "center",
    paddingVertical: 8,
  },
  btnSkipText: {
    color: Colors.textSecondary,
    fontSize: 14,
  },
});
