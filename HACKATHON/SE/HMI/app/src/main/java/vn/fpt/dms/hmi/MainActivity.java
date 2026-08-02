package vn.fpt.dms.hmi;

import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.speech.tts.TextToSpeech;
import android.text.InputType;
import android.util.Base64;
import android.view.Gravity;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.time.Instant;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/** Realtime HMI using CarSky Signals REST; ADB and custom VHAL are not runtime dependencies. */
public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String VALUES_URL = "https://hackathon-1.carsky.io/api/v1/signals/wfhuue4wpc9jbvv4o7jbi/dms-signal-broker/values";
    private static final String KEY_ALIAS = "dms_carsky_test_token";
    private static final String PREFS = "dms_secure_config";
    private static final long POLL_MS = 500;
    private static final long OFFLINE_AFTER_MS = 3000;
    private static final String REQUEST_BODY = "{\"paths\":["
            + "\"Vehicle.Driver.State\",\"Vehicle.Driver.AlertnessScore\","
            + "\"Vehicle.Speed\",\"Vehicle.ADAS.MinTTC\","
            + "\"Vehicle.ADAS.FinalRiskScore\",\"Vehicle.ADAS.DisplaySeverity\","
            + "\"Vehicle.ADAS.CriticalAlert\",\"Vehicle.ADAS.AIStatus\","
            + "\"Vehicle.ADAS.RecommendedActionCode\",\"Vehicle.ADAS.DataAgeMs\"]}";

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private volatile boolean requestInFlight;
    private volatile String apiKey;
    private TextToSpeech tts;
    private boolean voiceEnabled = true;
    private int lastSeverity = -1;
    private long lastWarningVoiceAt;
    private LinearLayout root;
    private TextView status, title, action, evidence, telemetry;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        tts = new TextToSpeech(this, this);
        apiKey = loadApiKey();
        if (apiKey == null || apiKey.isEmpty()) showSetup(); else startRealtimeUi();
    }

    private TextView text(int sp, int color) {
        TextView view = new TextView(this);
        view.setTextSize(sp); view.setTextColor(color); view.setGravity(Gravity.CENTER);
        view.setPadding(18, 10, 18, 10); return view;
    }

    private LinearLayout baseLayout() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL); layout.setGravity(Gravity.CENTER);
        layout.setPadding(50, 35, 50, 35); layout.setBackgroundColor(0xff101826);
        return layout;
    }

    private void showSetup() {
        handler.removeCallbacks(poll);
        LinearLayout setup = baseLayout();
        TextView heading = text(34, Color.WHITE); heading.setText("CARSKY REALTIME SETUP");
        TextView help = text(18, 0xffd8dce8);
        help.setText("Paste the scoped API key for deployment test. It is encrypted with Android Keystore and is not stored in the APK.");
        EditText input = new EditText(this);
        input.setTextColor(Color.WHITE); input.setHintTextColor(0xff94a3b8); input.setHint("CarSky API key");
        input.setSingleLine(true); input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        Button save = new Button(this); save.setText("SAVE AND CONNECT");
        TextView error = text(15, 0xffff8a8a);
        save.setOnClickListener(v -> {
            String candidate = input.getText().toString().trim();
            if (candidate.isEmpty()) { error.setText("API key is required"); return; }
            try { saveApiKey(candidate); apiKey = candidate; startRealtimeUi(); }
            catch (Exception exc) { error.setText("Cannot secure API key on this device"); }
        });
        setup.addView(heading); setup.addView(help); setup.addView(input); setup.addView(save); setup.addView(error);
        setContentView(setup);
    }

    private void startRealtimeUi() {
        root = baseLayout();
        status = text(18, Color.WHITE); title = text(44, Color.WHITE);
        action = text(28, Color.WHITE); evidence = text(22, 0xffd8dce8); telemetry = text(20, 0xffd8dce8);
        Button voice = new Button(this); voice.setText("VOICE ON");
        voice.setOnClickListener(v -> { voiceEnabled = !voiceEnabled; voice.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED"); if (!voiceEnabled && tts != null) tts.stop(); });
        Button reset = new Button(this); reset.setText("CHANGE API KEY");
        reset.setOnClickListener(v -> { clearApiKey(); apiKey = null; showSetup(); });
        root.addView(status); root.addView(title); root.addView(action); root.addView(evidence); root.addView(telemetry); root.addView(voice); root.addView(reset);
        setContentView(root); renderOffline("WAITING FOR CARSKY SIGNALS");
        handler.removeCallbacks(poll); handler.post(poll);
    }

    private final Runnable poll = new Runnable() {
        @Override public void run() {
            if (apiKey != null && !requestInFlight) {
                requestInFlight = true;
                network.execute(() -> {
                    try { State state = fetchState(); handler.post(() -> render(state)); }
                    catch (Throwable error) { handler.post(() -> renderOffline("CARSKY CONNECTION ERROR")); }
                    finally { requestInFlight = false; }
                });
            }
            handler.postDelayed(this, POLL_MS);
        }
    };

    private State fetchState() throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(VALUES_URL).openConnection();
        connection.setRequestMethod("POST"); connection.setConnectTimeout(3000); connection.setReadTimeout(3000); connection.setDoOutput(true);
        connection.setRequestProperty("Authorization", "Bearer " + apiKey);
        connection.setRequestProperty("Content-Type", "application/json"); connection.setRequestProperty("Accept", "application/json");
        byte[] body = REQUEST_BODY.getBytes(StandardCharsets.UTF_8); connection.setFixedLengthStreamingMode(body.length);
        try (OutputStream output = connection.getOutputStream()) { output.write(body); }
        int code = connection.getResponseCode();
        InputStream stream = code >= 200 && code < 300 ? connection.getInputStream() : connection.getErrorStream();
        String response = readAll(stream); connection.disconnect();
        if (code < 200 || code >= 300) throw new IllegalStateException("CarSky HTTP " + code);
        JSONArray values = new JSONObject(response).getJSONArray("values");
        Map<String, Object> signal = new HashMap<>(); long newest = 0;
        for (int i = 0; i < values.length(); i++) {
            JSONObject item = values.getJSONObject(i); signal.put(item.getString("path"), item.opt("value"));
            String timestamp = item.optString("timestamp", ""); if (!timestamp.isEmpty()) newest = Math.max(newest, Instant.parse(timestamp).toEpochMilli());
        }
        long age = newest == 0 ? Long.MAX_VALUE : Math.max(0, System.currentTimeMillis() - newest);
        if (age > OFFLINE_AFTER_MS) throw new IllegalStateException("Stale CarSky data");
        return State.from(signal, age);
    }

    private static String readAll(InputStream stream) throws Exception {
        if (stream == null) return ""; StringBuilder result = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) { String line; while ((line = reader.readLine()) != null) result.append(line); }
        return result.toString();
    }

    private void render(State state) {
        int severity = severityCode(state.severity);
        root.setBackgroundColor(severity == 2 ? 0xff6d1018 : severity == 1 ? 0xff664500 : severity == 3 ? 0xff123d58 : 0xff101826);
        status.setText("AI " + state.aiStatus + (voiceEnabled ? "  •  VOICE ON" : "  •  VOICE MUTED") + "  •  " + state.ageMs + "ms");
        title.setText(severity == 2 ? "NGUY HIEM" : severity == 1 ? "CANH BAO" : severity == 3 ? "DA AN TOAN TRO LAI" : "LAI XE AN TOAN");
        String actionText = actionText(state.action); action.setText(actionText);
        evidence.setText("Tai xe: " + state.driverState + (state.ttc > 0 ? String.format(Locale.US, "  •  TTC %.1fs", state.ttc) : ""));
        telemetry.setText(String.format(Locale.US, "%.0f km/h     Risk %.0f     Alertness %.0f%%", state.speed, state.risk, state.alertness * 100));
        maybeSpeak(severity, actionText);
    }

    private void renderOffline(String reason) {
        if (root == null) return; root.setBackgroundColor(0xff1f2937); status.setText("AI OFFLINE" + (voiceEnabled ? "  •  VOICE ON" : "  •  VOICE MUTED"));
        title.setText("KHONG CO DU LIEU"); action.setText(reason); evidence.setText("Dang cho du lieu realtime tu CarSky Signals"); telemetry.setText("-- km/h     Risk --     Alertness --"); lastSeverity = -1;
    }

    private static int severityCode(String v) { return "WARNING".equals(v) ? 1 : "CRITICAL".equals(v) ? 2 : "RECOVERY".equals(v) ? 3 : 0; }
    private static String actionText(String v) { return "FOCUS_FORWARD".equals(v) ? "TAP TRUNG PHIA TRUOC" : "TAKE_BREAK".equals(v) ? "HAY NGHI NGOI" : "BRAKE_SAFE".equals(v) ? "PHANH AN TOAN" : "REDUCE_SPEED".equals(v) ? "GIAM TOC DO" : "TIEP TUC QUAN SAT"; }
    private void maybeSpeak(int severity, String text) {
        if (!voiceEnabled || tts == null || severity == lastSeverity) { lastSeverity = severity; return; }
        long now = System.currentTimeMillis();
        if (severity == 1 && now - lastWarningVoiceAt >= 15000) { tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "warning"); lastWarningVoiceAt = now; }
        if (severity == 2) tts.speak("Nguy hiem. " + text, TextToSpeech.QUEUE_FLUSH, null, "critical"); lastSeverity = severity;
    }

    private SecretKey secureKey() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore"); store.load(null);
        if (store.containsAlias(KEY_ALIAS)) return ((KeyStore.SecretKeyEntry) store.getEntry(KEY_ALIAS, null)).getSecretKey();
        KeyGenerator generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
        generator.init(new KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build());
        return generator.generateKey();
    }

    private void saveApiKey(String value) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.ENCRYPT_MODE, secureKey());
        byte[] encrypted = cipher.doFinal(value.getBytes(StandardCharsets.UTF_8));
        getSharedPreferences(PREFS, MODE_PRIVATE).edit().putString("token", Base64.encodeToString(encrypted, Base64.NO_WRAP)).putString("iv", Base64.encodeToString(cipher.getIV(), Base64.NO_WRAP)).apply();
    }

    private String loadApiKey() {
        try {
            SharedPreferences prefs = getSharedPreferences(PREFS, MODE_PRIVATE); String token = prefs.getString("token", null), iv = prefs.getString("iv", null); if (token == null || iv == null) return null;
            Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding"); cipher.init(Cipher.DECRYPT_MODE, secureKey(), new GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)));
            return new String(cipher.doFinal(Base64.decode(token, Base64.NO_WRAP)), StandardCharsets.UTF_8);
        } catch (Exception error) { return null; }
    }

    private void clearApiKey() { getSharedPreferences(PREFS, MODE_PRIVATE).edit().clear().apply(); }
    @Override public void onInit(int result) { if (result == TextToSpeech.SUCCESS) tts.setLanguage(new Locale("vi", "VN")); }
    @Override protected void onDestroy() { handler.removeCallbacks(poll); network.shutdownNow(); if (tts != null) { tts.stop(); tts.shutdown(); } super.onDestroy(); }

    private static final class State {
        final String driverState, severity, aiStatus, action; final float speed, risk, alertness, ttc; final long ageMs;
        State(String d, String s, String ai, String a, float sp, float r, float al, float t, long age) { driverState=d; severity=s; aiStatus=ai; action=a; speed=sp; risk=r; alertness=al; ttc=t; ageMs=age; }
        static State from(Map<String,Object> v,long age) { return new State(string(v,"Vehicle.Driver.State","unknown"),string(v,"Vehicle.ADAS.DisplaySeverity","SAFE"),string(v,"Vehicle.ADAS.AIStatus","OFFLINE"),string(v,"Vehicle.ADAS.RecommendedActionCode","NONE"),number(v,"Vehicle.Speed"),number(v,"Vehicle.ADAS.FinalRiskScore"),number(v,"Vehicle.Driver.AlertnessScore"),number(v,"Vehicle.ADAS.MinTTC"),age); }
        static String string(Map<String,Object> v,String k,String f) { Object x=v.get(k); return x instanceof String ? (String)x : f; }
        static float number(Map<String,Object> v,String k) { Object x=v.get(k); return x instanceof Number ? ((Number)x).floatValue() : 0f; }
    }
}
