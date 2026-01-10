# 🦅 Next-Gen Face Recognition & Identity Intelligence System
### *Advanced Attendance, Emotion Analysis, and Security Forensics*

---

> ### 🌍 Language / اللغة
> **[English Documentation](#english-version)** | **[النسخة العربية الكاملة](#arabic-version)**

---

<a name="english-version"></a>

# 🇬🇧 English Documentation

## 🌟 Overview
The **Identity Intelligence System** is an advanced, enterprise-grade desktop application designed for seamless identity management and security forensics. Built using **Python 3.13** and **PyQt6**, it leverages high-precision computer vision to handle real-time attendance, facial expression (emotion) tracking, and liveness detection.

## 🚀 Key Innovation Pillars

### 🧠 1. Advanced Recognition Engine (AI Core)
The engine is not just a wrapper; it's a fine-tuned pipeline:
- **High-Accuracy Encoding**: Utilizes the Dlib-based `face_recognition` models with custom **Multi-Jittering** (sampling faces up to 10 times) to ensure recognition remains stable across different lighting and angles.
- **CLAHE Pre-Processing**: Automatically applies *Contrast Limited Adaptive Histogram Equalization* (CLAHE) to every frame.
- **Spatial Normalization**: Emotion detection uses **Normalized Landmark Ratios** based on eye-to-eye distance.

### 🎭 2. Emotional Intelligence & Liveness
- **Emotion Tracking**: Real-time analysis of "Happy", "Neutral", and "Surprised" states.
- **Smart Voice Greetings**: Integrated TTS (Text-to-Speech) for personalized feedback.
- **Anti-Spoofing (Liveness)**: Prevents "Photo Attacks" by requiring a natural blink (EAR).

### 🕵️‍♂️ 3. Security & Forensics
- **Stranger Tracking**: Any unrecognized face seen for more than 1.5s is automatically photographed and logged.
- **Offline Video Analysis**: Forensic analysis of CCTV footage to extract appearance time codes.

## 🎨 UI/UX Excellence
- **Carousel Tab Transitions**: Smooth, horizontal sliding animations (Out-Expo).
- **Scanning Laser Overlay**: Dynamic green laser line sweeps the camera feed.
- **Touch & Gesture Support**: Kinetic scrolling and optimized touch padding.

## ⚙️ AI Logic & Mathematical Heuristics
- **EAR formula**: $$EAR = \frac{||p2-p6|| + ||p3-p5||}{2 \times ||p1-p4||}$$
- **Emotion gates**: Based on mouth openness ratio ($H_{mouth}$) and eyebrow elevation ($E$).

---

<br><br>
<a name="arabic-version"></a>

# 🇸🇦 التوثيق باللغة العربية

---

# 🦅 نظام استخبارات الهوية والتعرف المتطور على الوجوه (Next-Gen Face Intelligence)
### *الجيل الثالث: حضور ذكي، تحليل مشاعر، ورقابة أمنية جنائية*

## 🌟 نظرة عامة (Overview)
هذا النظام ليس مجرد برنامج حضور وانصراف، بل هو منصة استخباراتية متكاملة تعتمد على الرؤية الحاسوبية (Computer Vision) والذكاء الاصطناعي لإدارة الهوية وتحليل السلوك البشري. تم بناؤه باستخدام **Python 3.13** و **PyQt6** ليوفر أداءً مؤسسياً فائق الدقة مع واجهة مستخدم عصرية وسلسة.

## 🚀 الركائز التقنية والابتكارية (Technical Pillars)

### 🧠 1. محرك التعرف المتقدم (Core AI)
- **تشفير الوجه (High-Accuracy Encoding)**: نستخدم نماذج Dlib مع تقنية **Multi-Jittering** (10 عينات للوجه) لضمان دقة التعرف.
- **معالجة CLAHE**: توحيد الإضاءة تلقائياً في جميع الظروف.
- **المعايرة المكانية (Spatial Normalization)**: حساب النسب المعيارية لضمان دقة المشاعر بغض النظر عن المسافة.

### 🎭 2. الذكاء العاطفي وكشف التزييف (Liveness)
- **تتبع المشاعر**: تحليل لحظي لحالات (سعيد، محايد، متفاجئ).
- **كشف الحيوية (Anti-Spoofing)**: منع هجمات الصور عبر تتبع رمش العين (EAR).
- **التحية الصوتية**: نظام TTS لترحيب شخصي ذكي.

### 🕵️‍♂️ 3. الرقابة الأمنية والتحليل الجنائي (Forensics)
- **تتبع الغرباء (Stranger Tracking)**: تصوير فوري وحفظ بيانات أي شخص غير معروف.
- **تحليل الفيديو دون اتصال (Offline Analysis)**: استخراج الأشخاص المعروفين من تسجيلات الكاميرات (CCTV).

## 🎨 استعراض واجهات النظام (UI Walkthrough)

### 1️⃣ واجهة تسجيل الدخول >>>>>> كلمة المرور:sam123
> [!TIP]
<img width="301" height="176" alt="image" src="https://github.com/user-attachments/assets/6cf90ee3-1edb-41c5-933e-c41a3a7b2adb" />
*

### 2️⃣ واجهة إدارة الهوية
> [!TIP]
> 
<img width="1366" height="724" alt="image" src="https://github.com/user-attachments/assets/b00e4293-36cc-49df-94e3-b65a409b3371" />

*

### 3️⃣ واجهة الحضور والتحقق الذكي
> [!TIP]
<img width="1366" height="723" alt="image" src="https://github.com/user-attachments/assets/f0b29300-f084-4261-a0a0-f31a655cf52e" />
*

### 4️⃣ لوحة التحليلات والإحصائيات
> [!TIP]
<img width="1366" height="728" alt="image" src="https://github.com/user-attachments/assets/cc16c6b5-9971-4176-8e0d-8f2ffe1f0e2f" />
*

## 🛠️ التوثيق التقني العميق (Deep Tech)

### ⚙️ 1. الخوارزميات والمنطق الرياضي
#### **أ. كشف المشاعر**
تعتمد على حساب المسافات النسبية:
- **الاندهاش**: فتحة الحاجب أو الفم > 45% من عرض الوجه.
- **السعادة**: عرض الفم > 95% من عرض الوجه مع رفع الزوايا.

#### **ب. كشف الرمش (EAR)**
يتم التأكد من الحيوية عبر المعادلة: $$EAR = \frac{||p2-p6|| + ||p3-p5||}{2 \times ||p1-p4||}$$

### 🏗️ 2. العمارة البرمجية
- **نمط التشغيل**: خيوط معالجة (Threads) منفصلة لمنع تجمد الواجهة.
- **قاعدة البيانات**: SQLite 3 مع تكرار آمن للبيانات.

---

## ✍️ تطوير المهندس
**م. سلطان شمسان (Eng. Sultan Shamsan)**  
أخصائي حلول الذكاء الاصطناعي المتقدمة  
[GitHub](https://github.com/s-u-l-t-a-n-7/sultan-shamsan) | [LinkedIn](https://www.linkedin.com/in/sultan-shamsan/)

---
*Developed for Advanced AI Enterprise Solutions.*
