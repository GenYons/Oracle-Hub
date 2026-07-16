import http.server
import socketserver
import os
import threading  # لمنع تجميد السيرفر المحلي أثناء الاستماع للفايربيس
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

PORT = 8000
TARGET_FOLDER = "Oracle.dev"

# 🔗 رابط قاعدة البيانات الفعلي الخاص بمشروعك
FIREBASE_DB_URL = "https://oracle-hub-98076-default-rtdb.firebaseio.com"

# 📊 جدول الأوزان الرياضية لحساب قوة الضغط وهجمات الفرق
EVENT_WEIGHTS = {
    'danger_attack': 12,  # هجمة خطيرة 🔥
    'corner': 7,          # ركنية 🚩
    'key_pass': 6,        # تمريرة مفتاحية 🔑
    'attack': 3,          # هجمة واعدة 🏃‍♂️
    'offside': 1          # تسلل 🏁
}

# ==========================================================
# 🧠 عقل المحرك التنبؤي (حساب المجالات الزمنية الذكية 15 دقيقة)
# ==========================================================
def analyze_team_pressure(current_minute, events_data):
    if current_minute < 1: 
        current_minute = 1
        
    start_min = ((current_minute - 1) // 15) * 15 + 1
    end_min = start_min + 14
    
    total_weight = 0
    
    if events_data:
        iterator = events_data.values() if isinstance(events_data, dict) else events_data
        for event in iterator:
            if isinstance(event, dict):
                try:
                    event_min = int(event.get('minute', 0))
                    if start_min <= event_min <= end_min:
                        event_type = event.get('type', '')
                        total_weight += EVENT_WEIGHTS.get(event_type, 0)
                except:
                    continue
                    
    return {
        "current_weight": total_weight,
        "goal_imminent": total_weight >= 25,  # عتبة التنبؤ
        "interval": f"{start_min}-{end_min}"
    }

# 🔄 دالة الاستماع الفوري والتحديث اللحظي المخصصة لمباراة المغرب وكندا
def on_live_state_change(event):
    try:
        # جلب العقدة الرئيسية للمباراة لضمان جلب الأسماء وهيكل البيانات بالكامل
        ref = db.reference('oracle_test_match')
        match_data = ref.get()
        if not match_data: return

        live_state = match_data.get('liveState', {})
        teams = match_data.get('teams', {})

        # قراءة الدقيقة والأحداث
        current_minute = int(live_state.get('clock', 0))
        home_events = live_state.get('homeEvents', [])
        away_events = live_state.get('awayEvents', [])

        # جلب أسماء الفرق ديناميكياً مع وضع (المغرب وكندا) كقيم افتراضية ذكية
        home_name = teams.get('home', {}).get('name', 'المغرب 🇲🇦')
        away_name = teams.get('away', {}).get('name', 'كندا 🇨🇦')

        # تشغيل المحرك التنبؤي
        home_prediction = analyze_team_pressure(current_minute, home_events)
        away_prediction = analyze_team_pressure(current_minute, away_events)

        # ضخ النتائج التنبؤية فوراً سحابياً لتقرأها شاشة العرض (index.html)
        db.reference('oracle_test_match/livePrediction').set({
            'home': home_prediction,
            'away': away_prediction
        })
        
        print(f"🔮 [تحليل ذكي] د:{current_minute} | {home_name}: {home_prediction['current_weight']}ن (وشيك: {home_prediction['goal_imminent']}) | {away_name}: {away_prediction['current_weight']}ن (وشيك: {away_prediction['goal_imminent']})")
    except Exception as e:
        print(f"❌ خطأ أثناء تشغيل المحرك التنبؤي: {e}")

# 🚀 دالة تهيئة اتصال الفايربيس في الخلفية
def start_firebase_engine():
    try:
        if os.path.exists("service_key.json"):
            cred = credentials.Certificate("service_key.json")
            firebase_admin.initialize_app(cred, {'databaseURL': FIREBASE_DB_URL})
        else:
            firebase_admin.initialize_app(options={'databaseURL': FIREBASE_DB_URL})
            
        db.reference('oracle_test_match/liveState').listen(on_live_state_change)
        print("🔥 تم ربط المحرك التنبؤي بالفايربيس وعقل المنظومة يستمع الآن...")
    except Exception as e:
        print(f"❌ تنبيه الفايربيس: يتطلب ملف الصلاحيات للتخاطب كمشرف: {e}")

# ==========================================================
# 🎯 محرك البحث الذكي عن مجلد مشروعك داخل ذاكرة الأندرويد
# ==========================================================
possible_paths = [
    os.path.join("/storage/emulated/0", TARGET_FOLDER),
    os.path.join("/storage/emulated/0/Documents", TARGET_FOLDER),
    os.path.join("/storage/emulated/0/Download", TARGET_FOLDER),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), TARGET_FOLDER),
    os.path.dirname(os.path.abspath(__file__)) 
]

folder_found = False
for path in possible_paths:
    if os.path.exists(path) and os.path.isdir(path):
        if os.path.exists(os.path.join(path, "panel.html")):
            os.chdir(path)
            folder_found = True
            break

class TargetedOracleHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

TargetedOracleHandler.extensions_map.update({
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.html': 'text/html; charset=utf-8',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
})

print("=" * 60)
if folder_found:
    print(f"🎯 رائع! عثرت المنظومة على مجلد [{TARGET_FOLDER}] بنجاح.")
    print(f"📍 المسار النشط للسيرفر الآن: {os.getcwd()}")
else:
    print(f"⚠️ تنبيه: لم أجد مجلد [{TARGET_FOLDER}] في المسارات الشائعة.")
    print(f"📍 المسار الحالي: {os.getcwd()}")
print("⏳ جاري إطلاق سيرفر البث المحلي النقي والمحرك التنبؤي...")
print("=" * 60)

threading.Thread(target=start_firebase_engine, daemon=True).start()

try:
    with socketserver.TCPServer(("", PORT), TargetedOracleHandler) as httpd:
        print(f"🚀 السيرفر مستقر ويعمل الآن على الأرض الصلبة!")
        print(f"🔗 رابط لوحة التحكم:   http://localhost:{PORT}/panel.html")
        print(f"🔗 رابط شاشة العرض:   http://localhost:{PORT}/index.html")
        print("-" * 60)
        print("🛑 لإيقاف السيرفر، اضغط على زر الإيقاف in Pydroid 3.")
        print("=" * 60)
        httpd.serve_forever()
except OSError:
    print(f"❌ المنفذ {PORT} مشغول حالياً.")
    print("💡 الحل: أغلق تطبيق Pydroid 3 بالكامل من الخلفية وأعد تشغيله.")
except KeyboardInterrupt:
    print("\n🛑 تم إيقاف السيرفر المحلي.")