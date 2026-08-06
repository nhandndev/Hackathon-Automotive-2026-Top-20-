package vn.fpt.dms.hmi;

import android.app.Activity;
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
    private static final int PERF_VEHICLE_SPEED = 291504647; // 0x11600207
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
        root.setGravity(Gravity.CENTER);
        root.setPadding(50, 35, 50, 35);
        root.setBackgroundColor(0xff101826);

        status = text(18, Color.WHITE);
        title = text(44, Color.WHITE);
        action = text(28, Color.WHITE);
        evidence = text(22, 0xffd8dce8);
        telemetry = text(20, 0xffd8dce8);

        Button voice = new Button(this);
        voice.setText("VOICE ON");
        voice.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                voiceEnabled = !voiceEnabled;
                voice.setText(voiceEnabled ? "VOICE ON" : "VOICE MUTED");
                if (!voiceEnabled && tts != null) tts.stop();
                render();
            }
        });

        root.addView(status);
        root.addView(title);
        root.addView(action);
        root.addView(evidence);
        root.addView(telemetry);
        root.addView(voice);
        setContentView(root);
        renderOffline("DANG CHO DU LIEU TU HMI BRIDGE");
    }

    private TextView text(int sp, int color) {
        TextView view = new TextView(this);
        view.setTextSize(sp);
        view.setTextColor(color);
        view.setGravity(Gravity.CENTER);
        view.setPadding(18, 10, 18, 10);
        return view;
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
            Log.i(TAG, "Registered DMS multiplex transport on PERF_VEHICLE_SPEED with callback + polling fallback");
        } catch (Throwable error) {
            Log.e(TAG, "Cannot connect Android Car/VHAL runtime", error);
            renderOffline("CAR SERVICE/VHAL CHUA SAN SANG");
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
            Method getFloatProperty = propertyManager.getClass().getMethod("getFloatProperty", int.class, int.class);
            Object raw = getFloatProperty.invoke(propertyManager, PERF_VEHICLE_SPEED, AREA_GLOBAL);
            if (raw instanceof Number) {
                float value = ((Number) raw).floatValue();
                decodeMultiplex(value);
                render();
            }
        } catch (Throwable error) {
            Log.w(TAG, "VHAL polling fallback could not read PERF_VEHICLE_SPEED", error);
        }
    }

    private void registerVehicleCallback() throws Exception {
        Class<?> callbackClass = Class.forName("android.car.hardware.property.CarPropertyManager$CarPropertyEventCallback");
        propertyCallback = Proxy.newProxyInstance(
                callbackClass.getClassLoader(),
                new Class<?>[]{callbackClass},
                new VehicleCallbackHandler());
        Method register = propertyManager.getClass().getMethod("registerCallback", callbackClass, int.class, float.class);
        Object ok = register.invoke(propertyManager, propertyCallback, PERF_VEHICLE_SPEED, SENSOR_RATE_HZ);
        Log.i(TAG, "register 0x" + Integer.toHexString(PERF_VEHICLE_SPEED) + "=" + ok);
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
            if (raw instanceof Number) {
                decodeMultiplex(((Number) raw).floatValue());
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

    private void decodeMultiplex(float raw) {
        state.lastUpdateAt = System.currentTimeMillis();
        int code = Math.round(raw);

        if (raw > 0.05f && raw < 1000.0f) {
            state.speed = raw;
            Log.i(TAG, "mux speed=" + raw);
            return;
        }
        if (raw == 0.0f) {
            // Background vehicle simulator continuously pushes 0.0. Keep speed 0 but DO NOT abort multiplex decoding!
            state.speed = 0.0f;
            return;
        }

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
                renderOffline("DANG CHO DU LIEU TU HMI BRIDGE");
            } else {
                render();
            }
            handler.postDelayed(this, WATCHDOG_MS);
        }
    };

    private void render() {
        long age = state.lastUpdateAt == 0 ? 0 : Math.max(0, System.currentTimeMillis() - state.lastUpdateAt);
        int severity = severityCode(state.severity);
        root.setBackgroundColor(severity == 2 ? 0xff8b111c : severity == 1 ? 0xff8a5a00 : severity == 3 ? 0xff123d58 : 0xff083529);
        status.setText("AI " + state.aiStatus + (voiceEnabled ? "  •  VOICE ON" : "  •  VOICE MUTED") + "  •  VHAL " + age + "ms");
        title.setText(severity == 2 ? "NGUY HIEM" : severity == 1 ? "CANH BAO" : severity == 3 ? "DA AN TOAN TRO LAI" : "LAI XE AN TOAN");
        String actionText = actionText(state.recommendedAction);
        action.setText(actionText);
        evidence.setText("Tai xe: " + driverText(state.driverState) + (state.ttc > 0 ? String.format(Locale.US, "  •  TTC %.1fs", state.ttc) : ""));
        telemetry.setText(String.format(Locale.US, "%.0f km/h     Risk %.0f     Alertness %.0f%%", state.speed, state.risk, state.alertness * 100));
        maybeSpeak(severity, actionText);
    }

    private void renderOffline(String reason) {
        if (root == null) return;
        root.setBackgroundColor(0xff1f2937);
        status.setText("AI OFFLINE" + (voiceEnabled ? "  •  VOICE ON" : "  •  VOICE MUTED"));
        title.setText("KHONG CO DU LIEU");
        action.setText(reason);
        evidence.setText("REST -> KUKSA -> HMI Bridge -> VHAL -> APK");
        telemetry.setText("-- km/h     Risk --     Alertness --");
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
        return "FOCUS_FORWARD".equals(v) ? "TAP TRUNG PHIA TRUOC"
                : "TAKE_BREAK".equals(v) ? "HAY NGHI NGOI"
                : "BRAKE_SAFE".equals(v) ? "PHANH AN TOAN"
                : "REDUCE_SPEED".equals(v) ? "GIAM TOC DO"
                : "TIEP TUC QUAN SAT";
    }

    private static String driverText(String v) {
        return "drowsy".equals(v) ? "Buon ngu"
                : "yawning".equals(v) ? "Ngap"
                : "distracted".equals(v) ? "Mat tap trung"
                : "microsleep".equals(v) ? "Vi ngu"
                : "Tinh tao";
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
        float alertness = 0f;
        float ttc = 0f;
        boolean critical = false;
        long lastUpdateAt = 0L;
    }
}
