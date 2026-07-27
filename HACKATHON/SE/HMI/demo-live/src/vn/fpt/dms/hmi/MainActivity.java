package vn.fpt.dms.hmi;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private TextView status;
    private TextView title;
    private TextView action;
    private TextView evidence;
    private TextView telemetry;
    private TextView ecuStatus;
    private Button voiceButton;
    private TextToSpeech tts;
    private boolean voiceEnabled = true;
    private int lastSeverity = -1;
    private int demoTick = 0;
    private long lastLiveAt = 0L;

    private static final Pattern RISK = Pattern.compile("\"Vehicle\\.ADAS\\.FinalRiskScore\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*([0-9.]+)");
    private static final Pattern SPEED = Pattern.compile("\"Vehicle\\.Speed\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*([0-9.]+)");
    private static final Pattern ALERTNESS = Pattern.compile("\"Vehicle\\.Driver\\.AlertnessScore\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*([0-9.]+)");
    private static final Pattern TTC = Pattern.compile("\"Vehicle\\.ADAS\\.MinTTC\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*([0-9.]+)");
    private static final Pattern SEVERITY = Pattern.compile("\"Vehicle\\.ADAS\\.DisplaySeverity\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*\"([A-Z]+)\"");
    private static final Pattern DRIVER = Pattern.compile("\"Vehicle\\.Driver\\.State\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*\"([a-zA-Z_]+)\"");
    private static final Pattern ACTION = Pattern.compile("\"Vehicle\\.ADAS\\.RecommendedActionCode\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*\"([A-Z_]+)\"");
    private static final Pattern AI = Pattern.compile("\"Vehicle\\.ADAS\\.AIStatus\"\\s*:\\s*\\{[^}]*\"value\"\\s*:\\s*\"([A-Z]+)\"");

    private final Runnable loop = new Runnable() {
        @Override public void run() {
            fetchLiveThenRender();
            handler.postDelayed(this, 1000L);
        }
    };

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUi();
        tts = new TextToSpeech(this, this);
        handler.post(loop);
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setPadding(60, 40, 60, 40);
        setContentView(root);

        status = text(18, Color.WHITE);
        title = text(50, Color.WHITE);
        action = text(30, Color.WHITE);
        evidence = text(22, Color.rgb(220, 225, 235));
        telemetry = text(20, Color.rgb(220, 225, 235));
        ecuStatus = text(22, Color.rgb(191, 219, 254));
        voiceButton = new Button(this);
        voiceButton.setText("VOICE ON");
        voiceButton.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) {
                voiceEnabled = !voiceEnabled;
                voiceButton.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED");
                if (!voiceEnabled && tts != null) tts.stop();
            }
        });

        root.addView(status);
        root.addView(title);
        root.addView(action);
        root.addView(evidence);
        root.addView(telemetry);
        root.addView(ecuStatus);
        root.addView(voiceButton, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 70));
        render(new State("OFFLINE", "SAFE", "alert", "NONE", 0f, 0f, 0f, 0f, false));
    }

    private TextView text(int sp, int color) {
        TextView tv = new TextView(this);
        tv.setTextSize(sp);
        tv.setTextColor(color);
        tv.setGravity(Gravity.CENTER);
        tv.setPadding(18, 8, 18, 8);
        return tv;
    }

    private void fetchLiveThenRender() {
        new Thread(new Runnable() {
            @Override public void run() {
                State state = null;
                try {
                    String body = httpGet(Config.CARSKY_VALUES_URL, Config.CARSKY_API_KEY);
                    state = parse(body);
                    lastLiveAt = System.currentTimeMillis();
                } catch (Throwable ignored) {
                    if (System.currentTimeMillis() - lastLiveAt > 2500L) state = demoState();
                }
                final State finalState = state;
                if (finalState != null) handler.post(new Runnable() {
                    @Override public void run() { render(finalState); }
                });
            }
        }).start();
    }

    private String httpGet(String url, String token) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(1500);
        conn.setReadTimeout(1500);
        if (token != null && token.length() > 0) conn.setRequestProperty("Authorization", "Bearer " + token);
        BufferedReader br = new BufferedReader(new InputStreamReader(conn.getInputStream()));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = br.readLine()) != null) sb.append(line);
        br.close();
        return sb.toString();
    }

    private State parse(String body) {
        String sev = str(body, SEVERITY, "SAFE");
        return new State(
            str(body, AI, "ONLINE"),
            sev,
            str(body, DRIVER, "alert"),
            str(body, ACTION, "NONE"),
            num(body, SPEED, 0f),
            num(body, RISK, 0f),
            num(body, ALERTNESS, 0f),
            num(body, TTC, 0f),
            "CRITICAL".equals(sev)
        );
    }

    private float num(String body, Pattern p, float fallback) {
        Matcher m = p.matcher(body);
        return m.find() ? Float.parseFloat(m.group(1)) : fallback;
    }

    private String str(String body, Pattern p, String fallback) {
        Matcher m = p.matcher(body);
        return m.find() ? m.group(1) : fallback;
    }

    private State demoState() {
        demoTick++;
        int phase = (demoTick / 5) % 3;
        if (phase == 1) return new State("DEGRADED", "WARNING", "distracted", "FOCUS_FORWARD", 75f, 55f, 0.45f, 3.0f, false);
        if (phase == 2) return new State("ONLINE", "CRITICAL", "microsleep", "BRAKE_SAFE", 80f, 88f, 0.15f, 1.2f, true);
        return new State("ONLINE", "SAFE", "alert", "NONE", 60f, 5f, 0.95f, 10f, false);
    }

    private void render(State s) {
        int severity = "CRITICAL".equals(s.severity) ? 2 : ("WARNING".equals(s.severity) ? 1 : 0);
        ((View) title.getParent()).setBackgroundColor(severity == 2 ? Color.rgb(109, 18, 31) : severity == 1 ? Color.rgb(117, 82, 15) : Color.rgb(11, 28, 45));
        status.setText("AI " + s.ai + "  •  " + (voiceEnabled ? "VOICE ON" : "VOICE MUTED"));
        title.setText(severity == 2 ? "NGUY HIỂM" : severity == 1 ? "CẢNH BÁO" : "LÁI XE AN TOÀN");
        String act = actionText(s.action);
        action.setText(act);
        evidence.setText("Tài xế: " + driverText(s.driver) + (s.ttc > 0 ? String.format(Locale.US, "  •  TTC %.1fs", s.ttc) : ""));
        telemetry.setText(String.format(Locale.US, "%.0f km/h     Risk %.0f     Alertness %.0f%%", s.speed, s.risk, s.alertness * 100f));
        ecuStatus.setText(ecuText(severity, s.action));
        maybeSpeak(severity, act, ecuVoice(severity, s.action));
    }

    private String actionText(String action) {
        if ("FOCUS_FORWARD".equals(action)) return "TẬP TRUNG PHÍA TRƯỚC";
        if ("TAKE_BREAK".equals(action)) return "HÃY NGHỈ NGƠI";
        if ("BRAKE_SAFE".equals(action)) return "PHANH AN TOÀN";
        if ("REDUCE_SPEED".equals(action)) return "GIẢM TỐC ĐỘ";
        return "TIẾP TỤC QUAN SÁT";
    }

    private String driverText(String driver) {
        if ("drowsy".equals(driver)) return "Buồn ngủ";
        if ("yawning".equals(driver)) return "Ngáp";
        if ("distracted".equals(driver)) return "Mất tập trung";
        if ("microsleep".equals(driver)) return "Vi ngủ";
        return "Tỉnh táo";
    }

    private String ecuText(int severity, String action) {
        if (severity == 2 || "BRAKE_SAFE".equals(action)) {
            return "ECU: BRAKE ASSIST REQUESTED  •  BUZZER ON  •  HAZARD ON";
        }
        if (severity == 1) {
            return "ECU: DRIVER WARNING BUZZER ON  •  HAPTIC ALERT ON";
        }
        return "ECU: STANDBY  •  ALL DRIVER ALERT ACTUATORS OFF";
    }

    private String ecuVoice(int severity, String action) {
        if (severity == 2 || "BRAKE_SAFE".equals(action)) {
            return "Kích hoạt ECU hỗ trợ phanh và cảnh báo khẩn cấp.";
        }
        if (severity == 1) {
            return "Kích hoạt cảnh báo tài xế.";
        }
        return "";
    }

    private void maybeSpeak(int severity, String act, String ecuVoice) {
        if (!voiceEnabled || tts == null || severity == lastSeverity) {
            lastSeverity = severity;
            return;
        }
        if (severity == 2) tts.speak("Nguy hiểm. " + act + ". " + ecuVoice, TextToSpeech.QUEUE_FLUSH, null, "critical");
        else if (severity == 1) tts.speak(act + ". " + ecuVoice, TextToSpeech.QUEUE_FLUSH, null, "warning");
        lastSeverity = severity;
    }

    @Override public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS && tts != null) tts.setLanguage(new Locale("vi", "VN"));
    }

    @Override protected void onDestroy() {
        handler.removeCallbacks(loop);
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }

    static final class State {
        final String ai, severity, driver, action;
        final float speed, risk, alertness, ttc;
        final boolean critical;
        State(String ai, String severity, String driver, String action, float speed, float risk, float alertness, float ttc, boolean critical) {
            this.ai = ai; this.severity = severity; this.driver = driver; this.action = action;
            this.speed = speed; this.risk = risk; this.alertness = alertness; this.ttc = ttc; this.critical = critical;
        }
    }
}
