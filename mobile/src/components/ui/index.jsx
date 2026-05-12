import { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  TextInput,
  Modal,
  FlatList,
} from "react-native";
import { theme } from "../../theme";

// ─── Toggle ───────────────────────────────────────────────────────────────────

export function Toggle({ checked, onChange }) {
  return (
    <TouchableOpacity
      onPress={() => onChange(!checked)}
      activeOpacity={0.8}
      style={{
        width: 40,
        height: 23,
        borderRadius: 999,
        backgroundColor: checked ? theme.blue : theme.border,
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      <View
        style={{
          position: "absolute",
          width: 17,
          height: 17,
          backgroundColor: "white",
          borderRadius: 999,
          top: 3,
          left: checked ? 20 : 3,
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 1 },
          shadowOpacity: 0.2,
          shadowRadius: 1,
          elevation: 2,
        }}
      />
    </TouchableOpacity>
  );
}

// ─── ToggleRow ────────────────────────────────────────────────────────────────

export function ToggleRow({ label, description, checked, onChange, badge, isLast }) {
  return (
    <View
      style={{
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        paddingVertical: 11,
        borderBottomWidth: isLast ? 0 : 1,
        borderBottomColor: theme.border,
        gap: 10,
      }}
    >
      <View style={{ flex: 1 }}>
        <Text style={{ fontSize: 13, fontWeight: "500", color: theme.ink, lineHeight: 18 }}>
          {label}
        </Text>
        {description ? (
          <Text style={{ fontSize: 11, color: theme.inkMuted, marginTop: 2 }}>
            {description}
          </Text>
        ) : null}
      </View>
      {badge ? (
        <Text
          style={{
            fontSize: 11,
            color: theme.blue,
            fontWeight: "500",
            flexShrink: 0,
            backgroundColor: theme.blueSoft,
            paddingHorizontal: 7,
            paddingVertical: 2,
            borderRadius: 4,
            fontFamily: "monospace",
          }}
        >
          {badge}
        </Text>
      ) : null}
      <Toggle checked={checked} onChange={onChange} />
    </View>
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────

export function Card({ icon, title, children, style }) {
  return (
    <View
      style={{
        backgroundColor: theme.white,
        borderRadius: theme.r,
        padding: 16,
        borderWidth: 1,
        borderColor: theme.border,
        shadowColor: "#0D1117",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.06,
        shadowRadius: 4,
        elevation: 2,
        ...style,
      }}
    >
      {(icon || title) ? (
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 14 }}>
          {icon ? (
            <View
              style={{
                width: 28,
                height: 28,
                borderRadius: 8,
                backgroundColor: theme.blueSoft,
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <Text style={{ fontSize: 13 }}>{icon}</Text>
            </View>
          ) : null}
          {title ? (
            <Text style={{ fontSize: 13, fontWeight: "600", color: theme.ink }}>{title}</Text>
          ) : null}
        </View>
      ) : null}
      {children}
    </View>
  );
}

// ─── Field ────────────────────────────────────────────────────────────────────

export function Field({ label, children, style }) {
  return (
    <View style={{ gap: 5, ...style }}>
      <Text
        style={{
          fontSize: 11,
          fontWeight: "500",
          color: theme.inkMuted,
          textTransform: "uppercase",
          letterSpacing: 0.6,
        }}
      >
        {label}
      </Text>
      {children}
    </View>
  );
}

// ─── Input ────────────────────────────────────────────────────────────────────

export function Input({ unit, style, onChange, value, ...props }) {
  return (
    <View style={{ position: "relative" }}>
      <TextInput
        style={{
          borderWidth: 1.5,
          borderColor: theme.border,
          borderRadius: theme.rSm,
          paddingVertical: 10,
          paddingLeft: 13,
          paddingRight: unit ? 52 : 13,
          fontSize: 14,
          color: theme.ink,
          backgroundColor: theme.white,
          ...style,
        }}
        value={value != null ? String(value) : ""}
        onChangeText={onChange}
        placeholderTextColor="#C8CBD4"
        {...props}
      />
      {unit ? (
        <Text
          style={{
            position: "absolute",
            right: 12,
            top: "50%",
            marginTop: -8,
            fontSize: 10,
            color: theme.inkMuted,
            fontWeight: "500",
            fontFamily: "monospace",
          }}
        >
          {unit}
        </Text>
      ) : null}
    </View>
  );
}

// ─── Select (modal-based grouped picker) ─────────────────────────────────────

export function Select({ value, onChange, options, placeholder }) {
  const [visible, setVisible] = useState(false);
  const selectedLabel =
    options?.find((o) => !o.isHeader && o.value === value)?.label ?? placeholder ?? "Selecionar...";

  return (
    <>
      <TouchableOpacity
        onPress={() => setVisible(true)}
        activeOpacity={0.7}
        style={{
          borderWidth: 1.5,
          borderColor: theme.border,
          borderRadius: theme.rSm,
          backgroundColor: theme.white,
          paddingHorizontal: 13,
          paddingVertical: 11,
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          minHeight: 44,
        }}
      >
        <Text
          style={{
            fontSize: 14,
            color: value ? theme.ink : "#C8CBD4",
            flex: 1,
          }}
          numberOfLines={1}
        >
          {selectedLabel}
        </Text>
        <Text style={{ color: theme.inkMuted, marginLeft: 8 }}>▾</Text>
      </TouchableOpacity>

      <Modal visible={visible} animationType="slide" transparent onRequestClose={() => setVisible(false)}>
        <View style={{ flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(0,0,0,0.4)" }}>
          <View
            style={{
              backgroundColor: theme.white,
              borderTopLeftRadius: 20,
              borderTopRightRadius: 20,
              maxHeight: "72%",
            }}
          >
            <View
              style={{
                flexDirection: "row",
                justifyContent: "space-between",
                alignItems: "center",
                padding: 16,
                borderBottomWidth: 1,
                borderBottomColor: theme.border,
              }}
            >
              <Text style={{ fontSize: 15, fontWeight: "600", color: theme.ink }}>
                Selecionar procedimento
              </Text>
              <TouchableOpacity onPress={() => setVisible(false)}>
                <Text style={{ color: theme.blue, fontSize: 15, fontWeight: "500" }}>Fechar</Text>
              </TouchableOpacity>
            </View>

            <FlatList
              data={options}
              keyExtractor={(item) => item.value}
              renderItem={({ item }) => {
                if (item.isHeader) {
                  return (
                    <View
                      style={{
                        paddingHorizontal: 16,
                        paddingVertical: 8,
                        backgroundColor: theme.bgSoft,
                      }}
                    >
                      <Text
                        style={{
                          fontSize: 11,
                          fontWeight: "600",
                          color: theme.inkMuted,
                          textTransform: "uppercase",
                          letterSpacing: 0.4,
                        }}
                      >
                        {item.label}
                      </Text>
                    </View>
                  );
                }
                return (
                  <TouchableOpacity
                    onPress={() => {
                      onChange(item.value);
                      setVisible(false);
                    }}
                    style={{
                      paddingHorizontal: 16,
                      paddingVertical: 13,
                      borderBottomWidth: 1,
                      borderBottomColor: theme.border,
                      backgroundColor: item.value === value ? theme.blueSoft : "transparent",
                    }}
                  >
                    <Text
                      style={{
                        fontSize: 13,
                        color: item.value === value ? theme.blue : theme.ink,
                        fontWeight: item.value === value ? "500" : "400",
                      }}
                    >
                      {item.label}
                    </Text>
                  </TouchableOpacity>
                );
              }}
            />
          </View>
        </View>
      </Modal>
    </>
  );
}

// ─── ChipGroup ────────────────────────────────────────────────────────────────

export function ChipGroup({ options, value, onChange }) {
  return (
    <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap" }}>
      {options.map((opt) => (
        <TouchableOpacity
          key={opt.value}
          onPress={() => onChange(opt.value)}
          activeOpacity={0.7}
          style={{
            paddingVertical: 7,
            paddingHorizontal: 14,
            borderRadius: 999,
            borderWidth: 1.5,
            borderColor: value === opt.value ? theme.blue : theme.border,
            backgroundColor: value === opt.value ? theme.blue : theme.white,
          }}
        >
          <Text
            style={{
              fontSize: 12,
              fontWeight: "500",
              color: value === opt.value ? "white" : theme.inkMuted,
            }}
          >
            {opt.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

// ─── InfoBox ──────────────────────────────────────────────────────────────────

export function InfoBox({ icon = "ℹ️", children }) {
  return (
    <View
      style={{
        borderRadius: theme.rSm,
        padding: 12,
        borderWidth: 1,
        borderColor: "#BDD3FB",
        backgroundColor: theme.blueSoft,
        flexDirection: "row",
        gap: 10,
        alignItems: "flex-start",
      }}
    >
      <Text style={{ fontSize: 16, flexShrink: 0 }}>{icon}</Text>
      <View style={{ flex: 1 }}>
        {typeof children === "string" ? (
          <Text style={{ fontSize: 12, color: "#1A3B7A", lineHeight: 18.6 }}>{children}</Text>
        ) : (
          children
        )}
      </View>
    </View>
  );
}
