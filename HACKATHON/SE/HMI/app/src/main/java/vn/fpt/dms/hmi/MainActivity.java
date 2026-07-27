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

import java.lang.reflect.Method;
import java.util.Locale;

public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final int PROP_SPEED = 291504647;
    private static final int PROP_RISK = 557843456;
    private static final int PROP_SEVERITY = 559940617;
    private static final int PROP_DRIVER = 559940618;
    private static final int PROP_ALERTNESS = 555746306;
    private static final int PROP_TTC = 555746307;
    private static final int PROP_CRITICAL = 555746305;
    private static final int PROP_AI_STATUS = 555746308;
    private static final int PROP_ACTION = 555746309;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private Object car;
    private Object propertyManager;
    private Method getProperty;
    private TextToSpeech tts;
    private boolean voiceEnabled = true;
    private int lastSeverity = -1;
    private long lastWarningVoiceAt = 0;

    private LinearLayout root;
    private TextView status;
    private TextView title;
    private TextView action;
    private TextView evidence;
    private TextView telemetry;
    private Button voice;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        buildUi();
        tts = new TextToSpeech(this, this);
        connectCarApi();
        handler.post(poll);
    }

    private TextView text(int sp, int color) {
        TextView view = new TextView(this);
        view.setTextSize(sp); view.setTextColor(color); view.setGravity(Gravity.CENTER);
        view.setPadding(18, 10, 18, 10); return view;
    }

    private void buildUi() {
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER); root.setPadding(50, 35, 50, 35);
        status = text(18, Color.WHITE); title = text(44, Color.WHITE);
        action = text(28, Color.WHITE); evidence = text(22, 0xffd8dce8);
        telemetry = text(20, 0xffd8dce8);
        voice = new Button(this); voice.setText("VOICE ON");
        voice.setOnClickListener(v -> { voiceEnabled = !voiceEnabled; voice.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED"); if (!voiceEnabled && tts != null) tts.stop(); });
        root.addView(status); root.addView(title); root.addView(action); root.addView(evidence); root.addView(telemetry); root.addView(voice);
        setContentView(root); render(0,0,0,0,0,2,0,0);
    }

    private void connectCarApi() {
        try {
            Class<?> carClass = Class.forName("android.car.Car");
            car = carClass.getMethod("createCar", android.content.Context.class).invoke(null, this);
            carClass.getMethod("connect").invoke(car);
            propertyManager = carClass.getMethod("getCarManager", String.class).invoke(car, "property");
            getProperty = propertyManager.getClass().getMethod("getProperty", int.class, int.class);
        } catch (Throwable error) {
            propertyManager = null;
            status.setText("AI OFFLINE • waiting for CarSky VHAL");
        }
    }

    private Number value(int property, Number fallback) {
        if (propertyManager == null) return fallback;
        try {
            Object carValue = getProperty.invoke(propertyManager, property, 0);
            Object raw = carValue.getClass().getMethod("getValue").invoke(carValue);
            return raw instanceof Number ? (Number) raw : fallback;
        } catch (Throwable ignored) { return fallback; }
    }

    private final Runnable poll = new Runnable() {
        @Override public void run() {
            render(value(PROP_SEVERITY,0).intValue(), value(PROP_DRIVER,0).intValue(),
                    value(PROP_SPEED,0).floatValue(), value(PROP_RISK,0).floatValue(),
                    value(PROP_ALERTNESS,0).floatValue(), value(PROP_AI_STATUS,2).intValue(),
                    value(PROP_TTC,0).floatValue(), value(PROP_ACTION,0).intValue());
            handler.postDelayed(this, 500);
        }
    };

    private void render(int severity, int driver, float speed, float risk, float alertness, int ai, float ttcValue, int actionCode) {
        int background = severity == 2 ? 0xff6d1018 : severity == 1 ? 0xff664500 : severity == 3 ? 0xff123d58 : 0xff101826;
        root.setBackgroundColor(background);
        String aiText = ai == 0 ? "AI ONLINE" : ai == 1 ? "AI DEGRADED" : "AI OFFLINE";
        status.setText(aiText + (voiceEnabled ? "  •  VOICE ON" : "  •  VOICE MUTED"));
        String driverText = new String[]{"Tỉnh táo","Buồn ngủ","Ngáp","Mất tập trung","Vi ngủ"}[Math.max(0, Math.min(4,driver))];
        if (severity == 2) title.setText("NGUY HIỂM");
        else if (severity == 1) title.setText("CẢNH BÁO");
        else if (severity == 3) title.setText("ĐÃ AN TOÀN TRỞ LẠI");
        else title.setText("LÁI XE AN TOÀN");
        String actionText = actionCode == 1 ? "TẬP TRUNG PHÍA TRƯỚC" : actionCode == 2 ? "HÃY NGHỈ NGƠI" : actionCode == 3 ? "PHANH AN TOÀN" : actionCode == 4 ? "GIẢM TỐC ĐỘ" : "TIẾP TỤC QUAN SÁT";
        action.setText(actionText);
        evidence.setText("Tài xế: " + driverText + (ttcValue > 0 ? String.format(Locale.US,"  •  TTC %.1fs",ttcValue) : ""));
        telemetry.setText(String.format(Locale.US,"%.0f km/h     Risk %.0f     Alertness %.0f%%",speed,risk,alertness*100));
        maybeSpeak(severity, actionText);
    }

    private void maybeSpeak(int severity, String actionText) {
        if (!voiceEnabled || tts == null || severity == lastSeverity) { lastSeverity = severity; return; }
        long now = System.currentTimeMillis();
        if (severity == 1 && now - lastWarningVoiceAt >= 15000) { tts.speak(actionText,TextToSpeech.QUEUE_FLUSH,null,"warning"); lastWarningVoiceAt=now; }
        if (severity == 2) tts.speak("Nguy hiểm. " + actionText,TextToSpeech.QUEUE_FLUSH,null,"critical");
        lastSeverity = severity;
    }

    @Override public void onInit(int result) { if (result == TextToSpeech.SUCCESS) tts.setLanguage(new Locale("vi","VN")); }
    @Override protected void onDestroy() { handler.removeCallbacks(poll); if (tts != null) {tts.stop();tts.shutdown();} super.onDestroy(); }
}
