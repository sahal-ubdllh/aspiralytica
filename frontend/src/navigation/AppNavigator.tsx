import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { Ionicons } from "@expo/vector-icons";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Colors } from "../theme/colors";

import SplashScreen   from "../screens/SplashScreen";
import LoginScreen    from "../screens/LoginScreen";
import RegisterScreen from "../screens/RegisterScreen";
import HomeScreen     from "../screens/HomeScreen";
import InputScreen    from "../screens/InputScreen";
import ResultScreen   from "../screens/ResultScreen";
import HistoryScreen  from "../screens/HistoryScreen";
import ProfileScreen  from "../screens/ProfileScreen";
import InsightScreen  from "../screens/InsightScreen";

const Tab   = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

function MainTabs() {
  const insets = useSafeAreaInsets();

  // Selalu tambah minimal 8px di bawah icon,
  // plus insets.bottom untuk gesture bar Android/iPhone
  const tabBarPaddingBottom = insets.bottom + 8;
  const tabBarHeight = 48 + tabBarPaddingBottom;

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: Colors.white,
          borderTopColor: Colors.border,
          borderTopWidth: 1,
          height: tabBarHeight,
          paddingBottom: tabBarPaddingBottom,
          paddingTop: 8,
        },
        tabBarActiveTintColor: Colors.primary,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarLabelStyle: { fontSize: 11, fontWeight: "600" },
        tabBarIcon: ({ focused, color }) => {
          const icons: Record<string, [string, string]> = {
            Beranda: ["home",      "home-outline"],
            Riwayat: ["time",      "time-outline"],
            Insight: ["bar-chart", "bar-chart-outline"],
            Akun:    ["person",    "person-outline"],
          };
          const [active, inactive] = icons[route.name] ?? ["ellipse", "ellipse-outline"];
          const name = (focused ? active : inactive) as keyof typeof Ionicons.glyphMap;
          return <Ionicons name={name} size={22} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Beranda" component={HomeScreen}    />
      <Tab.Screen name="Riwayat" component={HistoryScreen} />
      <Tab.Screen name="Insight" component={InsightScreen} />
      <Tab.Screen name="Akun"    component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{ headerShown: false }}
        initialRouteName="Splash"
      >
        <Stack.Screen name="Splash"   component={SplashScreen}   />
        <Stack.Screen name="Login"    component={LoginScreen}    />
        <Stack.Screen name="Register" component={RegisterScreen} />
        <Stack.Screen name="Main"     component={MainTabs}       />
        <Stack.Screen name="Input"    component={InputScreen}    />
        <Stack.Screen name="Result"   component={ResultScreen}   />
      </Stack.Navigator>
    </NavigationContainer>
  );
}