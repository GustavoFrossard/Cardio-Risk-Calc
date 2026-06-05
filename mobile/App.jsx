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

const PDF_BRIDGE_INJECTION = `
(function () {
  const originalOpen = window.open;
  const originalClick = HTMLAnchorElement.prototype.click;

  function sendPdfPayload(url, fallbackName) {
    if (typeof window.ReactNativeWebView?.postMessage !== "function") return;

    const baseName = (fallbackName || "CardioRisk-Relatorio.pdf").replace(/\\s+/g, "_");

    if (/^data:/i.test(url)) {
      const base64 = url.split(",")[1] || "";
      window.ReactNativeWebView.postMessage(JSON.stringify({ type: "pdf-base64", filename: baseName, base64 }));
      return;
    }

    if (/^blob:/i.test(url)) {
      fetch(url)
        .then((response) => response.blob())
        .then((blob) => new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result);
          reader.onerror = () => reject(new Error("Falha ao ler o PDF do blob."));
          reader.readAsDataURL(blob);
        }))
        .then((dataUri) => {
          const base64 = (dataUri || "").split(",")[1] || "";
          if (!base64) return;
          window.ReactNativeWebView.postMessage(JSON.stringify({ type: "pdf-base64", filename: baseName, base64 }));
        })
        .catch(() => {});
    }
  }

  HTMLAnchorElement.prototype.click = function () {
    try {
      const href = this.getAttribute("href") || "";
      const download = this.getAttribute("download") || "";
      if (/^(data:|blob:)/i.test(href) || /pdf/i.test(download)) {
        sendPdfPayload(href, download || "CardioRisk-Relatorio.pdf");
        return;
      }
    } catch (error) {
      // Ignore interception errors; fall back to the native click behavior.
    }

    return originalClick.apply(this, arguments);
  };

  window.open = function (url, name, specs) {
    if (typeof url === "string" && /^(data:|blob:)/i.test(url)) {
      sendPdfPayload(url, name || "CardioRisk-Relatorio.pdf");
      return null;
    }
    return originalOpen.apply(this, arguments);
  };
})();
true;
`;

async function handlePdfMessage(payload) {
  const filename = (payload?.filename || `CardioRisk-${Date.now()}.pdf`).replace(/\s+/g, "_");
  const safeFilename = filename.toLowerCase().endsWith(".pdf") ? filename : `${filename}.pdf`;
  const base64 = payload?.base64 || "";

  if (!base64) {
    Alert.alert("Falha ao gerar PDF", "O app não recebeu os dados do relatório.");
    return;
  }

  const fileUri = `${FileSystem.documentDirectory}${safeFilename}`;

  try {
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

    Alert.alert("PDF gerado", `Arquivo salvo em: ${fileUri}`);
  } catch (error) {
    console.error("Erro ao salvar PDF no app:", error);
    Alert.alert("Falha ao salvar PDF", "Não foi possível gravar ou compartilhar o relatório no dispositivo.");
  }
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
          injectedJavaScript={PDF_BRIDGE_INJECTION}
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
