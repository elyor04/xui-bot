"""Internationalization: t(key, lang, **kwargs) → str.

Supported languages:
  en – English (default)
  uz – O'zbek
  ru – Русский
  zh – 中文
  fa – فارسی
"""
from __future__ import annotations

LANGS: dict[str, str] = {
    "en": "🇬🇧 English",
    "uz": "🇺🇿 O'zbek",
    "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文",
    "fa": "🇮🇷 فارسی",
}
DEFAULT_LANG = "en"

_S: dict[str, dict[str, str]] = {
    # ── Navigation ──────────────────────────────────────────────────────────
    "btn_menu": {
        "en": "🏠 Menu", "uz": "🏠 Menyu", "ru": "🏠 Меню",
        "zh": "🏠 菜单", "fa": "🏠 منو",
    },
    "btn_back": {
        "en": "⬅️ Back", "uz": "⬅️ Orqaga", "ru": "⬅️ Назад",
        "zh": "⬅️ 返回", "fa": "⬅️ بازگشت",
    },
    "btn_refresh": {
        "en": "🔄 Refresh", "uz": "🔄 Yangilash", "ru": "🔄 Обновить",
        "zh": "🔄 刷新", "fa": "🔄 بروزرسانی",
    },
    "btn_cancel": {
        "en": "✖️ Cancel", "uz": "✖️ Bekor", "ru": "✖️ Отмена",
        "zh": "✖️ 取消", "fa": "✖️ لغو",
    },
    "btn_continue": {
        "en": "➡️ Continue", "uz": "➡️ Davom etish", "ru": "➡️ Продолжить",
        "zh": "➡️ 继续", "fa": "➡️ ادامه",
    },
    "btn_custom": {
        "en": "✏️ Custom", "uz": "✏️ Maxsus", "ru": "✏️ Своё",
        "zh": "✏️ 自定义", "fa": "✏️ سفارشی",
    },
    "btn_language": {
        "en": "🌐 Language", "uz": "🌐 Til", "ru": "🌐 Язык",
        "zh": "🌐 语言", "fa": "🌐 زبان",
    },
    "loading": {
        "en": "Loading…", "uz": "Yuklanmoqda…", "ru": "Загрузка…",
        "zh": "加载中…", "fa": "در حال بارگذاری…",
    },
    "cancelled": {
        "en": "Cancelled.", "uz": "Bekor qilindi.", "ru": "Отменено.",
        "zh": "已取消。", "fa": "لغو شد.",
    },
    # ── Language selection ───────────────────────────────────────────────────
    "choose_language": {
        "en": "🌐 Choose your language:",
        "uz": "🌐 Tilni tanlang:",
        "ru": "🌐 Выберите язык:",
        "zh": "🌐 选择语言：",
        "fa": "🌐 زبان خود را انتخاب کنید:",
    },
    "language_set": {
        "en": "✅ Language set to English.",
        "uz": "✅ Til O'zbekchaga o'zgartirildi.",
        "ru": "✅ Язык изменён на Русский.",
        "zh": "✅ 语言已设置为中文。",
        "fa": "✅ زبان به فارسی تغییر یافت.",
    },
    "btn_search_inline": {
        "en": "🔍 Search inline", "uz": "🔍 Inline qidirish", "ru": "🔍 Поиск inline",
        "zh": "🔍 内联搜索", "fa": "🔍 جستجوی inline",
    },
    # ── Timezone selection ───────────────────────────────────────────────────
    "btn_timezone": {
        "en": "🕐 Timezone", "uz": "🕐 Vaqt zonasi", "ru": "🕐 Часовой пояс",
        "zh": "🕐 时区", "fa": "🕐 منطقه زمانی",
    },
    "tz_title": {
        "en": "🕐 <b>Timezone settings</b>\n\nCurrent timezone: <code>{tz}</code>\n\nUse the button below to search and select a timezone.",
        "uz": "🕐 <b>Vaqt zonasi</b>\n\nJoriy zona: <code>{tz}</code>\n\nVaqt zonasini tanlash uchun quyidagi tugmani bosing.",
        "ru": "🕐 <b>Часовой пояс</b>\n\nТекущий пояс: <code>{tz}</code>\n\nНажмите кнопку ниже, чтобы найти и выбрать часовой пояс.",
        "zh": "🕐 <b>时区设置</b>\n\n当前时区：<code>{tz}</code>\n\n点击下方按钮搜索并选择时区。",
        "fa": "🕐 <b>تنظیمات منطقه زمانی</b>\n\nمنطقه فعلی: <code>{tz}</code>\n\nبرای جستجو و انتخاب منطقه زمانی دکمه زیر را بزنید.",
    },
    "tz_search_btn": {
        "en": "🔍 Search timezone", "uz": "🔍 Vaqt zonasini qidirish", "ru": "🔍 Найти часовой пояс",
        "zh": "🔍 搜索时区", "fa": "🔍 جستجوی منطقه زمانی",
    },
    "tz_set": {
        "en": "✅ Timezone set to <b>{tz}</b>",
        "uz": "✅ Vaqt zonasi <b>{tz}</b> ga o'zgartirildi",
        "ru": "✅ Часовой пояс установлен: <b>{tz}</b>",
        "zh": "✅ 时区已设置为 <b>{tz}</b>",
        "fa": "✅ منطقه زمانی به <b>{tz}</b> تغییر یافت",
    },
    "tz_invalid": {
        "en": "❌ Unknown timezone. Use the search button to pick a valid one.",
        "uz": "❌ Noma'lum vaqt zonasi. Qidirish tugmasidan foydalaning.",
        "ru": "❌ Неизвестный часовой пояс. Используйте кнопку поиска.",
        "zh": "❌ 未知时区，请使用搜索按钮选择有效时区。",
        "fa": "❌ منطقه زمانی نامعتبر. لطفاً از دکمه جستجو استفاده کنید.",
    },
    # ── Home ────────────────────────────────────────────────────────────────
    "home_admin": {
        "en": "👋 <b>Admin panel</b>\nSigned in as <code>{name}</code>.\n\nManage clients, inbounds and the server below.",
        "uz": "👋 <b>Admin paneli</b>\n<code>{name}</code> sifatida kirildi.\n\nQuyida mijozlar, inboundlar va serverni boshqaring.",
        "ru": "👋 <b>Панель администратора</b>\nВы вошли как <code>{name}</code>.\n\nУправляйте клиентами, входящими и сервером ниже.",
        "zh": "👋 <b>管理面板</b>\n已登录为 <code>{name}</code>。\n\n在下方管理客户端、入站和服务器。",
        "fa": "👋 <b>پنل مدیریت</b>\nوارد شده به عنوان <code>{name}</code>.\n\nمدیریت کلاینت‌ها، اینباند‌ها و سرور در زیر.",
    },
    "home_client_linked": {
        "en": "👋 Welcome back, <b>{name}</b>.\nYour account is linked to <code>{email}</code>.",
        "uz": "👋 Xush kelibsiz, <b>{name}</b>.\nHisobingiz <code>{email}</code> ga bog'langan.",
        "ru": "👋 С возвращением, <b>{name}</b>.\nВаш аккаунт привязан к <code>{email}</code>.",
        "zh": "👋 欢迎回来，<b>{name}</b>。\n您的账户已绑定到 <code>{email}</code>。",
        "fa": "👋 خوش آمدید، <b>{name}</b>.\nحساب شما به <code>{email}</code> متصل است.",
    },
    "home_client_unlinked": {
        "en": "👋 Welcome, <b>{name}</b>.\n\nTap <b>Link my account</b> to connect.",
        "uz": "👋 Xush kelibsiz, <b>{name}</b>.\n\nUlash uchun <b>Hisobimni ulash</b> ni bosing.",
        "ru": "👋 Добро пожаловать, <b>{name}</b>.\n\nНажмите <b>Привязать аккаунт</b> для подключения.",
        "zh": "👋 欢迎，<b>{name}</b>。\n\n点击 <b>绑定我的账户</b> 进行连接。",
        "fa": "👋 خوش آمدید، <b>{name}</b>.\n\nبرای اتصال روی <b>اتصال حساب من</b> ضربه بزنید.",
    },
    "mode_picker_prompt": {
        "en": "👋 How would you like to use the bot?",
        "uz": "👋 Botdan qanday foydalanmoqchisiz?",
        "ru": "👋 Как вы хотите использовать бота?",
        "zh": "👋 您想如何使用机器人？",
        "fa": "👋 چگونه می‌خواهید از ربات استفاده کنید؟",
    },
    "pick_account": {
        "en": "👤 Which account is yours?",
        "uz": "👤 Qaysi hisob sizniki?",
        "ru": "👤 Какой аккаунт ваш?",
        "zh": "👤 哪个账户是您的？",
        "fa": "👤 کدام حساب متعلق به شماست؟",
    },
    "no_client_accounts": {
        "en": "No client accounts are assigned to your Telegram ID.",
        "uz": "Telegram ID ingizga hech qanday mijoz hisobi biriktirilmagan.",
        "ru": "К вашему Telegram ID не привязан ни один клиентский аккаунт.",
        "zh": "您的 Telegram ID 没有分配任何客户端账户。",
        "fa": "هیچ حساب مشتری به شناسه تلگرام شما اختصاص داده نشده است.",
    },
    # ── Help ────────────────────────────────────────────────────────────────
    "help_admin": {
        "en": (
            "<b>Admin commands</b>\n"
            "/start – open the menu\n"
            "/find &lt;email&gt; – jump straight to a client\n"
            "/cancel – abort the current action\n\n"
            "Everything else is driven by the inline buttons."
        ),
        "uz": (
            "<b>Admin buyruqlari</b>\n"
            "/start – menyuni ochish\n"
            "/find &lt;email&gt; – mijozga o'tish\n"
            "/cancel – amalni bekor qilish\n\n"
            "Qolganlar inline tugmalar orqali boshqariladi."
        ),
        "ru": (
            "<b>Команды администратора</b>\n"
            "/start – открыть меню\n"
            "/find &lt;email&gt; – перейти к клиенту\n"
            "/cancel – прервать текущее действие\n\n"
            "Всё остальное управляется кнопками."
        ),
        "zh": (
            "<b>管理员命令</b>\n"
            "/start – 打开菜单\n"
            "/find &lt;email&gt; – 直接跳转到客户端\n"
            "/cancel – 中止当前操作\n\n"
            "其余功能通过内联按钮操作。"
        ),
        "fa": (
            "<b>دستورات مدیر</b>\n"
            "/start – باز کردن منو\n"
            "/find &lt;email&gt; – رفتن مستقیم به کلاینت\n"
            "/cancel – لغو عملیات جاری\n\n"
            "بقیه با دکمه‌های اینلاین مدیریت می‌شود."
        ),
    },
    "help_client": {
        "en": (
            "<b>Commands</b>\n"
            "/start – open the menu\n"
            "/cancel – abort the current action\n\n"
            "Use the buttons to link your account and view usage."
        ),
        "uz": (
            "<b>Buyruqlar</b>\n"
            "/start – menyuni ochish\n"
            "/cancel – amalni bekor qilish\n\n"
            "Hisobingizni ulash va foydalanishni ko'rish uchun tugmalardan foydalaning."
        ),
        "ru": (
            "<b>Команды</b>\n"
            "/start – открыть меню\n"
            "/cancel – прервать текущее действие\n\n"
            "Используйте кнопки для привязки аккаунта и просмотра статистики."
        ),
        "zh": (
            "<b>命令</b>\n"
            "/start – 打开菜单\n"
            "/cancel – 中止当前操作\n\n"
            "使用按钮绑定账户并查看使用情况。"
        ),
        "fa": (
            "<b>دستورات</b>\n"
            "/start – باز کردن منو\n"
            "/cancel – لغو عملیات جاری\n\n"
            "از دکمه‌ها برای اتصال حساب و مشاهده مصرف استفاده کنید."
        ),
    },
    # ── Admin menu buttons ───────────────────────────────────────────────────
    "btn_sorted_traffic": {
        "en": "📊 Sorted Traffic Report", "uz": "📊 Traffic Hisoboti",
        "ru": "📊 Отчёт по трафику", "zh": "📊 流量排行", "fa": "📊 گزارش ترافیک",
    },
    "btn_server": {
        "en": "📈 Server", "uz": "📈 Server", "ru": "📈 Сервер",
        "zh": "📈 服务器", "fa": "📈 سرور",
    },
    "btn_reset_all": {
        "en": "🔄 Reset All Traffics", "uz": "🔄 Barchasini Tiklash",
        "ru": "🔄 Сбросить весь трафик", "zh": "🔄 重置所有流量", "fa": "🔄 بازنشانی همه ترافیک‌ها",
    },
    "btn_backup": {
        "en": "💾 Backup", "uz": "💾 Zaxira", "ru": "💾 Резервная копия",
        "zh": "💾 备份", "fa": "💾 پشتیبان",
    },
    "btn_restart_xray": {
        "en": "⚡ Restart Xray", "uz": "⚡ Xrayni qayta ishga tushirish",
        "ru": "⚡ Перезапустить Xray", "zh": "⚡ 重启 Xray", "fa": "⚡ راه‌اندازی مجدد Xray",
    },
    "btn_inbounds": {
        "en": "📦 Inbounds", "uz": "📦 Inboundlar", "ru": "📦 Входящие",
        "zh": "📦 入站", "fa": "📦 اینباندها",
    },
    "btn_deplete_soon": {
        "en": "⚠️ Deplete Soon", "uz": "⚠️ Tez Tugaydi", "ru": "⚠️ Скоро кончится",
        "zh": "⚠️ 即将耗尽", "fa": "⚠️ به زودی تمام می‌شود",
    },
    "btn_commands": {
        "en": "📋 Commands", "uz": "📋 Buyruqlar", "ru": "📋 Команды",
        "zh": "📋 命令", "fa": "📋 دستورات",
    },
    "btn_online": {
        "en": "🟢 Online", "uz": "🟢 Onlayn", "ru": "🟢 Онлайн",
        "zh": "🟢 在线", "fa": "🟢 آنلاین",
    },
    "btn_clients": {
        "en": "👥 Clients", "uz": "👥 Mijozlar", "ru": "👥 Клиенты",
        "zh": "👥 客户端", "fa": "👥 کلاینت‌ها",
    },
    "btn_create_client": {
        "en": "➕ Create client", "uz": "➕ Mijoz yaratish", "ru": "➕ Создать клиента",
        "zh": "➕ 创建客户端", "fa": "➕ ایجاد کلاینت",
    },
    "btn_switch_to_client": {
        "en": "👤 Switch to client", "uz": "👤 Mijozga o'tish", "ru": "👤 Переключиться на клиента",
        "zh": "👤 切换到客户端", "fa": "👤 تغییر به کلاینت",
    },
    "btn_switch_to_admin": {
        "en": "⚙️ Switch to admin", "uz": "⚙️ Adminga o'tish", "ru": "⚙️ Переключиться на админа",
        "zh": "⚙️ 切换到管理员", "fa": "⚙️ تغییر به مدیر",
    },
    "btn_admin_panel": {
        "en": "⚙️ Admin panel", "uz": "⚙️ Admin paneli", "ru": "⚙️ Панель администратора",
        "zh": "⚙️ 管理面板", "fa": "⚙️ پنل مدیریت",
    },
    # ── Client menu buttons ──────────────────────────────────────────────────
    "btn_my_account": {
        "en": "📈 My account", "uz": "📈 Mening hisobim", "ru": "📈 Мой аккаунт",
        "zh": "📈 我的账户", "fa": "📈 حساب من",
    },
    "btn_my_configs": {
        "en": "🔗 My configs", "uz": "🔗 Mening konfiglarim", "ru": "🔗 Мои конфиги",
        "zh": "🔗 我的配置", "fa": "🔗 پیکربندی‌های من",
    },
    "btn_my_qr": {
        "en": "📷 My QR", "uz": "📷 Mening QR", "ru": "📷 Мой QR",
        "zh": "📷 我的二维码", "fa": "📷 QR من",
    },
    "btn_unlink": {
        "en": "🔌 Unlink", "uz": "🔌 Uzish", "ru": "🔌 Отвязать",
        "zh": "🔌 取消绑定", "fa": "🔌 قطع اتصال",
    },
    "btn_link_account": {
        "en": "🔗 Link my account", "uz": "🔗 Hisobimni ulash", "ru": "🔗 Привязать аккаунт",
        "zh": "🔗 绑定我的账户", "fa": "🔗 اتصال حساب من",
    },
    # ── Client card action buttons ────────────────────────────────────────────
    "btn_reset_traffic": {
        "en": "♻️ Reset traffic", "uz": "♻️ Trafikni tiklash", "ru": "♻️ Сбросить трафик",
        "zh": "♻️ 重置流量", "fa": "♻️ بازنشانی ترافیک",
    },
    "btn_extend_days": {
        "en": "➕ Extend days", "uz": "➕ Kunlarni uzaytirish", "ru": "➕ Продлить дни",
        "zh": "➕ 延长天数", "fa": "➕ افزایش روز",
    },
    "btn_set_quota": {
        "en": "💽 Set quota", "uz": "💽 Kvotani o'rnatish", "ru": "💽 Установить квоту",
        "zh": "💽 设置配额", "fa": "💽 تنظیم سهمیه",
    },
    "btn_set_expiry": {
        "en": "📅 Set expiry", "uz": "📅 Muddatni o'rnatish", "ru": "📅 Установить срок",
        "zh": "📅 设置到期", "fa": "📅 تنظیم انقضا",
    },
    "btn_ips": {
        "en": "🌐 IPs", "uz": "🌐 IP'lar", "ru": "🌐 IP-адреса",
        "zh": "🌐 IP地址", "fa": "🌐 آی‌پی‌ها",
    },
    "btn_clear_ips": {
        "en": "🧽 Clear IPs", "uz": "🧽 IP'larni tozalash", "ru": "🧽 Очистить IP",
        "zh": "🧽 清除IP", "fa": "🧽 پاک کردن آی‌پی‌ها",
    },
    "btn_ip_limit": {
        "en": "🔢 IP limit", "uz": "🔢 IP cheklov", "ru": "🔢 Лимит IP",
        "zh": "🔢 IP限制", "fa": "🔢 محدودیت IP",
    },
    "btn_disable": {
        "en": "⏸ Disable", "uz": "⏸ O'chirish", "ru": "⏸ Отключить",
        "zh": "⏸ 禁用", "fa": "⏸ غیرفعال",
    },
    "btn_enable": {
        "en": "▶️ Enable", "uz": "▶️ Yoqish", "ru": "▶️ Включить",
        "zh": "▶️ 启用", "fa": "▶️ فعال",
    },
    "btn_sub_url": {
        "en": "🔗 Sub URL", "uz": "🔗 Sub URL", "ru": "🔗 Sub URL",
        "zh": "🔗 订阅链接", "fa": "🔗 لینک اشتراک",
    },
    "btn_ind_links": {
        "en": "🔗 Ind. links", "uz": "🔗 Alohida linklar", "ru": "🔗 Инд. ссылки",
        "zh": "🔗 独立链接", "fa": "🔗 لینک‌های جداگانه",
    },
    "btn_qr": {
        "en": "📷 QR", "uz": "📷 QR", "ru": "📷 QR",
        "zh": "📷 QR码", "fa": "📷 QR",
    },
    "btn_delete": {
        "en": "🗑 Delete", "uz": "🗑 O'chirish", "ru": "🗑 Удалить",
        "zh": "🗑 删除", "fa": "🗑 حذف",
    },
    "btn_set_tgid": {
        "en": "👤 Set TG ID", "uz": "👤 TG ID belgilash", "ru": "👤 Установить TG ID",
        "zh": "👤 设置TG ID", "fa": "👤 تنظیم شناسه تلگرام",
    },
    "btn_all_clients": {
        "en": "👥 All clients", "uz": "👥 Barcha mijozlar", "ru": "👥 Все клиенты",
        "zh": "👥 所有客户端", "fa": "👥 همه کلاینت‌ها",
    },
    "btn_pick_tg_user": {
        "en": "👤 Pick a Telegram user", "uz": "👤 Telegram foydalanuvchi tanlash",
        "ru": "👤 Выбрать пользователя", "zh": "👤 选择Telegram用户", "fa": "👤 انتخاب کاربر تلگرام",
    },
    # ── Confirm buttons ──────────────────────────────────────────────────────
    "btn_yes_delete": {
        "en": "✅ Yes, delete", "uz": "✅ Ha, o'chirish", "ru": "✅ Да, удалить",
        "zh": "✅ 是，删除", "fa": "✅ بله، حذف",
    },
    "btn_yes_create": {
        "en": "✅ Create", "uz": "✅ Yaratish", "ru": "✅ Создать",
        "zh": "✅ 创建", "fa": "✅ ایجاد",
    },
    "btn_yes_reset_all": {
        "en": "✅ Yes, reset all", "uz": "✅ Ha, barchasini tiklash", "ru": "✅ Да, сбросить всё",
        "zh": "✅ 是，全部重置", "fa": "✅ بله، همه را بازنشانی کن",
    },
    # ── Server status ────────────────────────────────────────────────────────
    "server_xray_version": {
        "en": "📡 Xray Version: {v}", "uz": "📡 Xray Versiya: {v}", "ru": "📡 Версия Xray: {v}",
        "zh": "📡 Xray版本：{v}", "fa": "📡 نسخه Xray: {v}",
    },
    "server_ipv4": {
        "en": "🌐 IPv4: {v}", "uz": "🌐 IPv4: {v}", "ru": "🌐 IPv4: {v}",
        "zh": "🌐 IPv4：{v}", "fa": "🌐 IPv4: {v}",
    },
    "server_ipv6": {
        "en": "🌐 IPv6: {v}", "uz": "🌐 IPv6: {v}", "ru": "🌐 IPv6: {v}",
        "zh": "🌐 IPv6：{v}", "fa": "🌐 IPv6: {v}",
    },
    "server_uptime": {
        "en": "⏳ Uptime: {v}", "uz": "⏳ Ishlash vaqti: {v}", "ru": "⏳ Аптайм: {v}",
        "zh": "⏳ 运行时间：{v}", "fa": "⏳ آپتایم: {v}",
    },
    "server_load": {
        "en": "📈 System Load: {v}", "uz": "📈 Tizim yuklanishi: {v}", "ru": "📈 Нагрузка: {v}",
        "zh": "📈 系统负载：{v}", "fa": "📈 بار سیستم: {v}",
    },
    "server_ram": {
        "en": "📋 RAM: {used}/{total}", "uz": "📋 RAM: {used}/{total}", "ru": "📋 ОЗУ: {used}/{total}",
        "zh": "📋 内存：{used}/{total}", "fa": "📋 رم: {used}/{total}",
    },
    "server_online": {
        "en": "🌐 Online Clients: {v}", "uz": "🌐 Onlayn Mijozlar: {v}", "ru": "🌐 Онлайн: {v}",
        "zh": "🌐 在线客户端：{v}", "fa": "🌐 کلاینت‌های آنلاین: {v}",
    },
    "server_tcp": {
        "en": "🔹 TCP: {v}", "uz": "🔹 TCP: {v}", "ru": "🔹 TCP: {v}",
        "zh": "🔹 TCP：{v}", "fa": "🔹 TCP: {v}",
    },
    "server_udp": {
        "en": "🔸 UDP: {v}", "uz": "🔸 UDP: {v}", "ru": "🔸 UDP: {v}",
        "zh": "🔸 UDP：{v}", "fa": "🔸 UDP: {v}",
    },
    "server_traffic": {
        "en": "🚦 Traffic: {total} (↑{up},↓{down})", "uz": "🚦 Traffic: {total} (↑{up},↓{down})",
        "ru": "🚦 Трафик: {total} (↑{up},↓{down})", "zh": "🚦 流量：{total}（↑{up}，↓{down}）",
        "fa": "🚦 ترافیک: {total} (↑{up},↓{down})",
    },
    "server_status_line": {
        "en": "ℹ️ Status: {v}", "uz": "ℹ️ Holat: {v}", "ru": "ℹ️ Состояние: {v}",
        "zh": "ℹ️ 状态：{v}", "fa": "ℹ️ وضعیت: {v}",
    },
    "refreshed_on": {
        "en": "📋🔄 Refreshed On: {v}", "uz": "📋🔄 Yangilangan: {v}", "ru": "📋🔄 Обновлено: {v}",
        "zh": "📋🔄 刷新时间：{v}", "fa": "📋🔄 بروزرسانی در: {v}",
    },
    # ── Online ───────────────────────────────────────────────────────────────
    "online_title": {
        "en": "🟢 <b>Online clients</b> — {count} total",
        "uz": "🟢 <b>Onlayn mijozlar</b> — jami {count}",
        "ru": "🟢 <b>Онлайн клиенты</b> — всего {count}",
        "zh": "🟢 <b>在线客户端</b> — 共 {count}",
        "fa": "🟢 <b>کلاینت‌های آنلاین</b> — {count} در مجموع",
    },
    "online_showing_first": {
        "en": "\n(showing first 60)", "uz": "\n(dastlabki 60 ta ko'rsatilmoqda)",
        "ru": "\n(показаны первые 60)", "zh": "\n（显示前60个）",
        "fa": "\n(نمایش 60 اول)",
    },
    "online_empty": {
        "en": "🟢 <b>Online clients</b>\n\nNo clients are online right now.",
        "uz": "🟢 <b>Onlayn mijozlar</b>\n\nHozirda hech qanday mijoz onlayn emas.",
        "ru": "🟢 <b>Онлайн клиенты</b>\n\nСейчас нет онлайн-клиентов.",
        "zh": "🟢 <b>在线客户端</b>\n\n目前没有客户端在线。",
        "fa": "🟢 <b>کلاینت‌های آنلاین</b>\n\nهیچ کلاینتی در حال حاضر آنلاین نیست.",
    },
    # ── Inbounds ─────────────────────────────────────────────────────────────
    "inbounds_empty": {
        "en": "No inbounds configured.", "uz": "Hech qanday inbound sozlanmagan.",
        "ru": "Нет настроенных входящих.", "zh": "未配置入站。", "fa": "هیچ اینباندی تنظیم نشده است.",
    },
    "inbound_name": {
        "en": "📍 Inbound: {v}", "uz": "📍 Inbound: {v}", "ru": "📍 Входящий: {v}",
        "zh": "📍 入站：{v}", "fa": "📍 اینباند: {v}",
    },
    "inbound_port": {
        "en": "🔌 Port: {v}", "uz": "🔌 Port: {v}", "ru": "🔌 Порт: {v}",
        "zh": "🔌 端口：{v}", "fa": "🔌 پورت: {v}",
    },
    "inbound_traffic": {
        "en": "🚦 Traffic: {total} (↑{up},↓{down})",
        "uz": "🚦 Traffic: {total} (↑{up},↓{down})",
        "ru": "🚦 Трафик: {total} (↑{up},↓{down})",
        "zh": "🚦 流量：{total}（↑{up}，↓{down}）",
        "fa": "🚦 ترافیک: {total} (↑{up},↓{down})",
    },
    "inbound_clients": {
        "en": "👥 Clients: {v}", "uz": "👥 Mijozlar: {v}", "ru": "👥 Клиентов: {v}",
        "zh": "👥 客户端：{v}", "fa": "👥 کلاینت‌ها: {v}",
    },
    "inbound_expire": {
        "en": "📅 Expire Date: {v}", "uz": "📅 Muddati: {v}", "ru": "📅 Срок действия: {v}",
        "zh": "📅 到期日期：{v}", "fa": "📅 تاریخ انقضا: {v}",
    },
    # ── Backup ───────────────────────────────────────────────────────────────
    "backup_sending": {
        "en": "Sending backup…", "uz": "Zaxira yuborilmoqda…", "ru": "Отправка резервной копии…",
        "zh": "正在发送备份…", "fa": "در حال ارسال پشتیبان…",
    },
    "backup_done": {
        "en": "💾 Backup dispatched to the panel's configured Telegram admins.",
        "uz": "💾 Zaxira panel Telegram adminlariga yuborildi.",
        "ru": "💾 Резервная копия отправлена настроенным Telegram-администраторам.",
        "zh": "💾 备份已发送到面板配置的 Telegram 管理员。",
        "fa": "💾 پشتیبان برای مدیران تلگرام پیکربندی‌شده در پنل ارسال شد.",
    },
    # ── Cleanup ──────────────────────────────────────────────────────────────
    "cleanup_cleaning": {
        "en": "Cleaning up…", "uz": "Tozalanmoqda…", "ru": "Очистка…",
        "zh": "正在清理…", "fa": "در حال پاکسازی…",
    },
    "cleanup_done": {
        "en": "🧹 Removed depleted/expired clients: <b>{count}</b>.",
        "uz": "🧹 O'chirilgan mijozlar: <b>{count}</b>.",
        "ru": "🧹 Удалено истощённых/истёкших клиентов: <b>{count}</b>.",
        "zh": "🧹 已删除耗尽/过期客户端：<b>{count}</b>。",
        "fa": "🧹 کلاینت‌های تمام‌شده/منقضی‌شده حذف شدند: <b>{count}</b>.",
    },
    # ── Deplete soon ─────────────────────────────────────────────────────────
    "deplete_title": {
        "en": "⚠️ <b>Depleting soon</b>\n",
        "uz": "⚠️ <b>Tez tugaydi</b>\n",
        "ru": "⚠️ <b>Скоро заканчивается</b>\n",
        "zh": "⚠️ <b>即将耗尽</b>\n",
        "fa": "⚠️ <b>به زودی تمام می‌شود</b>\n",
    },
    "deplete_disabled_inbounds": {
        "en": "Disabled inbounds: <b>{v}</b>",
        "uz": "O'chirilgan inboundlar: <b>{v}</b>",
        "ru": "Отключённые входящие: <b>{v}</b>",
        "zh": "已禁用入站：<b>{v}</b>",
        "fa": "اینباندهای غیرفعال: <b>{v}</b>",
    },
    "deplete_disabled_clients": {
        "en": "Disabled clients: <b>{v}</b>",
        "uz": "O'chirilgan mijozlar: <b>{v}</b>",
        "ru": "Отключённые клиенты: <b>{v}</b>",
        "zh": "已禁用客户端：<b>{v}</b>",
        "fa": "کلاینت‌های غیرفعال: <b>{v}</b>",
    },
    "deplete_inbounds_header": {
        "en": "📦 <b>Inbounds near limit:</b>",
        "uz": "📦 <b>Chegaraga yaqin inboundlar:</b>",
        "ru": "📦 <b>Входящие у предела:</b>",
        "zh": "📦 <b>接近限制的入站：</b>",
        "fa": "📦 <b>اینباندهای نزدیک به محدودیت:</b>",
    },
    "deplete_clients_header": {
        "en": "👥 <b>Clients near limit:</b>",
        "uz": "👥 <b>Chegaraga yaqin mijozlar:</b>",
        "ru": "👥 <b>Клиенты у предела:</b>",
        "zh": "👥 <b>接近限制的客户端：</b>",
        "fa": "👥 <b>کلاینت‌های نزدیک به محدودیت:</b>",
    },
    "deplete_none": {
        "en": "✅ No inbounds or clients are close to their limits.",
        "uz": "✅ Hech qanday inbound yoki mijoz chegaraga yaqin emas.",
        "ru": "✅ Нет входящих или клиентов у предела.",
        "zh": "✅ 没有入站或客户端接近其限制。",
        "fa": "✅ هیچ اینباند یا کلاینتی به محدودیت خود نزدیک نیست.",
    },
    # ── Reset all ─────────────────────────────────────────────────────────────
    "reset_all_confirm": {
        "en": (
            "⚠️ <b>Reset ALL client traffic?</b>\n\n"
            "This will zero the up/down counters for every client on the panel. "
            "This action cannot be undone."
        ),
        "uz": (
            "⚠️ <b>BARCHA mijoz trafikini tiklash?</b>\n\n"
            "Bu paneldagi har bir mijozning hisoblagichlarini nolga kamaytiradi. "
            "Bu amalni qaytarib bo'lmaydi."
        ),
        "ru": (
            "⚠️ <b>Сбросить весь трафик клиентов?</b>\n\n"
            "Это обнулит счётчики для каждого клиента на панели. "
            "Действие нельзя отменить."
        ),
        "zh": (
            "⚠️ <b>重置所有客户端流量？</b>\n\n"
            "这将清零面板上每个客户端的上/下行计数器。"
            "此操作无法撤销。"
        ),
        "fa": (
            "⚠️ <b>بازنشانی ترافیک همه کلاینت‌ها؟</b>\n\n"
            "این کار شمارنده‌های هر کلاینت در پنل را به صفر می‌رساند. "
            "این عملیات قابل برگشت نیست."
        ),
    },
    "reset_all_done": {
        "en": "✅ Traffic reset for all clients.",
        "uz": "✅ Barcha mijozlar uchun trafik tiklandi.",
        "ru": "✅ Трафик сброшен для всех клиентов.",
        "zh": "✅ 已重置所有客户端的流量。",
        "fa": "✅ ترافیک برای همه کلاینت‌ها بازنشانی شد.",
    },
    "reset_all_resetting": {
        "en": "Resetting…", "uz": "Tiklanmoqda…", "ru": "Сброс…",
        "zh": "正在重置…", "fa": "در حال بازنشانی…",
    },
    # ── Sorted report ────────────────────────────────────────────────────────
    "sorted_title": {
        "en": "📊 <b>Clients by traffic used</b>\n",
        "uz": "📊 <b>Foydalanilgan trafik bo'yicha mijozlar</b>\n",
        "ru": "📊 <b>Клиенты по использованному трафику</b>\n",
        "zh": "📊 <b>按流量使用排序的客户端</b>\n",
        "fa": "📊 <b>کلاینت‌ها بر اساس ترافیک مصرف‌شده</b>\n",
    },
    "sorted_more": {
        "en": "\n… and {count} more clients.",
        "uz": "\n… va yana {count} ta mijoz.",
        "ru": "\n… и ещё {count} клиентов.",
        "zh": "\n… 还有 {count} 个客户端。",
        "fa": "\n… و {count} کلاینت دیگر.",
    },
    "sorted_empty": {
        "en": "No clients found.", "uz": "Mijozlar topilmadi.", "ru": "Клиентов не найдено.",
        "zh": "未找到客户端。", "fa": "هیچ کلاینتی یافت نشد.",
    },
    # ── Commands ─────────────────────────────────────────────────────────────
    "commands_text": {
        "en": (
            "📋 <b>Admin commands</b>\n\n"
            "/start — open the main menu\n"
            "/find &lt;email&gt; — jump to a client by email\n"
            "/cancel — abort the current multi-step action\n\n"
            "Everything else is driven by the inline buttons."
        ),
        "uz": (
            "📋 <b>Admin buyruqlari</b>\n\n"
            "/start — asosiy menyuni ochish\n"
            "/find &lt;email&gt; — email bo'yicha mijozga o'tish\n"
            "/cancel — joriy amalni bekor qilish\n\n"
            "Qolganlar inline tugmalar orqali boshqariladi."
        ),
        "ru": (
            "📋 <b>Команды администратора</b>\n\n"
            "/start — открыть главное меню\n"
            "/find &lt;email&gt; — перейти к клиенту по email\n"
            "/cancel — прервать текущее действие\n\n"
            "Всё остальное управляется кнопками."
        ),
        "zh": (
            "📋 <b>管理员命令</b>\n\n"
            "/start — 打开主菜单\n"
            "/find &lt;email&gt; — 通过邮件直接跳转到客户端\n"
            "/cancel — 中止当前操作\n\n"
            "其余功能通过内联按钮操作。"
        ),
        "fa": (
            "📋 <b>دستورات مدیر</b>\n\n"
            "/start — باز کردن منوی اصلی\n"
            "/find &lt;email&gt; — رفتن به کلاینت با ایمیل\n"
            "/cancel — لغو عملیات جاری\n\n"
            "بقیه با دکمه‌های اینلاین مدیریت می‌شود."
        ),
    },
    # ── Restart Xray ─────────────────────────────────────────────────────────
    "restart_restarting": {
        "en": "Restarting Xray…", "uz": "Xray qayta ishga tushirilmoqda…",
        "ru": "Перезапуск Xray…", "zh": "正在重启Xray…", "fa": "در حال راه‌اندازی مجدد Xray…",
    },
    "restart_done": {
        "en": "⚡ Xray service restarted successfully.",
        "uz": "⚡ Xray xizmati muvaffaqiyatli qayta ishga tushirildi.",
        "ru": "⚡ Сервис Xray успешно перезапущен.",
        "zh": "⚡ Xray服务已成功重启。",
        "fa": "⚡ سرویس Xray با موفقیت راه‌اندازی مجدد شد.",
    },
    # ── Client list ──────────────────────────────────────────────────────────
    "clients_filter_prompt": {
        "en": "👥 <b>Clients</b> — pick an inbound to filter, or view all:",
        "uz": "👥 <b>Mijozlar</b> — filtr uchun inbound tanlang yoki hammasini ko'ring:",
        "ru": "👥 <b>Клиенты</b> — выберите входящий для фильтрации или посмотрите всех:",
        "zh": "👥 <b>客户端</b> — 选择入站过滤，或查看所有：",
        "fa": "👥 <b>کلاینت‌ها</b> — یک اینباند برای فیلتر انتخاب کنید، یا همه را ببینید:",
    },
    "clients_title": {
        "en": "👥 <b>Clients</b>{filter} — {count} total",
        "uz": "👥 <b>Mijozlar</b>{filter} — jami {count}",
        "ru": "👥 <b>Клиенты</b>{filter} — всего {count}",
        "zh": "👥 <b>客户端</b>{filter} — 共 {count}",
        "fa": "👥 <b>کلاینت‌ها</b>{filter} — {count} در مجموع",
    },
    "clients_filter_label": {
        "en": " · inbound #{v}", "uz": " · inbound #{v}", "ru": " · входящий #{v}",
        "zh": " · 入站 #{v}", "fa": " · اینباند #{v}",
    },
    # ── Client card fields ───────────────────────────────────────────────────
    "card_email": {
        "en": "📧 Email: {v}", "uz": "📧 Email: {v}", "ru": "📧 Email: {v}",
        "zh": "📧 邮件：{v}", "fa": "📧 ایمیل: {v}",
    },
    "card_inbounds": {
        "en": "🔗 Inbounds: {v}", "uz": "🔗 Inboundlar: {v}", "ru": "🔗 Входящие: {v}",
        "zh": "🔗 入站：{v}", "fa": "🔗 اینباندها: {v}",
    },
    "card_enabled": {
        "en": "🚨 Enabled: {v}", "uz": "🚨 Yoqilgan: {v}", "ru": "🚨 Включён: {v}",
        "zh": "🚨 已启用：{v}", "fa": "🚨 فعال: {v}",
    },
    "card_connection": {
        "en": "🌐 Connection status: {v}", "uz": "🌐 Ulanish holati: {v}",
        "ru": "🌐 Статус соединения: {v}", "zh": "🌐 连接状态：{v}", "fa": "🌐 وضعیت اتصال: {v}",
    },
    "card_last_online": {
        "en": "🔙 Last online: {v}", "uz": "🔙 Oxirgi online: {v}", "ru": "🔙 Последний раз онлайн: {v}",
        "zh": "🔙 最后在线：{v}", "fa": "🔙 آخرین آنلاین: {v}",
    },
    "card_active": {
        "en": "💡 Active: {v}", "uz": "💡 Faol: {v}", "ru": "💡 Активен: {v}",
        "zh": "💡 活跃：{v}", "fa": "💡 فعال: {v}",
    },
    "card_expire": {
        "en": "📅 Expire Date: {v}", "uz": "📅 Muddati: {v}", "ru": "📅 Срок действия: {v}",
        "zh": "📅 到期日期：{v}", "fa": "📅 تاریخ انقضا: {v}",
    },
    "card_upload": {
        "en": "🔼 Upload: ↑{v}", "uz": "🔼 Yuklash: ↑{v}", "ru": "🔼 Загрузка: ↑{v}",
        "zh": "🔼 上传：↑{v}", "fa": "🔼 آپلود: ↑{v}",
    },
    "card_download": {
        "en": "🔽 Download: ↓{v}", "uz": "🔽 Yuklab olish: ↓{v}", "ru": "🔽 Скачивание: ↓{v}",
        "zh": "🔽 下载：↓{v}", "fa": "🔽 دانلود: ↓{v}",
    },
    "card_total": {
        "en": "📊 Total: ↑↓{used} / {quota}", "uz": "📊 Jami: ↑↓{used} / {quota}",
        "ru": "📊 Итого: ↑↓{used} / {quota}", "zh": "📊 总计：↑↓{used} / {quota}",
        "fa": "📊 مجموع: ↑↓{used} / {quota}",
    },
    "mark_yes": {
        "en": "✅ Yes", "uz": "✅ Ha", "ru": "✅ Да", "zh": "✅ 是", "fa": "✅ بله",
    },
    "mark_no": {
        "en": "❌ No", "uz": "❌ Yo'q", "ru": "❌ Нет", "zh": "❌ 否", "fa": "❌ خیر",
    },
    "mark_online": {
        "en": "🟢 Online", "uz": "🟢 Onlayn", "ru": "🟢 Онлайн", "zh": "🟢 在线", "fa": "🟢 آنلاین",
    },
    "mark_offline": {
        "en": "🔴 Offline", "uz": "🔴 Oflayn", "ru": "🔴 Оффлайн", "zh": "🔴 离线", "fa": "🔴 آفلاین",
    },
    # ── Find client ──────────────────────────────────────────────────────────
    "find_prompt": {
        "en": "🔎 Send an email (or partial email) to search.",
        "uz": "🔎 Qidirish uchun email (yoki qisman email) yuboring.",
        "ru": "🔎 Отправьте email (или часть email) для поиска.",
        "zh": "🔎 发送邮件（或邮件的一部分）进行搜索。",
        "fa": "🔎 برای جستجو یک ایمیل (یا بخشی از ایمیل) بفرستید.",
    },
    "find_cmd_usage": {
        "en": "Usage: <code>/find &lt;email&gt;</code>",
        "uz": "Foydalanish: <code>/find &lt;email&gt;</code>",
        "ru": "Использование: <code>/find &lt;email&gt;</code>",
        "zh": "用法：<code>/find &lt;email&gt;</code>",
        "fa": "استفاده: <code>/find &lt;email&gt;</code>",
    },
    "find_no_match": {
        "en": "No clients matching <code>{q}</code>.",
        "uz": "<code>{q}</code> ga mos mijozlar topilmadi.",
        "ru": "Не найдено клиентов, соответствующих <code>{q}</code>.",
        "zh": "没有找到与 <code>{q}</code> 匹配的客户端。",
        "fa": "هیچ کلاینتی مطابق با <code>{q}</code> یافت نشد.",
    },
    "find_many_matches": {
        "en": "🔎 <b>{count} matches</b> for <code>{q}</code> — refine your search.",
        "uz": "🔎 <code>{q}</code> uchun <b>{count} ta mos</b> — qidiruvni aniqlashtiring.",
        "ru": "🔎 <b>{count} совпадений</b> для <code>{q}</code> — уточните поиск.",
        "zh": "🔎 <b>{count} 个匹配</b> <code>{q}</code> — 请细化搜索。",
        "fa": "🔎 <b>{count} تطابق</b> برای <code>{q}</code> — جستجو را دقیق‌تر کنید.",
    },
    "find_pick_result": {
        "en": "🔎 <b>{count} matches</b> for <code>{q}</code>:",
        "uz": "🔎 <code>{q}</code> uchun <b>{count} ta mos</b>:",
        "ru": "🔎 <b>{count} совпадений</b> для <code>{q}</code>:",
        "zh": "🔎 <b>{count} 个匹配</b> <code>{q}</code>：",
        "fa": "🔎 <b>{count} تطابق</b> برای <code>{q}</code>:",
    },
    "client_not_found": {
        "en": "Client <code>{email}</code> not found.",
        "uz": "Mijoz <code>{email}</code> topilmadi.",
        "ru": "Клиент <code>{email}</code> не найден.",
        "zh": "未找到客户端 <code>{email}</code>。",
        "fa": "کلاینت <code>{email}</code> یافت نشد.",
    },
    # ── Client actions ───────────────────────────────────────────────────────
    "traffic_reset_done": {
        "en": "Traffic reset ✅", "uz": "Trafik tiklandi ✅", "ru": "Трафик сброшен ✅",
        "zh": "流量已重置 ✅", "fa": "ترافیک بازنشانی شد ✅",
    },
    "updated_ok": {
        "en": "Updated ✅", "uz": "Yangilandi ✅", "ru": "Обновлено ✅",
        "zh": "已更新 ✅", "fa": "بروزرسانی شد ✅",
    },
    "not_found_alert": {
        "en": "Not found", "uz": "Topilmadi", "ru": "Не найдено", "zh": "未找到", "fa": "یافت نشد",
    },
    "no_links": {
        "en": "No URL-style configs for this client (protocol may not support links).",
        "uz": "Bu mijoz uchun URL-formatdagi konfiglar yo'q.",
        "ru": "Нет URL-конфигов для этого клиента (протокол может не поддерживать ссылки).",
        "zh": "此客户端没有URL格式的配置（协议可能不支持链接）。",
        "fa": "هیچ پیکربندی URL برای این کلاینت وجود ندارد (پروتکل ممکن است از لینک‌ها پشتیبانی نکند).",
    },
    "links_title": {
        "en": "🔗 <b>{email}</b>", "uz": "🔗 <b>{email}</b>", "ru": "🔗 <b>{email}</b>",
        "zh": "🔗 <b>{email}</b>", "fa": "🔗 <b>{email}</b>",
    },
    "ips_title": {
        "en": "🌐 <b>{email}</b>", "uz": "🌐 <b>{email}</b>", "ru": "🌐 <b>{email}</b>",
        "zh": "🌐 <b>{email}</b>", "fa": "🌐 <b>{email}</b>",
    },
    "ip_list_cleared": {
        "en": "IP list cleared ✅", "uz": "IP ro'yxati tozalandi ✅", "ru": "Список IP очищен ✅",
        "zh": "IP列表已清除 ✅", "fa": "لیست IP پاک شد ✅",
    },
    "no_sub_url": {
        "en": (
            "⚠️ No subscription URL available.\n"
            "Set <code>SUB_BASE_URL</code> in your bot config to enable this."
        ),
        "uz": (
            "⚠️ Obuna URL mavjud emas.\n"
            "Yoqish uchun bot config'da <code>SUB_BASE_URL</code> o'rnating."
        ),
        "ru": (
            "⚠️ URL подписки недоступен.\n"
            "Укажите <code>SUB_BASE_URL</code> в конфиге бота, чтобы включить его."
        ),
        "zh": (
            "⚠️ 没有可用的订阅URL。\n"
            "在机器人配置中设置 <code>SUB_BASE_URL</code> 以启用此功能。"
        ),
        "fa": (
            "⚠️ URL اشتراک در دسترس نیست.\n"
            "برای فعال کردن، <code>SUB_BASE_URL</code> را در پیکربندی ربات تنظیم کنید."
        ),
    },
    "sublinks_title": {
        "en": "🔗 <b>Sub links · {email}</b>", "uz": "🔗 <b>Sub linklar · {email}</b>",
        "ru": "🔗 <b>Ссылки подписки · {email}</b>", "zh": "🔗 <b>订阅链接 · {email}</b>",
        "fa": "🔗 <b>لینک‌های اشتراک · {email}</b>",
    },
    "sub_url_label": {
        "en": "<b>Subscription URL</b>", "uz": "<b>Obuna URL</b>", "ru": "<b>URL подписки</b>",
        "zh": "<b>订阅URL</b>", "fa": "<b>URL اشتراک</b>",
    },
    "qr_generating": {
        "en": "Generating QR…", "uz": "QR yaratilmoqda…", "ru": "Генерация QR…",
        "zh": "正在生成QR码…", "fa": "در حال تولید QR…",
    },
    "qr_no_data": {
        "en": "No QR data available (no sub URL or links for this client).",
        "uz": "QR ma'lumot yo'q (bu mijoz uchun sub URL yoki linklar yo'q).",
        "ru": "Нет данных для QR (нет sub URL или ссылок для этого клиента).",
        "zh": "没有QR数据（此客户端没有订阅URL或链接）。",
        "fa": "هیچ داده QR در دسترس نیست (هیچ URL اشتراک یا لینکی برای این کلاینت وجود ندارد).",
    },
    "qr_done": {
        "en": "✅ Done.", "uz": "✅ Tayyor.", "ru": "✅ Готово.", "zh": "✅ 完成。", "fa": "✅ انجام شد.",
    },
    "qr_sub_caption": {
        "en": "📷 Sub URL QR · <code>{email}</code>",
        "uz": "📷 Sub URL QR · <code>{email}</code>",
        "ru": "📷 QR URL подписки · <code>{email}</code>",
        "zh": "📷 订阅URL二维码 · <code>{email}</code>",
        "fa": "📷 QR اشتراک · <code>{email}</code>",
    },
    "qr_config_caption": {
        "en": "📷 Config #{n} · <code>{email}</code>",
        "uz": "📷 Konfiguratsiya #{n} · <code>{email}</code>",
        "ru": "📷 Конфиг #{n} · <code>{email}</code>",
        "zh": "📷 配置 #{n} · <code>{email}</code>",
        "fa": "📷 پیکربندی #{n} · <code>{email}</code>",
    },
    # ── Delete ───────────────────────────────────────────────────────────────
    "del_confirm": {
        "en": "🗑 Delete <code>{email}</code>? This cannot be undone.",
        "uz": "🗑 <code>{email}</code>ni o'chirish? Buni qaytarib bo'lmaydi.",
        "ru": "🗑 Удалить <code>{email}</code>? Это нельзя отменить.",
        "zh": "🗑 删除 <code>{email}</code>？此操作无法撤销。",
        "fa": "🗑 حذف <code>{email}</code>؟ این عملیات قابل برگشت نیست.",
    },
    "del_done": {
        "en": "🗑 Deleted <code>{email}</code>.",
        "uz": "🗑 <code>{email}</code> o'chirildi.",
        "ru": "🗑 Удалён <code>{email}</code>.",
        "zh": "🗑 已删除 <code>{email}</code>。",
        "fa": "🗑 <code>{email}</code> حذف شد.",
    },
    "deleted_ok": {
        "en": "Deleted ✅", "uz": "O'chirildi ✅", "ru": "Удалено ✅", "zh": "已删除 ✅", "fa": "حذف شد ✅",
    },
    # ── Set TG ID ────────────────────────────────────────────────────────────
    "set_tgid_prompt": {
        "en": (
            "👤 Assign a Telegram user to <code>{email}</code>.\n\n"
            "Tap <b>Pick a Telegram user</b> to choose from your contacts, "
            "or type a numeric Telegram ID directly."
        ),
        "uz": (
            "👤 <code>{email}</code> ga Telegram foydalanuvchi biriktirish.\n\n"
            "<b>Telegram foydalanuvchi tanlash</b>ni bosing yoki raqamli Telegram ID kiriting."
        ),
        "ru": (
            "👤 Назначить Telegram-пользователя для <code>{email}</code>.\n\n"
            "Нажмите <b>Выбрать пользователя</b> или введите числовой Telegram ID."
        ),
        "zh": (
            "👤 为 <code>{email}</code> 分配Telegram用户。\n\n"
            "点击 <b>选择Telegram用户</b> 从联系人中选择，或直接输入数字Telegram ID。"
        ),
        "fa": (
            "👤 تخصیص یک کاربر تلگرام به <code>{email}</code>.\n\n"
            "برای انتخاب از مخاطبین روی <b>انتخاب کاربر تلگرام</b> ضربه بزنید، "
            "یا مستقیماً یک شناسه تلگرام عددی وارد کنید."
        ),
    },
    "tgid_no_user": {
        "en": "No user selected.", "uz": "Foydalanuvchi tanlanmadi.", "ru": "Пользователь не выбран.",
        "zh": "未选择用户。", "fa": "هیچ کاربری انتخاب نشد.",
    },
    "tgid_invalid": {
        "en": "Please send a <b>numeric</b> Telegram user ID, or use the picker button.",
        "uz": "Iltimos, <b>raqamli</b> Telegram foydalanuvchi ID yuboring yoki tanlash tugmasidan foydalaning.",
        "ru": "Пожалуйста, отправьте <b>числовой</b> Telegram ID или используйте кнопку выбора.",
        "zh": "请发送<b>数字</b>Telegram用户ID，或使用选择按钮。",
        "fa": "لطفاً یک شناسه کاربری تلگرام <b>عددی</b> بفرستید، یا از دکمه انتخاب استفاده کنید.",
    },
    "tgid_done": {
        "en": "✅ TG ID <code>{tg_id}</code> assigned to <code>{email}</code>.",
        "uz": "✅ TG ID <code>{tg_id}</code> <code>{email}</code> ga biriktirildi.",
        "ru": "✅ TG ID <code>{tg_id}</code> назначен <code>{email}</code>.",
        "zh": "✅ TG ID <code>{tg_id}</code> 已分配给 <code>{email}</code>。",
        "fa": "✅ شناسه تلگرام <code>{tg_id}</code> به <code>{email}</code> اختصاص یافت.",
    },
    # ── Extend ───────────────────────────────────────────────────────────────
    "extend_prompt": {
        "en": "➕ <b>Extend</b> <code>{email}</code> — pick days to add:",
        "uz": "➕ <b>Uzaytirish</b> <code>{email}</code> — qo'shish uchun kunlarni tanlang:",
        "ru": "➕ <b>Продлить</b> <code>{email}</code> — выберите количество дней:",
        "zh": "➕ <b>延长</b> <code>{email}</code> — 选择要添加的天数：",
        "fa": "➕ <b>افزایش</b> <code>{email}</code> — روزهای افزودنی را انتخاب کنید:",
    },
    "extend_custom_prompt": {
        "en": "➕ How many days to add to <code>{email}</code>?\nSend a number (negative to reduce).",
        "uz": "➕ <code>{email}</code> ga necha kun qo'shish?\nRaqam yuboring (kamaytirishni manfiy qiling).",
        "ru": "➕ Сколько дней добавить к <code>{email}</code>?\nОтправьте число (отрицательное для уменьшения).",
        "zh": "➕ 要为 <code>{email}</code> 添加多少天？\n发送一个数字（负数表示减少）。",
        "fa": "➕ چند روز به <code>{email}</code> اضافه شود؟\nیک عدد بفرستید (منفی برای کاهش).",
    },
    "extend_invalid": {
        "en": "Please send a whole number, e.g. <code>30</code>.",
        "uz": "Iltimos, butun son yuboring, masalan <code>30</code>.",
        "ru": "Пожалуйста, отправьте целое число, например <code>30</code>.",
        "zh": "请发送整数，例如 <code>30</code>。",
        "fa": "لطفاً یک عدد صحیح بفرستید، مثلاً <code>30</code>.",
    },
    "extend_remove_expiry_btn": {
        "en": "∞ Remove expiry", "uz": "∞ Muddatni olib tashlash", "ru": "∞ Убрать срок",
        "zh": "∞ 移除到期", "fa": "∞ حذف انقضا",
    },
    "no_expiry_btn": {
        "en": "∞ No expiry", "uz": "∞ Muddatsiz", "ru": "∞ Без срока",
        "zh": "∞ 无到期", "fa": "∞ بدون انقضا",
    },
    # ── Set quota ────────────────────────────────────────────────────────────
    "quota_prompt": {
        "en": "💽 Traffic quota for <code>{email}</code>:",
        "uz": "💽 <code>{email}</code> uchun trafik kvotasi:",
        "ru": "💽 Квота трафика для <code>{email}</code>:",
        "zh": "💽 <code>{email}</code> 的流量配额：",
        "fa": "💽 سهمیه ترافیک برای <code>{email}</code>:",
    },
    "quota_custom_prompt": {
        "en": "💽 Send quota in <b>GB</b> (0 = unlimited):",
        "uz": "💽 Kvotani <b>GB</b> da yuboring (0 = cheksiz):",
        "ru": "💽 Отправьте квоту в <b>ГБ</b> (0 = без лимита):",
        "zh": "💽 以<b>GB</b>发送配额（0 = 无限制）：",
        "fa": "💽 سهمیه را به <b>GB</b> بفرستید (0 = نامحدود):",
    },
    "quota_custom_prompt_wizard": {
        "en": "💽 Send quota in <b>GB</b> (0 = unlimited).\nDefault: <code>{default}</code>",
        "uz": "💽 Kvotani <b>GB</b> da yuboring (0 = cheksiz).\nDefault: <code>{default}</code>",
        "ru": "💽 Отправьте квоту в <b>ГБ</b> (0 = без лимита).\nПо умолчанию: <code>{default}</code>",
        "zh": "💽 以<b>GB</b>发送配额（0 = 无限制）。\n默认值：<code>{default}</code>",
        "fa": "💽 سهمیه را به <b>GB</b> بفرستید (0 = نامحدود).\nپیش‌فرض: <code>{default}</code>",
    },
    "quota_invalid": {
        "en": "Send a number, e.g. <code>50</code> (or 0 for unlimited).",
        "uz": "Raqam yuboring, masalan <code>50</code> (yoki cheksiz uchun 0).",
        "ru": "Отправьте число, например <code>50</code> (или 0 для безлимита).",
        "zh": "发送一个数字，例如 <code>50</code>（或0表示无限制）。",
        "fa": "یک عدد بفرستید، مثلاً <code>50</code> (یا 0 برای نامحدود).",
    },
    # ── Set expiry ───────────────────────────────────────────────────────────
    "expiry_prompt": {
        "en": "📅 Expiry for <code>{email}</code> — pick days from today:",
        "uz": "📅 <code>{email}</code> uchun muddati — bugundan kunlarni tanlang:",
        "ru": "📅 Срок для <code>{email}</code> — выберите дни с сегодня:",
        "zh": "📅 <code>{email}</code> 的到期日 — 从今天起选择天数：",
        "fa": "📅 انقضای <code>{email}</code> — روزها از امروز را انتخاب کنید:",
    },
    "expiry_custom_prompt": {
        "en": "📅 Send number of <b>days from now</b> (0 = no expiry, negative = days from first use):",
        "uz": "📅 <b>Bugundan kunlar</b> sonini yuboring (0 = muddatsiz, manfiy = birinchi foydalanishdan):",
        "ru": "📅 Отправьте количество <b>дней с сегодня</b> (0 = без срока, отрицательное = от первого использования):",
        "zh": "📅 发送<b>从今天起的天数</b>（0 = 无到期，负数 = 从首次使用起的天数）：",
        "fa": "📅 تعداد <b>روز از حالا</b> را بفرستید (0 = بدون انقضا، منفی = روز از اولین استفاده):",
    },
    "expiry_invalid": {
        "en": "Send a whole number, e.g. <code>30</code>.",
        "uz": "Butun son yuboring, masalan <code>30</code>.",
        "ru": "Отправьте целое число, например <code>30</code>.",
        "zh": "发送整数，例如 <code>30</code>。",
        "fa": "یک عدد صحیح بفرستید، مثلاً <code>30</code>.",
    },
    "days_custom_prompt_wizard": {
        "en": "📅 Send validity in <b>days</b> (0 = unlimited).\nDefault: <code>{default}</code>",
        "uz": "📅 Muddatni <b>kun</b>da yuboring (0 = cheksiz).\nDefault: <code>{default}</code>",
        "ru": "📅 Отправьте срок в <b>днях</b> (0 = без лимита).\nПо умолчанию: <code>{default}</code>",
        "zh": "📅 以<b>天</b>发送有效期（0 = 无限制）。\n默认值：<code>{default}</code>",
        "fa": "📅 اعتبار را به <b>روز</b> بفرستید (0 = نامحدود).\nپیش‌فرض: <code>{default}</code>",
    },
    # ── IP limit ─────────────────────────────────────────────────────────────
    "iplimit_prompt": {
        "en": "🔢 IP limit for <code>{email}</code>:",
        "uz": "🔢 <code>{email}</code> uchun IP cheklov:",
        "ru": "🔢 Лимит IP для <code>{email}</code>:",
        "zh": "🔢 <code>{email}</code> 的IP限制：",
        "fa": "🔢 محدودیت IP برای <code>{email}</code>:",
    },
    "iplimit_custom_prompt": {
        "en": "🔢 Send max simultaneous IPs (0 = unlimited):",
        "uz": "🔢 Maksimal bir vaqtdagi IP'lar sonini yuboring (0 = cheksiz):",
        "ru": "🔢 Отправьте максимум одновременных IP (0 = без лимита):",
        "zh": "🔢 发送最大同时IP数（0 = 无限制）：",
        "fa": "🔢 حداکثر IP‌های همزمان را بفرستید (0 = نامحدود):",
    },
    "iplimit_invalid": {
        "en": "Send a non-negative whole number, e.g. <code>3</code>.",
        "uz": "Manfiy bo'lmagan butun son yuboring, masalan <code>3</code>.",
        "ru": "Отправьте неотрицательное целое число, например <code>3</code>.",
        "zh": "发送非负整数，例如 <code>3</code>。",
        "fa": "یک عدد صحیح غیرمنفی بفرستید، مثلاً <code>3</code>.",
    },
    # ── Create wizard ─────────────────────────────────────────────────────────
    "create_inbounds_prompt": {
        "en": "➕ <b>New client</b>\nSelect one or more inbounds, then Continue.",
        "uz": "➕ <b>Yangi mijoz</b>\nBir yoki bir nechta inbound tanlang, so'ng Davom etish.",
        "ru": "➕ <b>Новый клиент</b>\nВыберите один или несколько входящих, затем Продолжить.",
        "zh": "➕ <b>新客户端</b>\n选择一个或多个入站，然后继续。",
        "fa": "➕ <b>کلاینت جدید</b>\nیک یا چند اینباند انتخاب کنید، سپس ادامه دهید.",
    },
    "create_email_prompt_default": {
        "en": "➕ <b>New client</b>\nSend the <b>email</b> (label) for the new client.",
        "uz": "➕ <b>Yangi mijoz</b>\nYangi mijoz uchun <b>email</b> (yorliq) yuboring.",
        "ru": "➕ <b>Новый клиент</b>\nОтправьте <b>email</b> (метку) для нового клиента.",
        "zh": "➕ <b>新客户端</b>\n发送新客户端的<b>邮件</b>（标签）。",
        "fa": "➕ <b>کلاینت جدید</b>\n<b>ایمیل</b> (برچسب) برای کلاینت جدید بفرستید.",
    },
    "create_email_prompt": {
        "en": "✏️ Send the <b>email</b> (label) for the new client.",
        "uz": "✏️ Yangi mijoz uchun <b>email</b> (yorliq) yuboring.",
        "ru": "✏️ Отправьте <b>email</b> (метку) для нового клиента.",
        "zh": "✏️ 发送新客户端的<b>邮件</b>（标签）。",
        "fa": "✏️ <b>ایمیل</b> (برچسب) برای کلاینت جدید بفرستید.",
    },
    "create_email_invalid": {
        "en": "Email must be a single token without spaces. Try again.",
        "uz": "Email bo'shliqsiz yagona so'z bo'lishi kerak. Qaytadan urinib ko'ring.",
        "ru": "Email должен быть одним словом без пробелов. Попробуйте снова.",
        "zh": "邮件必须是不含空格的单个标记。请重试。",
        "fa": "ایمیل باید یک توکن بدون فاصله باشد. دوباره امتحان کنید.",
    },
    "create_pick_at_least_one": {
        "en": "Pick at least one inbound.",
        "uz": "Kamida bitta inbound tanlang.",
        "ru": "Выберите хотя бы один входящий.",
        "zh": "至少选择一个入站。",
        "fa": "حداقل یک اینباند انتخاب کنید.",
    },
    "create_no_inbounds": {
        "en": "No inbounds available.", "uz": "Inboundlar mavjud emas.", "ru": "Нет доступных входящих.",
        "zh": "没有可用的入站。", "fa": "هیچ اینباندی موجود نیست.",
    },
    "create_validity_prompt": {
        "en": "📅 Validity — pick days from today:",
        "uz": "📅 Muddati — bugundan kunlarni tanlang:",
        "ru": "📅 Срок действия — выберите дни с сегодня:",
        "zh": "📅 有效期 — 从今天起选择天数：",
        "fa": "📅 اعتبار — روزها از امروز را انتخاب کنید:",
    },
    "create_confirm": {
        "en": (
            "🧾 <b>Confirm new client</b>\n\n"
            "Email: <code>{email}</code>\n"
            "Quota: <b>{quota}</b>\n"
            "Validity: <b>{days}</b>\n"
            "Inbounds: {inbounds}"
        ),
        "uz": (
            "🧾 <b>Yangi mijozni tasdiqlash</b>\n\n"
            "Email: <code>{email}</code>\n"
            "Kvota: <b>{quota}</b>\n"
            "Muddat: <b>{days}</b>\n"
            "Inboundlar: {inbounds}"
        ),
        "ru": (
            "🧾 <b>Подтвердить нового клиента</b>\n\n"
            "Email: <code>{email}</code>\n"
            "Квота: <b>{quota}</b>\n"
            "Срок: <b>{days}</b>\n"
            "Входящие: {inbounds}"
        ),
        "zh": (
            "🧾 <b>确认新客户端</b>\n\n"
            "邮件：<code>{email}</code>\n"
            "配额：<b>{quota}</b>\n"
            "有效期：<b>{days}</b>\n"
            "入站：{inbounds}"
        ),
        "fa": (
            "🧾 <b>تأیید کلاینت جدید</b>\n\n"
            "ایمیل: <code>{email}</code>\n"
            "سهمیه: <b>{quota}</b>\n"
            "اعتبار: <b>{days}</b>\n"
            "اینباندها: {inbounds}"
        ),
    },
    "created_ok": {
        "en": "Created ✅", "uz": "Yaratildi ✅", "ru": "Создан ✅", "zh": "已创建 ✅", "fa": "ایجاد شد ✅",
    },
    "create_done": {
        "en": "✅ Created <code>{email}</code>.",
        "uz": "✅ <code>{email}</code> yaratildi.",
        "ru": "✅ Создан <code>{email}</code>.",
        "zh": "✅ 已创建 <code>{email}</code>。",
        "fa": "✅ <code>{email}</code> ایجاد شد.",
    },
    "loading_inbounds": {
        "en": "Loading inbounds…", "uz": "Inboundlar yuklanmoqda…", "ru": "Загрузка входящих…",
        "zh": "正在加载入站…", "fa": "در حال بارگذاری اینباندها…",
    },
    # ── Client side ──────────────────────────────────────────────────────────
    "link_done": {
        "en": "✅ Linked to <code>{email}</code>.",
        "uz": "✅ <code>{email}</code> ga ulandi.",
        "ru": "✅ Привязан к <code>{email}</code>.",
        "zh": "✅ 已绑定到 <code>{email}</code>。",
        "fa": "✅ به <code>{email}</code> متصل شد.",
    },
    "link_not_found": {
        "en": "❌ Your Telegram ID is not assigned to any account yet. Contact your provider.",
        "uz": "❌ Telegram ID ingiz hali hech qanday hisobga biriktirilmagan. Provayderingiz bilan bog'laning.",
        "ru": "❌ Ваш Telegram ID ещё не привязан ни к одному аккаунту. Свяжитесь с провайдером.",
        "zh": "❌ 您的Telegram ID尚未分配给任何账户。请联系您的提供商。",
        "fa": "❌ شناسه تلگرام شما هنوز به هیچ حسابی اختصاص داده نشده است. با ارائه‌دهنده خود تماس بگیرید.",
    },
    "unlink_done": {
        "en": "🔌 Account unlinked.", "uz": "🔌 Hisob uzildi.", "ru": "🔌 Аккаунт отвязан.",
        "zh": "🔌 账户已取消绑定。", "fa": "🔌 حساب قطع اتصال شد.",
    },
    "account_no_link": {
        "en": "Link your account first.", "uz": "Avval hisobingizni ulang.", "ru": "Сначала привяжите аккаунт.",
        "zh": "请先绑定您的账户。", "fa": "ابتدا حساب خود را متصل کنید.",
    },
    "account_gone": {
        "en": "Your linked account no longer exists. Please re-link.",
        "uz": "Bog'langan hisobingiz endi mavjud emas. Qayta ulang.",
        "ru": "Ваш привязанный аккаунт больше не существует. Привяжите заново.",
        "zh": "您绑定的账户不再存在。请重新绑定。",
        "fa": "حساب متصل شما دیگر وجود ندارد. لطفاً مجدداً متصل شوید.",
    },
    "my_configs_title": {
        "en": "🔗 <b>Your configs</b>",
        "uz": "🔗 <b>Sizning konfiglaringiz</b>",
        "ru": "🔗 <b>Ваши конфиги</b>",
        "zh": "🔗 <b>您的配置</b>",
        "fa": "🔗 <b>پیکربندی‌های شما</b>",
    },
    "my_configs_no_links": {
        "en": "No config links are available for your account.",
        "uz": "Hisobingiz uchun hech qanday konfiguratsiya linki mavjud emas.",
        "ru": "Для вашего аккаунта нет конфигурационных ссылок.",
        "zh": "您的账户没有可用的配置链接。",
        "fa": "هیچ لینک پیکربندی برای حساب شما در دسترس نیست.",
    },
    "my_sub_label": {
        "en": "<b>Subscription</b>", "uz": "<b>Obuna</b>", "ru": "<b>Подписка</b>",
        "zh": "<b>订阅</b>", "fa": "<b>اشتراک</b>",
    },
    "my_qr_sub_caption": {
        "en": "📷 Your subscription QR code",
        "uz": "📷 Sizning obuna QR kodi",
        "ru": "📷 QR-код вашей подписки",
        "zh": "📷 您的订阅二维码",
        "fa": "📷 کد QR اشتراک شما",
    },
    "my_qr_config_caption": {
        "en": "📷 Config #{n}", "uz": "📷 Konfiguratsiya #{n}", "ru": "📷 Конфиг #{n}",
        "zh": "📷 配置 #{n}", "fa": "📷 پیکربندی #{n}",
    },
    "my_qr_no_data": {
        "en": (
            "No QR data available.\n"
            "Set <code>SUB_BASE_URL</code> in your bot config or ask your provider for links."
        ),
        "uz": (
            "QR ma'lumot yo'q.\n"
            "Bot config'da <code>SUB_BASE_URL</code> o'rnating yoki provayderingizdan linklar so'rang."
        ),
        "ru": (
            "Нет данных для QR.\n"
            "Укажите <code>SUB_BASE_URL</code> в конфиге бота или попросите провайдера ссылки."
        ),
        "zh": (
            "没有QR数据。\n"
            "在机器人配置中设置 <code>SUB_BASE_URL</code> 或向提供商索取链接。"
        ),
        "fa": (
            "داده QR در دسترس نیست.\n"
            "<code>SUB_BASE_URL</code> را در پیکربندی ربات تنظیم کنید یا از ارائه‌دهنده خود لینک بخواهید."
        ),
    },
    # ── Account card fields (client side) ─────────────────────────────────────
    "acc_email": {
        "en": "📧 Email: {v}", "uz": "📧 Email: {v}", "ru": "📧 Email: {v}",
        "zh": "📧 邮件：{v}", "fa": "📧 ایمیل: {v}",
    },
    "acc_inbounds": {
        "en": "🔗 Inbounds: {v}", "uz": "🔗 Inboundlar: {v}", "ru": "🔗 Входящие: {v}",
        "zh": "🔗 入站：{v}", "fa": "🔗 اینباندها: {v}",
    },
    "acc_expire": {
        "en": "📅 Expire Date: {v}", "uz": "📅 Muddati: {v}", "ru": "📅 Срок действия: {v}",
        "zh": "📅 到期日期：{v}", "fa": "📅 تاریخ انقضا: {v}",
    },
    "acc_upload": {
        "en": "🔼 Upload: ↑{v}", "uz": "🔼 Yuklash: ↑{v}", "ru": "🔼 Загрузка: ↑{v}",
        "zh": "🔼 上传：↑{v}", "fa": "🔼 آپلود: ↑{v}",
    },
    "acc_download": {
        "en": "🔽 Download: ↓{v}", "uz": "🔽 Yuklab olish: ↓{v}", "ru": "🔽 Скачивание: ↓{v}",
        "zh": "🔽 下载：↓{v}", "fa": "🔽 دانلود: ↓{v}",
    },
    "acc_total": {
        "en": "📊 Total: ↑↓{used} / {quota}", "uz": "📊 Jami: ↑↓{used} / {quota}",
        "ru": "📊 Итого: ↑↓{used} / {quota}", "zh": "📊 总计：↑↓{used} / {quota}",
        "fa": "📊 مجموع: ↑↓{used} / {quota}",
    },
    "acc_last_online": {
        "en": "🔙 Last online: {v}", "uz": "🔙 Oxirgi online: {v}", "ru": "🔙 Последний раз онлайн: {v}",
        "zh": "🔙 最后在线：{v}", "fa": "🔙 آخرین آنلاین: {v}",
    },
    # ── Periodic report ──────────────────────────────────────────────────────
    "report_title": {
        "en": "📊 <b>Periodic Report</b>", "uz": "📊 <b>Davriy Hisobot</b>",
        "ru": "📊 <b>Периодический отчёт</b>", "zh": "📊 <b>定期报告</b>", "fa": "📊 <b>گزارش دوره‌ای</b>",
    },
    "report_cpu": {
        "en": "🖥 CPU: {v}%", "uz": "🖥 CPU: {v}%", "ru": "🖥 ЦПУ: {v}%",
        "zh": "🖥 CPU：{v}%", "fa": "🖥 پردازنده: {v}%",
    },
    "report_ram": {
        "en": "💾 RAM: {v}", "uz": "💾 RAM: {v}", "ru": "💾 ОЗУ: {v}",
        "zh": "💾 内存：{v}", "fa": "💾 رم: {v}",
    },
    "report_disk": {
        "en": "💿 Disk: {v}", "uz": "💿 Disk: {v}", "ru": "💿 Диск: {v}",
        "zh": "💿 磁盘：{v}", "fa": "💿 دیسک: {v}",
    },
    "report_uptime": {
        "en": "⏱ Uptime: {uptime}  |  Xray: {xray}",
        "uz": "⏱ Ishlash vaqti: {uptime}  |  Xray: {xray}",
        "ru": "⏱ Аптайм: {uptime}  |  Xray: {xray}",
        "zh": "⏱ 运行时间：{uptime}  |  Xray：{xray}",
        "fa": "⏱ آپتایم: {uptime}  |  Xray: {xray}",
    },
    "report_stats": {
        "en": "👥 Total: {total}  |  🟢 Online: {online}",
        "uz": "👥 Jami: {total}  |  🟢 Onlayn: {online}",
        "ru": "👥 Всего: {total}  |  🟢 Онлайн: {online}",
        "zh": "👥 总计：{total}  |  🟢 在线：{online}",
        "fa": "👥 مجموع: {total}  |  🟢 آنلاین: {online}",
    },
    "report_depleting": {
        "en": "⚠️ <b>Depleting soon ({count})</b>",
        "uz": "⚠️ <b>Tez tugaydi ({count})</b>",
        "ru": "⚠️ <b>Скоро закончится ({count})</b>",
        "zh": "⚠️ <b>即将耗尽（{count}）</b>",
        "fa": "⚠️ <b>به زودی تمام می‌شود ({count})</b>",
    },
    "report_and_more": {
        "en": "  …and {count} more",
        "uz": "  …va yana {count} ta",
        "ru": "  …и ещё {count}",
        "zh": "  …还有 {count} 个",
        "fa": "  …و {count} مورد دیگر",
    },
}


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    """Return a translated string, formatted with kwargs."""
    lang_dict = _S.get(key)
    if lang_dict is None:
        return key
    text = lang_dict.get(lang) or lang_dict.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
