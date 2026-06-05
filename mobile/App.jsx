import { View, Text, ActivityIndicator, Alert } from "react-native";
import { registerRootComponent } from "expo";
import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";
import Constants from "expo-constants";
import * as FileSystem from "expo-file-system";
import * as Sharing from "expo-sharing";
import { theme } from "./src/theme";

const WEB_APP_URL =
  process.env.EXPO_PUBLIC_WEB_APP_URL ||
  Constants.expoConfig?.extra?.webAppUrl ||
  "https://cardio-risk-calc.vercel.app";

async function handlePdfMessage(payload) {
  const filename = payload?.filename || `CardioRisk-${Date.now()}.pdf`;
  const base64 = payload?.base64 || "";

  if (!base64) {
    Alert.alert("Falha ao gerar PDF", "O app não recebeu os dados do relatório.");
    return;
  }

  const fileUri = `${FileSystem.cacheDirectory}${filename.replace(/[\\/:*?"<>|]/g, "_")}`;
  await FileSystem.writeAsStringAsync(fileUri, base64, {
    encoding: FileSystem.EncodingType.Base64,
  });

  if (await Sharing.isAvailableAsync()) {
    await Sharing.shareAsync(fileUri, {
      mimeType: "application/pdf",
      dialogTitle: "CardioRisk - Relatório",
      UTI: "com.adobe.pdf",
    });
    return;
  }

  Alert.alert("PDF gerado", `Arquivo salvo em cache: ${filename}`);
}

async function onWebViewMessage(event) {
  try {
    const payload = JSON.parse(event.nativeEvent.data || "{}");
    if (payload?.type === "pdf-base64") {
      await handlePdfMessage(payload);
    }
  } catch {
    // Ignore non-JSON or unrelated messages from the page.
  }
}

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
          onMessage={onWebViewMessage}
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
