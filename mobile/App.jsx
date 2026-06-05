import { View, Text, ActivityIndicator } from "react-native";
import { registerRootComponent } from "expo";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";
import Constants from "expo-constants";
import { theme } from "./src/theme";

const WEB_APP_URL =
  process.env.EXPO_PUBLIC_WEB_APP_URL ||
  Constants.expoConfig?.extra?.webAppUrl ||
  "https://cardio-risk-calc.vercel.app";

export default function App() {
  return (
    <SafeAreaProvider>
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
        <StatusBar style="dark" />

        <WebView
          source={{ uri: WEB_APP_URL }}
          startInLoadingState
          javaScriptEnabled
          domStorageEnabled
          renderLoading={() => (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center", gap: 10 }}>
              <ActivityIndicator size="large" color={theme.blue} />
              <Text style={{ color: theme.inkMid, fontSize: 14 }}>Carregando CardioRisk...</Text>
            </View>
          )}
          onError={() => {
            // Intentionally handled by the WebView built-in error screen.
          }}
        />
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

registerRootComponent(App);
