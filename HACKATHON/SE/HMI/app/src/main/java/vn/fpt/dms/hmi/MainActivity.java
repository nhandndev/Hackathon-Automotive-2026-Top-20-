package vn.fpt.dms.hmi;

import android.app.Activity;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.Locale;

/**
 * Realtime HMI through CarSky Vehicle/HPC runtime.
 *
 * Data path:
 * Backend/AI -> CarSky KUKSA -> dms_hmi_bridge.lua -> VHAL PERF_VEHICLE_SPEED
 * -> Android CarProperty -> this APK.
 *
 * Why multiplex?
 * The CarSky AAOS image currently exposes PERF_VEHICLE_SPEED reliably, while
 * custom DMS VHAL properties were not visible in Android CarService during
 * runtime checks. The bridge therefore encodes DMS state into the standard
 * speed property and this APK decodes it back into HMI state.
 */
public final class MainActivity extends Activity implements TextToSpeech.OnInitListener {
    private static final String TAG = "DMS_HMI";
    private static final String BUILD_TAG = "V2.2 SPEED MUX";
    private static final int PERF_VEHICLE_SPEED = 291504647; // 0x11600207
    private static final int PROP_FINAL_RISK = 557843456; // 0x21400400
    private static final int PROP_CRITICAL_ALERT = 555746305; // 0x21200401
    private static final int PROP_ALERTNESS = 559940610; // 0x21600402
    private static final int PROP_MIN_TTC = 559940611; // 0x21600403
    private static final int PROP_AI_STATUS = 557843460; // 0x21400404
    private static final int PROP_ACTION = 557843461; // 0x21400405
    private static final int PROP_SEVERITY = 557843465; // 0x21400409
    private static final int PROP_DRIVER_STATE = 557843466; // 0x2140040A
    private static final int[] DMS_PROPS = new int[]{
            PERF_VEHICLE_SPEED
    };
    private static final int AREA_GLOBAL = 0;
    private static final float SENSOR_RATE_HZ = 10.0f;
    private static final long WATCHDOG_MS = 500;
    private static final long VHAL_POLL_MS = 250;
    private static final long OFFLINE_AFTER_MS = 4000;

    private final Handler handler = new Handler(Looper.getMainLooper());
    private final State state = new State();

    private TextToSpeech tts;
    private boolean voiceEnabled = true;
    private int lastSeverity = -1;
    private long lastWarningVoiceAt;

    private Object car;
    private Object propertyManager;
    private Object propertyCallback;
    private float lastPolledRaw = Float.NaN;

    private LinearLayout root;
    private TextView status;
    private TextView title;
    private TextView action;
    private TextView evidence;
    private TextView telemetry;
    private TextView aiPill;
    private TextView driverValue;
    private TextView alertnessValue;
    private TextView ttcValue;
    private TextView riskValue;
    private TextView safeScoreValue;
    private TextView ecuValue;
    private TextView speedValue;
    private TextView limitValue;
    private TextView reasonValue;
    private TextView ageValue;
    private Button voiceButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        tts = new TextToSpeech(this, this);
        buildUi();
        connectVehicleRuntime();
        handler.post(watchdog);
    }

    private void buildUi() {
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(44, 24, 44, 24);
        root.setBackground(makeBackground(0xff081827));

        LinearLayout topbar = new LinearLayout(this);
        topbar.setOrientation(LinearLayout.HORIZONTAL);
        topbar.setGravity(Gravity.CENTER_VERTICAL);
        topbar.setPadding(0, 0, 0, 18);
        root.addView(topbar, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 78));

        aiPill = pill("AI OFFLINE", 0xff64748b);
        topbar.addView(aiPill, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        status = pill(BUILD_TAG, 0xff38bdf8);
        topbar.addView(status, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1.3f));

        voiceButton = new Button(this);
        voiceButton.setText("VOICE ON");
        voiceButton.setTextColor(Color.WHITE);
        voiceButton.setTextSize(15);
        voiceButton.setTypeface(Typeface.DEFAULT_BOLD);
        voiceButton.setBackground(cardBackground(0x66111827, 0x33ffffff, 999));
        voiceButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                voiceEnabled = !voiceEnabled;
                voiceButton.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED");
                if (!voiceEnabled && tts != null) tts.stop();
                render();
            }
        });
        topbar.addView(voiceButton, new LinearLayout.LayoutParams(0, 54, 0.8f));

        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.HORIZONTAL);
        main.setGravity(Gravity.CENTER);
        root.addView(main, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f));

        LinearLayout leftCard = card();
        driverValue = addMetric(leftCard, "DRIVER", "Alert", 31);
        alertnessValue = addMetric(leftCard, "ALERTNESS", "--", 31);
        ttcValue = addMetric(leftCard, "TTC", "--", 31);
        main.addView(leftCard, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f));

        LinearLayout hero = new LinearLayout(this);
        hero.setOrientation(LinearLayout.VERTICAL);
        hero.setGravity(Gravity.CENTER);
        hero.setPadding(28, 18, 28, 18);
        title = text(58, Color.WHITE);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        action = text(34, Color.WHITE);
        action.setTypeface(Typeface.DEFAULT_BOLD);
        evidence = text(21, 0xdde5e7eb);
        telemetry = text(19, 0xffcbd5e1);
        hero.addView(title);
        hero.addView(action);
        hero.addView(evidence);
        hero.addView(telemetry);
        main.addView(hero, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1.55f));

        LinearLayout rightCard = card();
        TextView riskLabel = label("RISK SCORE");
        rightCard.addView(riskLabel);
        riskValue = text(46, Color.WHITE);
        riskValue.setTypeface(Typeface.DEFAULT_BOLD);
        riskValue.setSingleLine(true);
        riskValue.setBackground(cardBackground(0x44111827, 0x26ffffff, 999));
        rightCard.addView(riskValue, new LinearLayout.LayoutParams(210, 128));
        safeScoreValue = addMetric(rightCard, "SAFE SCORE", "--", 24);
        ecuValue = addMetric(rightCard, "ECU REACTION", "STANDBY", 20);
        main.addView(rightCard, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f));

        LinearLayout footer = new LinearLayout(this);
        footer.setOrientation(LinearLayout.HORIZONTAL);
        footer.setGravity(Gravity.CENTER);
        footer.setPadding(0, 18, 0, 0);
        root.addView(footer, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 86));
        speedValue = footerCell(footer);
        limitValue = footerCell(footer);
        reasonValue = footerCell(footer);
        ageValue = footerCell(footer);

        setContentView(root);
        renderOffline("WAITING FOR DATA FROM HMI BRIDGE");
    }

    private TextView text(int sp, int color) {
        TextView view = new TextView(this);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER);
        view.setPadding(18, 10, 18, 10);
        return view;
    }

    private TextView label(String value) {
        TextView view = text(14, 0xa6ffffff);
        view.setGravity(Gravity.LEFT);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setAllCaps(false);
        return viewWithText(view, value);
    }

    private TextView viewWithText(TextView view, String value) {
        view.setText(value);
        return view;
    }

    private TextView pill(String value, int accent) {
        TextView view = text(16, Color.WHITE);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setText(value);
        view.setBackground(cardBackground(0x66111827, accent, 999));
        return view;
    }

    private LinearLayout card() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setPadding(24, 20, 24, 20);
        layout.setBackground(cardBackground(0x66111827, 0x26ffffff, 24));
        return layout;
    }

    private TextView addMetric(LinearLayout parent, String label, String value, int sp) {
        parent.addView(label(label));
        TextView metric = text(sp, Color.WHITE);
        metric.setTypeface(Typeface.DEFAULT_BOLD);
        metric.setText(value);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, 2, 0, 14);
        parent.addView(metric, lp);
        return metric;
    }

    private TextView footerCell(LinearLayout parent) {
        TextView view = text(20, Color.WHITE);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setBackground(cardBackground(0x99000000, 0x1affffff, 10));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f);
        lp.setMargins(0, 0, 10, 0);
        parent.addView(view, lp);
        return view;
    }

    private GradientDrawable cardBackground(int color, int strokeColor, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        drawable.setStroke(1, strokeColor);
        return drawable;
    }

    private GradientDrawable makeBackground(int color) {
        GradientDrawable drawable = new GradientDrawable(
                GradientDrawable.Orientation.TL_BR,
                new int[]{adjustColor(color, 1.35f), color});
        return drawable;
    }

    private int adjustColor(int color, float factor) {
        int a = Color.alpha(color);
        int r = Math.min(255, Math.round(Color.red(color) * factor));
        int g = Math.min(255, Math.round(Color.green(color) * factor));
        int b = Math.min(255, Math.round(Color.blue(color) * factor));
        return Color.argb(a, r, g, b);
    }

    private void connectVehicleRuntime() {
        try {
            Class<?> carClass = Class.forName("android.car.Car");
            car = carClass.getMethod("createCar", android.content.Context.class).invoke(null, this);
            String propertyService = "property";
            try {
                Object fieldValue = carClass.getField("PROPERTY_SERVICE").get(null);
                if (fieldValue instanceof String) propertyService = (String) fieldValue;
            } catch (Throwable ignored) {
                // Some platform jars do not expose the constant to reflection.
            }
            propertyManager = carClass.getMethod("getCarManager", String.class).invoke(car, propertyService);
            registerVehicleCallback();
            handler.post(vehiclePoller);
            Log.i(TAG, "Registered DMS VHAL transport with speed-mux");
        } catch (Throwable error) {
            Log.e(TAG, "Cannot connect Android Car/VHAL runtime", error);
            renderOffline("CAR SERVICE / VHAL NOT READY");
        }
    }

    private final Runnable vehiclePoller = new Runnable() {
        @Override
        public void run() {
            pollVehicleValueOnce();
            handler.postDelayed(this, VHAL_POLL_MS);
        }
    };

    private void pollVehicleValueOnce() {
        if (propertyManager == null) return;
        try {
            Method getProperty = propertyManager.getClass().getMethod("getProperty", int.class, int.class);
            boolean changed = false;
            for (int propId : DMS_PROPS) {
                try {
                    Object propertyValue = getProperty.invoke(propertyManager, propId, AREA_GLOBAL);
                    if (propertyValue == null) continue;
                    Object raw = propertyValue.getClass().getMethod("getValue").invoke(propertyValue);
                    if (raw != null) {
                        decodeProperty(propId, raw);
                        changed = true;
                    }
                } catch (Throwable propError) {
                    Log.w(TAG, "VHAL property unavailable 0x" + Integer.toHexString(propId), propError);
                }
            }
            if (changed) render();
        } catch (Throwable error) {
            Log.w(TAG, "VHAL polling fallback could not read DMS properties", error);
        }
    }

    private void registerVehicleCallback() throws Exception {
        Class<?> callbackClass = Class.forName("android.car.hardware.property.CarPropertyManager$CarPropertyEventCallback");
        propertyCallback = Proxy.newProxyInstance(
                callbackClass.getClassLoader(),
                new Class<?>[]{callbackClass},
                new VehicleCallbackHandler());
        Method register = propertyManager.getClass().getMethod("registerCallback", callbackClass, int.class, float.class);
        for (int propId : DMS_PROPS) {
            try {
                Object ok = register.invoke(propertyManager, propertyCallback, propId, SENSOR_RATE_HZ);
                Log.i(TAG, "register 0x" + Integer.toHexString(propId) + "=" + ok);
            } catch (Throwable propError) {
                Log.w(TAG, "register failed 0x" + Integer.toHexString(propId), propError);
            }
        }
    }

    private final class VehicleCallbackHandler implements InvocationHandler {
        @Override
        public Object invoke(Object proxy, Method method, Object[] args) {
            String name = method.getName();
            if ("hashCode".equals(name)) {
                return System.identityHashCode(proxy);
            } else if ("equals".equals(name)) {
                return args != null && args.length > 0 && proxy == args[0];
            } else if ("toString".equals(name)) {
                return "DMS CarPropertyEventCallback";
            } else if ("onChangeEvent".equals(name) && args != null && args.length > 0) {
                handleCarPropertyEvent(args[0]);
            } else if ("onErrorEvent".equals(name)) {
                Log.e(TAG, "CarProperty callback error");
            }
            return null;
        }
    }

    private void handleCarPropertyEvent(Object event) {
        try {
            Object propertyValue = event;
            try {
                propertyValue = event.getClass().getMethod("getCarPropertyValue").invoke(event);
            } catch (NoSuchMethodException ignored) {
                // Android AAOS CarPropertyManager callback already passes CarPropertyValue.
            }
            Object raw = propertyValue.getClass().getMethod("getValue").invoke(propertyValue);
            int propId = PERF_VEHICLE_SPEED;
            try {
                Object id = propertyValue.getClass().getMethod("getPropertyId").invoke(propertyValue);
                if (id instanceof Number) propId = ((Number) id).intValue();
            } catch (Throwable ignored) {
                // Keep speed-mux fallback for older AAOS APIs.
            }
            if (raw != null) {
                decodeProperty(propId, raw);
                handler.post(new Runnable() {
                    @Override
                    public void run() {
                        render();
                    }
                });
            }
        } catch (Throwable error) {
            Log.e(TAG, "Cannot decode VHAL event", error);
        }
    }

    private void decodeProperty(int propId, Object raw) {
        state.lastUpdateAt = System.currentTimeMillis();
        if (raw instanceof Number) {
            float value = ((Number) raw).floatValue();
            if (propId == PERF_VEHICLE_SPEED) {
                decodeMultiplex(value);
            } else if (propId == PROP_FINAL_RISK) {
                state.risk = value;
            } else if (propId == PROP_CRITICAL_ALERT) {
                state.critical = Math.round(value) == 1;
            } else if (propId == PROP_ALERTNESS) {
                state.alertness = value > 1.0f ? value / 100.0f : value;
            } else if (propId == PROP_MIN_TTC) {
                state.ttc = value;
            } else if (propId == PROP_AI_STATUS) {
                state.aiStatus = aiFromCode(Math.round(value));
            } else if (propId == PROP_ACTION) {
                state.recommendedAction = actionFromCode(Math.round(value));
            } else if (propId == PROP_SEVERITY) {
                state.severity = severityFromCode(Math.round(value));
            } else if (propId == PROP_DRIVER_STATE) {
                state.driverState = driverFromCode(Math.round(value));
            }
            Log.i(TAG, "prop 0x" + Integer.toHexString(propId) + "=" + value);
        } else {
            Log.i(TAG, "prop 0x" + Integer.toHexString(propId) + "=" + raw);
        }
    }

    private void decodeMultiplex(float raw) {
        if (raw >= 41.0f && raw < 51.0f) {
            int group = (int) Math.floor(raw);
            int payload = Math.round((raw - group) * 1000.0f);
            state.lastUpdateAt = System.currentTimeMillis();
            switch (group) {
                case 41:
                    state.risk = payload;
                    break;
                case 42:
                    state.severity = severityFromCode(payload);
                    break;
                case 43:
                    state.driverState = driverFromCode(payload);
                    break;
                case 44:
                    state.alertness = payload / 100.0f;
                    break;
                case 45:
                    state.ttc = payload / 10.0f;
                    break;
                case 46:
                    state.critical = payload == 1;
                    break;
                case 47:
                    state.aiStatus = aiFromCode(payload);
                    break;
                case 48:
                    state.recommendedAction = actionFromCode(payload);
                    break;
                case 49:
                    state.speed = payload;
                    break;
                case 50:
                    state.safeScore = payload;
                    break;
                default:
                    Log.w(TAG, "Unknown decimal DMS mux value=" + raw);
            }
            Log.i(TAG, "mux decimal raw=" + raw + " group=" + group + " payload=" + payload);
            return;
        }

        if (raw > 0.05f && raw < 1000.0f) {
            state.lastUpdateAt = System.currentTimeMillis();
            state.speed = raw;
            Log.i(TAG, "mux speed=" + raw);
            return;
        }
        if (raw == 0.0f) {
            // Background vehicle simulator continuously pushes 0.0. Do not let it
            // overwrite the explicit 49.xxx display-speed mux value.
            return;
        }

        state.lastUpdateAt = System.currentTimeMillis();
        int code = Math.round(raw);
        int group = code / 1000;
        int payload = code % 1000;
        switch (group) {
            case 10:
                state.risk = payload;
                break;
            case 11:
                state.severity = severityFromCode(payload);
                break;
            case 12:
                state.driverState = driverFromCode(payload);
                break;
            case 13:
                state.alertness = payload / 100.0f;
                break;
            case 14:
                state.ttc = payload / 10.0f;
                break;
            case 15:
                state.critical = payload == 1;
                break;
            case 16:
                state.aiStatus = aiFromCode(payload);
                break;
            case 17:
                state.recommendedAction = actionFromCode(payload);
                break;
            default:
                Log.w(TAG, "Unknown DMS mux value=" + raw);
        }
        Log.i(TAG, "mux raw=" + raw + " group=" + group + " payload=" + payload);
    }

    private final Runnable watchdog = new Runnable() {
        @Override
        public void run() {
            long age = state.lastUpdateAt == 0 ? Long.MAX_VALUE : System.currentTimeMillis() - state.lastUpdateAt;
            if (age > OFFLINE_AFTER_MS) {
                renderOffline("WAITING FOR DATA FROM HMI BRIDGE");
            } else {
                render();
            }
            handler.postDelayed(this, WATCHDOG_MS);
        }
    };

    private void render() {
        long age = state.lastUpdateAt == 0 ? 0 : Math.max(0, System.currentTimeMillis() - state.lastUpdateAt);
        int severity = severityCode(state.severity);
        int bg = severity == 2 ? 0xff641523 : severity == 1 ? 0xff7c5209 : severity == 3 ? 0xff123d58 : 0xff081827;
        int accent = severity == 2 ? 0xfffb7185 : severity == 1 ? 0xfffacc15 : severity == 3 ? 0xff38bdf8 : 0xff22c55e;
        root.setBackground(makeBackground(bg));
        aiPill.setText("●  AI " + state.aiStatus);
        aiPill.setTextColor(accent);
        status.setText(BUILD_TAG + "  •  VHAL " + age + "ms");
        status.setTextColor(Color.WHITE);
        voiceButton.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED");
        title.setText(severity == 2 ? "CRITICAL RISK" : severity == 1 ? "WARNING" : severity == 3 ? "RECOVERY" : "SAFE DRIVING");
        String actionText = actionText(state.recommendedAction);
        action.setText(actionText);
        evidence.setText(reasonText(state.severity));
        telemetry.setText(String.format(Locale.US, "Driver: %s  •  TTC %.1fs", driverText(state.driverState), state.ttc));
        driverValue.setText(driverText(state.driverState));
        alertnessValue.setText(String.format(Locale.US, "%.0f%%", state.alertness * 100));
        ttcValue.setText(String.format(Locale.US, "%.1fs", state.ttc));
        riskValue.setText(String.format(Locale.US, "%.0f", state.risk));
        riskValue.setTextColor(accent);
        safeScoreValue.setText(String.format(Locale.US, "%.0f/100", state.safeScore));
        ecuValue.setText(ecuText(state.severity));
        speedValue.setText(String.format(Locale.US, "%.0f km/h", state.speed));
        limitValue.setText("Limit 80");
        reasonValue.setText(reasonCode(state));
        ageValue.setText(age + " ms");
        maybeSpeak(severity, actionText);
    }

    private void renderOffline(String reason) {
        if (root == null) return;
        root.setBackground(makeBackground(0xff1f2937));
        aiPill.setText("●  AI OFFLINE");
        aiPill.setTextColor(0xff94a3b8);
        status.setText(BUILD_TAG + "  •  WAITING");
        voiceButton.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED");
        title.setText("NO DATA");
        action.setText(reason);
        evidence.setText("REST -> KUKSA -> HMI Bridge -> VHAL -> APK");
        telemetry.setText("Waiting for mux frames");
        driverValue.setText("--");
        alertnessValue.setText("--");
        ttcValue.setText("--");
        riskValue.setText("--");
        riskValue.setTextColor(Color.WHITE);
        safeScoreValue.setText("--");
        ecuValue.setText("STANDBY");
        speedValue.setText("-- km/h");
        limitValue.setText("Limit 80");
        reasonValue.setText("NO DATA");
        ageValue.setText("-- ms");
        lastSeverity = -1;
    }

    private static int severityCode(String v) {
        return "WARNING".equals(v) ? 1 : "CRITICAL".equals(v) ? 2 : "RECOVERY".equals(v) ? 3 : 0;
    }

    private static String severityFromCode(int v) {
        return v == 1 ? "WARNING" : v == 2 ? "CRITICAL" : v == 3 ? "RECOVERY" : "SAFE";
    }

    private static String driverFromCode(int v) {
        return v == 1 ? "drowsy" : v == 2 ? "yawning" : v == 3 ? "distracted" : v == 4 ? "microsleep" : "alert";
    }

    private static String aiFromCode(int v) {
        return v == 0 ? "ONLINE" : v == 1 ? "DEGRADED" : "OFFLINE";
    }

    private static String actionFromCode(int v) {
        return v == 1 ? "FOCUS_FORWARD" : v == 2 ? "TAKE_BREAK" : v == 3 ? "BRAKE_SAFE" : v == 4 ? "REDUCE_SPEED" : "NONE";
    }

    private static String actionText(String v) {
        return "FOCUS_FORWARD".equals(v) ? "FOCUS FORWARD"
                : "TAKE_BREAK".equals(v) ? "TAKE A BREAK"
                : "BRAKE_SAFE".equals(v) ? "BRAKE SAFELY"
                : "REDUCE_SPEED".equals(v) ? "REDUCE SPEED"
                : "KEEP MONITORING";
    }

    private static String reasonText(String severity) {
        if ("CRITICAL".equals(severity)) return "High risk detected. Immediate driver response is required.";
        if ("WARNING".equals(severity)) return "AI detected a behavior or traffic condition that needs attention.";
        if ("RECOVERY".equals(severity)) return "Risk is decreasing. Continue monitoring the driver and road.";
        return "No critical risk detected.";
    }

    private static String ecuText(String severity) {
        if ("CRITICAL".equals(severity)) return "BRAKE ASSIST REQUESTED";
        if ("WARNING".equals(severity)) return "WARNING BUZZER ON";
        if ("RECOVERY".equals(severity)) return "RECOVERY MONITORING";
        return "STANDBY";
    }

    private static String reasonCode(State state) {
        if ("CRITICAL".equals(state.severity) && state.ttc > 0 && state.ttc <= 1.5f) return "TTC_CRITICAL";
        if ("microsleep".equals(state.driverState)) return "MICROSLEEP";
        if ("distracted".equals(state.driverState)) return "DRIVER_DISTRACTED";
        if ("WARNING".equals(state.severity)) return "DRIVER_WARNING";
        return "NONE";
    }

    private static String driverText(String v) {
        return "drowsy".equals(v) ? "Drowsy"
                : "yawning".equals(v) ? "Yawning"
                : "distracted".equals(v) ? "Distracted"
                : "microsleep".equals(v) ? "Microsleep"
                : "Alert";
    }

    private void maybeSpeak(int severity, String text) {
        if (!voiceEnabled || tts == null || severity == lastSeverity) {
            lastSeverity = severity;
            return;
        }
        long now = System.currentTimeMillis();
        if (severity == 1 && now - lastWarningVoiceAt >= 15000) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "warning");
            lastWarningVoiceAt = now;
        }
        if (severity == 2) tts.speak("Nguy hiem. " + text, TextToSpeech.QUEUE_FLUSH, null, "critical");
        lastSeverity = severity;
    }

    @Override
    public void onInit(int result) {
        if (result == TextToSpeech.SUCCESS) tts.setLanguage(new Locale("vi", "VN"));
    }

    @Override
    protected void onDestroy() {
        handler.removeCallbacks(watchdog);
        handler.removeCallbacks(vehiclePoller);
        unregisterVehicleCallback();
        if (tts != null) {
            tts.stop();
            tts.shutdown();
        }
        super.onDestroy();
    }

    private void unregisterVehicleCallback() {
        if (propertyManager == null || propertyCallback == null) return;
        try {
            Class<?> callbackClass = Class.forName("android.car.hardware.property.CarPropertyManager$CarPropertyEventCallback");
            propertyManager.getClass().getMethod("unregisterCallback", callbackClass).invoke(propertyManager, propertyCallback);
        } catch (Throwable ignored) {
            // Best effort during Activity teardown.
        }
    }

    private static final class State {
        String driverState = "alert";
        String severity = "SAFE";
        String aiStatus = "OFFLINE";
        String recommendedAction = "NONE";
        float speed = 0f;
        float risk = 0f;
        float safeScore = 100f;
        float alertness = 0f;
        float ttc = 0f;
        boolean critical = false;
        long lastUpdateAt = 0L;
    }
}
