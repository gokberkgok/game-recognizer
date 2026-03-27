
from flask import Flask, request, jsonify, render_template_string
import numpy as np
import requests

app = Flask(__name__)

RAWG_KEY  = ""
RAWG_BASE = "https://api.rawg.io/api"

# ══════════════════════════════════════════════════════════════════
#  14-BOYUTLU VEKTÖR
# ══════════════════════════════════════════════════════════════════
ALL_TAGS = [
    "competitive", "story", "loot_craft", "exploration",
    "action_reflex", "strategy", "relaxing", "cinematic",
    "solo", "coop_mmo",
    "grind", "p2w_toxic", "shallow_story", "buggy",
]
PENALTY_TAGS = {"grind", "p2w_toxic", "shallow_story", "buggy"}

# ══════════════════════════════════════════════════════════════════
#  PLATFORM HARİTASI
# ══════════════════════════════════════════════════════════════════
PLATFORM_RAWG = {
    "pc":      [4],
    "ps":      [18, 187],
    "xbox":    [1, 186],
    "switch":  [7],
    "mobile":  [3, 21],
}

# ══════════════════════════════════════════════════════════════════
#  RAWG ↔ İÇ VEKTÖR
# ══════════════════════════════════════════════════════════════════
RAWG_TO_INTERNAL = {
    "action":                 {"action_reflex": 8, "competitive": 3},
    "shooter":                {"action_reflex": 9, "competitive": 7},
    "role-playing-games-rpg": {"story": 6, "loot_craft": 7, "exploration": 5},
    "adventure":              {"story": 7, "exploration": 6, "cinematic": 5},
    "strategy":               {"strategy": 9},
    "simulation":             {"relaxing": 7, "loot_craft": 5},
    "casual":                 {"relaxing": 9},
    "massively-multiplayer":  {"coop_mmo": 10, "grind": 6},
    "indie":                  {"story": 4, "exploration": 4, "relaxing": 3},
    "puzzle":                 {"strategy": 6, "relaxing": 5},
    "platformer":             {"action_reflex": 7},
    "fighting":               {"action_reflex": 8, "competitive": 9},
    "sports":                 {"competitive": 8},
    "racing":                 {"action_reflex": 7, "competitive": 6},
    "singleplayer":           {"solo": 10},
    "multiplayer":            {"coop_mmo": 7, "competitive": 5},
    "co-op":                  {"coop_mmo": 8},
    "online-co-op":           {"coop_mmo": 8},
    "mmo":                    {"coop_mmo": 10, "grind": 6},
    "open-world":             {"exploration": 9},
    "story-rich":             {"story": 9, "cinematic": 6},
    "atmospheric":            {"cinematic": 7, "story": 5},
    "action-rpg":             {"action_reflex": 7, "loot_craft": 7, "story": 5},
    "roguelike":              {"action_reflex": 6, "loot_craft": 5, "strategy": 5},
    "roguelite":              {"action_reflex": 6, "loot_craft": 5},
    "turn-based":             {"strategy": 8, "relaxing": 4},
    "turn-based-strategy":    {"strategy": 9},
    "real-time-strategy":     {"strategy": 9, "action_reflex": 4},
    "crafting":               {"loot_craft": 9},
    "survival":               {"loot_craft": 6, "exploration": 6, "action_reflex": 4},
    "sandbox":                {"loot_craft": 7, "exploration": 8, "relaxing": 5},
    "relaxing":               {"relaxing": 10},
    "cozy":                   {"relaxing": 10},
    "farming-sim":            {"relaxing": 9, "loot_craft": 6},
    "exploration":            {"exploration": 9},
    "fast-paced":             {"action_reflex": 8, "competitive": 5},
    "pvp":                    {"competitive": 9, "coop_mmo": 5},
    "competitive":            {"competitive": 9},
    "esports":                {"competitive": 10},
    "loot":                   {"loot_craft": 8},
    "base-building":          {"loot_craft": 7, "strategy": 6},
    "tower-defense":          {"strategy": 7},
    "tactical":               {"strategy": 8},
    "stealth":                {"strategy": 6, "solo": 5},
    "horror":                 {"cinematic": 5, "story": 5},
    "narrative":              {"story": 10, "cinematic": 8},
    "visual-novel":           {"story": 9, "cinematic": 7, "relaxing": 5},
    "metroidvania":           {"exploration": 8, "action_reflex": 7, "story": 5},
    "souls-like":             {"action_reflex": 9, "strategy": 6},
    "hack-and-slash":         {"action_reflex": 8, "loot_craft": 6},
    "dungeon-crawler":        {"loot_craft": 8, "action_reflex": 6, "exploration": 5},
    "4x":                     {"strategy": 10, "exploration": 6},
    "city-builder":           {"strategy": 8, "relaxing": 6},
    "management":             {"strategy": 7, "relaxing": 5},
    "great-soundtrack":       {"cinematic": 5, "relaxing": 3},
    "souls-like":             {"action_reflex": 9, "strategy": 6},
    "difficult":              {"action_reflex": 5, "strategy": 5},
    "choices-matter":         {"story": 8, "cinematic": 6},
    "multiple-endings":       {"story": 9, "cinematic": 7},
    "card-game":              {"strategy": 7, "competitive": 4},
    "deckbuilding":           {"strategy": 8, "loot_craft": 5},
    "linear":                 {"cinematic": 6, "story": 5},
    "nonlinear":              {"exploration": 6, "story": 5},
    "character-customization":{"loot_craft": 6},
    "bullet-hell":            {"action_reflex": 9, "competitive": 4},
    "resource-management":    {"strategy": 8, "loot_craft": 5},
    "post-apocalyptic":       {"exploration": 5, "story": 4},
    "cyberpunk":              {"story": 5, "cinematic": 6},
    "sci-fi":                 {"story": 4, "cinematic": 4},
    "fantasy":                {"story": 5, "loot_craft": 4},
    "pixel-graphics":         {"relaxing": 3},
    "party-game":             {"coop_mmo": 7, "relaxing": 5},
    "isometric":              {"strategy": 5},
    "stealth":                {"strategy": 6, "solo": 5},
}

INTERNAL_TO_RAWG_GENRES = {
    "competitive":   ["shooter", "fighting", "sports"],
    "story":         ["adventure", "role-playing-games-rpg"],
    "loot_craft":    ["role-playing-games-rpg", "simulation"],
    "exploration":   ["adventure", "role-playing-games-rpg"],
    "action_reflex": ["action", "shooter", "platformer", "fighting"],
    "strategy":      ["strategy"],
    "relaxing":      ["casual", "simulation", "indie", "puzzle"],
    "cinematic":     ["adventure"],
    "solo":          ["adventure", "indie"],
    "coop_mmo":      ["massively-multiplayer", "shooter"],
}

INTERNAL_TO_RAWG_TAGS = {
    "competitive":   ["competitive", "pvp", "esports"],
    "story":         ["story-rich", "narrative", "choices-matter"],
    "loot_craft":    ["loot", "crafting", "dungeon-crawler", "deckbuilding"],
    "exploration":   ["open-world", "exploration", "sandbox"],
    "action_reflex": ["fast-paced", "action-rpg", "hack-and-slash", "souls-like"],
    "strategy":      ["turn-based", "real-time-strategy", "tactical", "4x"],
    "relaxing":      ["relaxing", "cozy", "farming-sim"],
    "cinematic":     ["atmospheric", "story-rich", "linear"],
    "solo":          ["singleplayer", "stealth"],
    "coop_mmo":      ["multiplayer", "co-op", "online-co-op", "mmo"],
}

# ══════════════════════════════════════════════════════════════════
#  SORU 1 — Platform
# ══════════════════════════════════════════════════════════════════
PHASE1_QUESTIONS = [
    {
        "id": "q1",
        "text": "Hangi platformda oynarsın?",
        "multi": True,
        "choices": [
            {"key": "pc",     "label": "PC"},
            {"key": "ps",     "label": "PlayStation"},
            {"key": "xbox",   "label": "Xbox"},
            {"key": "switch", "label": "Switch / Taşınabilir"},
            {"key": "mobile", "label": "Mobil"},
        ],
        "weights_map": {
            "pc":     {"solo": +3, "exploration": +2, "loot_craft": +2},
            "ps":     {"cinematic": +5, "story": +3},
            "xbox":   {"action_reflex": +3, "competitive": +3},
            "switch": {"relaxing": +5, "solo": +3},
            "mobile": {"relaxing": +8, "coop_mmo": -3},
        },
    },
    # ── Q2: Oynanış döngüsü ─────────────────────────────────────
    {
        "id": "q2",
        "text": "Seni saatlerce ekrana bağlayan şey nedir?",
        "multi": True,
        "choices": [
            {"key": "story",    "label": "Derin hikaye & karakter gelişimi"},
            {"key": "reflex",   "label": "Yetenek, refleks & mekanik ustalığı"},
            {"key": "strategy", "label": "Kaynak yönetimi & strateji"},
            {"key": "explore",  "label": "Uçsuz bucaksız dünyayı keşfetmek"},
            {"key": "loot",     "label": "Build yapmak, eşya & min-max"},
        ],
        "weights_map": {
            "story":    {"story": +10, "cinematic": +6, "competitive": -2},
            "reflex":   {"action_reflex": +10, "competitive": +5, "relaxing": -4},
            "strategy": {"strategy": +10, "loot_craft": +3},
            "explore":  {"exploration": +10, "story": +3, "relaxing": +4},
            "loot":     {"loot_craft": +10, "strategy": +4, "competitive": +2},
        },
    },
    # ── Q3: Zorluk toleransı ─────────────────────────────────────
    {
        "id": "q3",
        "text": "Oyundaki zorluk anlayışın nedir?",
        "multi": False,
        "choices": [
            {"key": "souls",   "label": "Cezalandırıcı ama tatmin edici (Soulslike)"},
            {"key": "rogue",   "label": "Ölünce başa dön, hatadan öğren (Roguelike)"},
            {"key": "fair",    "label": "Taktik değiştirerek aşılabilir, adil zorluk"},
            {"key": "dynamic", "label": "Dinamik zorluk, beceriye göre adapte olsun"},
            {"key": "story",   "label": "Zorluk önemli değil, akışı yaşamak isterim"},
        ],
        "weights_map": {
            "souls":   {"action_reflex": +8, "strategy": +5, "competitive": +3, "relaxing": -5},
            "rogue":   {"action_reflex": +6, "loot_craft": +5, "strategy": +4},
            "fair":    {"strategy": +7, "loot_craft": +4, "action_reflex": +3},
            "dynamic": {"relaxing": +6, "cinematic": +4, "action_reflex": -2},
            "story":   {"story": +7, "cinematic": +7, "relaxing": +8, "action_reflex": -8},
        },
    },
    # ── Q4: Oturum süresi ───────────────────────────────────────
    {
        "id": "q4",
        "text": "Tipik oyun oturumun ne kadar sürer?",
        "multi": False,
        "choices": [
            {"key": "quick",  "label": "15–30 dk · Hızlı seanslar"},
            {"key": "mid",    "label": "1–2 saat · Net maçlar & görevler"},
            {"key": "long",   "label": "4–5 saat · Dünyaya gömülmek"},
            {"key": "daily",  "label": "Her gün düzenli · Canlı servis (MMO/GaaS)"},
            {"key": "flex",   "label": "Belirsiz · İstediğim an bırakabilmeliyim"},
        ],
        "weights_map": {
            "quick":  {"relaxing": +8, "solo": +4, "coop_mmo": -3, "exploration": -2},
            "mid":    {"competitive": +3, "story": +3, "action_reflex": +3},
            "long":   {"story": +7, "exploration": +6, "cinematic": +5},
            "daily":  {"coop_mmo": +10, "grind": +4, "competitive": +3},
            "flex":   {"relaxing": +6, "strategy": +5, "solo": +5},
        },
    },
    # ── Q5: Sosyal tercih ───────────────────────────────────────
    {
        "id": "q5",
        "text": "Diğer oyuncularla nasıl bir etkileşim istersin?",
        "multi": False,
        "choices": [
            {"key": "ranked",  "label": "Rekabetçi · Rank & sıralama"},
            {"key": "coop",    "label": "İşbirliği · Arkadaşla omuz omuza"},
            {"key": "mmo",     "label": "Devasa topluluk · Guild & ekonomi (MMO)"},
            {"key": "ghost",   "label": "Dolaylı · Başkalarının izini görmek yeter"},
            {"key": "solo",    "label": "Tamamen yalnız · Tek oyunculu"},
        ],
        "weights_map": {
            "ranked": {"competitive": +10, "coop_mmo": +4, "solo": -5},
            "coop":   {"coop_mmo": +8, "competitive": +3, "solo": -3},
            "mmo":    {"coop_mmo": +10, "grind": +4, "competitive": +3},
            "ghost":  {"solo": +7, "exploration": +4, "cinematic": +3},
            "solo":   {"solo": +10, "coop_mmo": -10, "competitive": -5},
        },
    },
    # ── Q6: Atmosfer ────────────────────────────────────────────
    {
        "id": "q6",
        "text": "Hangi atmosfer seni en çok çeker?",
        "multi": True,
        "choices": [
            {"key": "dark",   "label": "Karanlık · Gotik · Distopik"},
            {"key": "cozy",   "label": "Cozy · Renkli · Huzurlu"},
            {"key": "real",   "label": "Gerçekçi · Askeri · Tarihsel"},
            {"key": "indie",  "label": "Stilize · Piksel · Sanatsal"},
            {"key": "scifi",  "label": "Sci-Fi · Cyberpunk · Uzay"},
        ],
        "weights_map": {
            "dark":  {"story": +5, "cinematic": +6, "relaxing": -3},
            "cozy":  {"relaxing": +10, "solo": +3, "competitive": -5},
            "real":  {"action_reflex": +5, "competitive": +5, "cinematic": +4},
            "indie": {"relaxing": +4, "story": +4, "exploration": +4},
            "scifi": {"story": +5, "cinematic": +6, "exploration": +4},
        },
    },
    # ── Q7: İlerleme stili ──────────────────────────────────────
    {
        "id": "q7",
        "text": "Oyun sana nasıl bir yol sunmalı?",
        "multi": False,
        "choices": [
            {"key": "choice",   "label": "Seçimlerim sonu değiştirsin (Branching story)"},
            {"key": "sandbox",  "label": "Hedefsiz sandbox · Kendi hikayem"},
            {"key": "linear",   "label": "Çizgisel · Mükemmel tempo & aksiyon"},
            {"key": "openmap",  "label": "Açık harita · Görev & ikon dolu"},
            {"key": "detective","label": "Metin & dedektiflik · Düşünce odaklı"},
        ],
        "weights_map": {
            "choice":    {"story": +10, "cinematic": +6, "exploration": +3},
            "sandbox":   {"exploration": +10, "loot_craft": +6, "story": -2},
            "linear":    {"cinematic": +9, "story": +7, "action_reflex": +4},
            "openmap":   {"exploration": +7, "loot_craft": +5, "action_reflex": +3},
            "detective": {"story": +9, "strategy": +5, "action_reflex": -5},
        },
    },
    # ── Q8: Mekanik derinliği ────────────────────────────────────
    {
        "id": "q8",
        "text": "Kaç tuş, kaç alt-menü istersin?",
        "multi": True,
        "choices": [
            {"key": "deep",    "label": "Grand Strategy seviyesi derinlik · Mikro-yönetim"},
            {"key": "ranked",  "label": "Basit öğren, yıllarca ustalaş (MOBA/taktik FPS)"},
            {"key": "timing",  "label": "Az tuş ama kusursuz zamanlama & ritim"},
            {"key": "puzzle",  "label": "Fizik motoru & kompleks bulmaca"},
            {"key": "simple",  "label": "Direkt aksiyona gir, tutorial yok"},
        ],
        "weights_map": {
            "deep":   {"strategy": +10, "loot_craft": +5, "action_reflex": -5},
            "ranked": {"competitive": +9, "strategy": +6, "action_reflex": +5},
            "timing": {"action_reflex": +8, "competitive": +4, "relaxing": +2},
            "puzzle": {"strategy": +7, "exploration": +5, "action_reflex": +3},
            "simple": {"relaxing": +8, "story": +4, "cinematic": +4, "action_reflex": -3},
        },
    },
    # ── Q9: Uzun vade ────────────────────────────────────────────
    {
        "id": "q9",
        "text": "Oyundan uzun vadede ne bekliyorsun?",
        "multi": True,
        "choices": [
            {"key": "finish",  "label": "Net final · Bitsin, rafa kalksın"},
            {"key": "endgame", "label": "End-game · Aylarca oyalasın"},
            {"key": "mods",    "label": "Modding desteği"},
            {"key": "live",    "label": "Sezon & Battle Pass · Canlı servis"},
            {"key": "replay",  "label": "Yüksek replayability · Farklı build/ending"},
        ],
        "weights_map": {
            "finish":  {"cinematic": +5, "story": +5, "solo": +5},
            "endgame": {"loot_craft": +9, "competitive": +4, "coop_mmo": +3},
            "mods":    {"exploration": +6, "loot_craft": +4, "solo": +4},
            "live":    {"coop_mmo": +9, "grind": +4, "competitive": +4},
            "replay":  {"loot_craft": +6, "strategy": +5, "story": +4, "action_reflex": +3},
        },
    },
    # ── Q10: Kırmızı Bayrak ─────────────────────────────────────
    {
        "id": "q10",
        "text": "Oyunu anında silmeni sağlayacak şey nedir?",
        "multi": True,
        "choices": [
            {"key": "p2w",    "label": "Pay-to-Win · Gacha"},
            {"key": "toxic",  "label": "Toksik topluluk · Zorunlu online"},
            {"key": "grind",  "label": "Anlamsız Grind · Tekrarlı görev"},
            {"key": "cutsc",  "label": "Sonsuz kesme sahnesi · Oynamak yerine izlemek"},
            {"key": "bug",    "label": "Kötü kontrol · Bug · Optimizasyon sorunu"},
        ],
        "weights_map": {
            "p2w":   {"p2w_toxic": -50},
            "toxic": {"p2w_toxic": -30, "coop_mmo": -5},
            "grind": {"grind": -50, "story": +3, "cinematic": +3},
            "cutsc": {"shallow_story": -20, "cinematic": -10, "action_reflex": +5},
            "bug":   {"buggy": -50, "relaxing": +3},
        },
    },
]

# ══════════════════════════════════════════════════════════════════
#  EKSTRA 5 SORU — profile'a göre dinamik
#  Her sorunun hangi iç etikete göre gösterileceği belirtilmiş.
#  En yüksek puanlı 5 etikete karşılık gelen 5 soru seçilir.
# ══════════════════════════════════════════════════════════════════
PHASE2_POOL = [
    # ── competitive ─────────────────────────────────────────────
    {
        "id": "p2_competitive",
        "trigger": "competitive",
        "text": "Rekabetçi ortamda hangi formata girersin?",
        "multi": True,
        "choices": [
            {"key": "fps",   "label": "Taktiksel FPS (CS, Valorant)"},
            {"key": "moba",  "label": "MOBA (LoL, Dota)"},
            {"key": "br",    "label": "Battle Royale"},
            {"key": "rts",   "label": "RTS · 1v1 strateji"},
            {"key": "fight", "label": "Dövüş oyunları"},
        ],
        "weights_map": {
            "fps":   {"action_reflex": +8, "competitive": +5, "strategy": +4},
            "moba":  {"strategy": +8, "competitive": +6, "coop_mmo": +4},
            "br":    {"action_reflex": +6, "competitive": +7, "exploration": +2},
            "rts":   {"strategy": +10, "competitive": +5},
            "fight": {"action_reflex": +9, "competitive": +8},
        },
    },
    # ── story ────────────────────────────────────────────────────
    {
        "id": "p2_story",
        "trigger": "story",
        "text": "Seni en çok etkileyen hikaye türü hangisi?",
        "multi": True,
        "choices": [
            {"key": "dark",     "label": "Karanlık, trajik, tökezleten"},
            {"key": "choice",   "label": "Seçim bazlı, dallanmalı anlatı"},
            {"key": "epic",     "label": "Destansı fantezi & epik macera"},
            {"key": "mystery",  "label": "Gizem & dedektiflik"},
            {"key": "emotional","label": "Duygusal, karaktere bağlanmak"},
        ],
        "weights_map": {
            "dark":      {"story": +6, "cinematic": +7, "relaxing": -3},
            "choice":    {"story": +8, "cinematic": +5, "exploration": +3},
            "epic":      {"story": +6, "cinematic": +6, "action_reflex": +3},
            "mystery":   {"story": +7, "strategy": +5, "exploration": +4},
            "emotional": {"story": +9, "cinematic": +8, "competitive": -3},
        },
    },
    # ── loot_craft ───────────────────────────────────────────────
    {
        "id": "p2_loot",
        "trigger": "loot_craft",
        "text": "Karakter / eşya sistemi nasıl olmalı?",
        "multi": True,
        "choices": [
            {"key": "deep_loot", "label": "Derin loot & nadirlik sistemi (Diablo tarzı)"},
            {"key": "crafting",  "label": "Crafting · Ham maddeden eşya üret"},
            {"key": "build",     "label": "Karmaşık yetenek ağacı & build teorisi"},
            {"key": "deck",      "label": "Kart & deck kurma"},
            {"key": "base",      "label": "Üs / baz inşa et & geliştir"},
        ],
        "weights_map": {
            "deep_loot": {"loot_craft": +9, "action_reflex": +4},
            "crafting":  {"loot_craft": +8, "exploration": +4, "strategy": +3},
            "build":     {"loot_craft": +7, "strategy": +7},
            "deck":      {"strategy": +8, "loot_craft": +5, "competitive": +3},
            "base":      {"loot_craft": +7, "strategy": +6, "relaxing": +3},
        },
    },
    # ── exploration ─────────────────────────────────────────────
    {
        "id": "p2_exploration",
        "trigger": "exploration",
        "text": "Keşif oyununda seni en çok heyecanlandıran nedir?",
        "multi": True,
        "choices": [
            {"key": "proc",   "label": "Prosedürel üretim · Her seferinde farklı harita"},
            {"key": "lore",   "label": "Dünyaya gizlenmiş gizli lore & easter egg"},
            {"key": "vert",   "label": "Dikey dünya · Mağaralar, kuleler, derinlik"},
            {"key": "open",   "label": "Dev açık dünya · Kaybolurum"},
            {"key": "metroid","label": "Haritayı açarak ilerlemek (Metroidvania)"},
        ],
        "weights_map": {
            "proc":    {"exploration": +8, "loot_craft": +4, "strategy": +3},
            "lore":    {"exploration": +7, "story": +6, "cinematic": +4},
            "vert":    {"exploration": +8, "action_reflex": +4},
            "open":    {"exploration": +9, "relaxing": +4},
            "metroid": {"exploration": +8, "action_reflex": +5, "story": +3},
        },
    },
    # ── action_reflex ────────────────────────────────────────────
    {
        "id": "p2_action",
        "trigger": "action_reflex",
        "text": "Aksiyon oyununda hangi his seni tatmin eder?",
        "multi": True,
        "choices": [
            {"key": "combo",   "label": "Akıcı kombo & animasyon hissi (hack&slash)"},
            {"key": "aim",     "label": "Nişan hassasiyeti & headshot (FPS)"},
            {"key": "parry",   "label": "Mükemmel timing · Parry & dodge"},
            {"key": "speed",   "label": "Hız & momentum (Platformer, Speedrun)"},
            {"key": "stealth", "label": "Gizlilik & sessiz öldürme"},
        ],
        "weights_map": {
            "combo":   {"action_reflex": +8, "cinematic": +4, "loot_craft": +3},
            "aim":     {"action_reflex": +9, "competitive": +6},
            "parry":   {"action_reflex": +8, "strategy": +5},
            "speed":   {"action_reflex": +9, "competitive": +4},
            "stealth": {"action_reflex": +5, "strategy": +6, "solo": +5},
        },
    },
    # ── strategy ─────────────────────────────────────────────────
    {
        "id": "p2_strategy",
        "trigger": "strategy",
        "text": "Strateji oyununda hangi boyutu seversin?",
        "multi": True,
        "choices": [
            {"key": "grand",  "label": "Grand Strategy · Ulusları yönet, tarih yaz"},
            {"key": "turn",   "label": "Turn-based taktik · Her hamleyi hesapla"},
            {"key": "city",   "label": "Şehir kurma & ekonomi simülasyonu"},
            {"key": "tower",  "label": "Tower Defense & puzzle strateji"},
            {"key": "realtime","label": "RTS · Gerçek zamanlı komuta"},
        ],
        "weights_map": {
            "grand":    {"strategy": +10, "exploration": +5, "loot_craft": +3},
            "turn":     {"strategy": +9, "loot_craft": +4},
            "city":     {"strategy": +8, "relaxing": +5, "loot_craft": +3},
            "tower":    {"strategy": +7, "action_reflex": +3},
            "realtime": {"strategy": +9, "action_reflex": +4, "competitive": +3},
        },
    },
    # ── relaxing ─────────────────────────────────────────────────
    {
        "id": "p2_relaxing",
        "trigger": "relaxing",
        "text": "Rahatlamak için hangi oyun stilini seçersin?",
        "multi": True,
        "choices": [
            {"key": "farm",   "label": "Çiftçilik & köy simülasyonu"},
            {"key": "puzzle", "label": "Rahatlatıcı bulmaca"},
            {"key": "walk",   "label": "Walking sim · Atmosfer & keşif"},
            {"key": "craft",  "label": "Sakin crafting & inşaat"},
            {"key": "idle",   "label": "Idle / Incremental oyunlar"},
        ],
        "weights_map": {
            "farm":   {"relaxing": +10, "loot_craft": +5, "solo": +3},
            "puzzle": {"relaxing": +8, "strategy": +4},
            "walk":   {"relaxing": +7, "story": +5, "cinematic": +5},
            "craft":  {"relaxing": +8, "loot_craft": +6, "exploration": +3},
            "idle":   {"relaxing": +9, "competitive": -3},
        },
    },
    # ── cinematic ────────────────────────────────────────────────
    {
        "id": "p2_cinematic",
        "trigger": "cinematic",
        "text": "Sinematik oyunlarda seni büyüleyen ne?",
        "multi": True,
        "choices": [
            {"key": "direct",  "label": "Sinematografi & yönetmenlik kalitesi"},
            {"key": "voice",   "label": "Seslendirme & müzik"},
            {"key": "world",   "label": "Dünya kurgusu & lore derinliği"},
            {"key": "morality","label": "Ahlaki ikilemler & zor seçimler"},
            {"key": "set",     "label": "Unutulmaz set parçaları & aksiyon sahneleri"},
        ],
        "weights_map": {
            "direct":   {"cinematic": +9, "story": +5},
            "voice":    {"cinematic": +7, "story": +5, "relaxing": +3},
            "world":    {"cinematic": +6, "story": +7, "exploration": +5},
            "morality": {"story": +9, "cinematic": +5},
            "set":      {"cinematic": +8, "action_reflex": +5},
        },
    },
    # ── coop_mmo ─────────────────────────────────────────────────
    {
        "id": "p2_coop",
        "trigger": "coop_mmo",
        "text": "Çok oyunculu ortamda rolün ne?",
        "multi": False,
        "choices": [
            {"key": "tank",    "label": "Tank · Ön cephe, lider"},
            {"key": "heal",    "label": "Healer / Support"},
            {"key": "dps",     "label": "DPS · Hasar makinesi"},
            {"key": "crafter", "label": "Ekonomi & crafting uzmanı"},
            {"key": "scout",   "label": "Kaşif & informasyon toplayıcı"},
        ],
        "weights_map": {
            "tank":    {"competitive": +6, "coop_mmo": +7, "action_reflex": +4},
            "heal":    {"coop_mmo": +8, "strategy": +5, "relaxing": +3},
            "dps":     {"action_reflex": +7, "competitive": +6, "coop_mmo": +4},
            "crafter": {"loot_craft": +8, "strategy": +4, "coop_mmo": +5},
            "scout":   {"exploration": +7, "coop_mmo": +5, "strategy": +4},
        },
    },
    # ── solo ─────────────────────────────────────────────────────
    {
        "id": "p2_solo",
        "trigger": "solo",
        "text": "Tek oyunculu deneyimde ne ararsın?",
        "multi": True,
        "choices": [
            {"key": "immersion", "label": "Tam dalış · Baş başa bir evren"},
            {"key": "challenge", "label": "Beni alt eden zorluk"},
            {"key": "narrative", "label": "Güçlü anlatı & karakter"},
            {"key": "freedom",   "label": "Sınırsız özgürlük & yaratıcılık"},
            {"key": "complete",  "label": "%100 tamamlama & başarım avcılığı"},
        ],
        "weights_map": {
            "immersion": {"solo": +8, "cinematic": +6, "story": +5},
            "challenge": {"solo": +6, "action_reflex": +6, "strategy": +4},
            "narrative": {"story": +9, "cinematic": +6, "solo": +5},
            "freedom":   {"exploration": +8, "loot_craft": +5, "solo": +5},
            "complete":  {"loot_craft": +7, "competitive": +4, "solo": +6},
        },
    },
]

# ══════════════════════════════════════════════════════════════════
#  YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════════
def build_vector(answers: dict, question_bank: list) -> dict:
    """answers: {q_id: [key, key, ...]} → vektör"""
    vec = {k: 0 for k in ALL_TAGS}
    for q_id, selected_keys in answers.items():
        question = next((q for q in question_bank if q["id"] == q_id), None)
        if not question:
            continue
        if isinstance(selected_keys, str):
            selected_keys = [selected_keys]
        for key in selected_keys:
            for tag, val in question["weights_map"].get(key, {}).items():
                vec[tag] = vec.get(tag, 0) + val
    return vec


def build_rawg_params(user_vec: dict, platforms: list,
                      page: int = 1, page_size: int = 40,
                      exclude_ids: list = None) -> dict:
    positive = {k: v for k, v in user_vec.items()
                if v > 0 and k not in PENALTY_TAGS}
    top3 = sorted(positive, key=positive.get, reverse=True)[:3]

    genre_set, tag_set = [], []
    for tag in top3:
        for g in INTERNAL_TO_RAWG_GENRES.get(tag, []):
            if g not in genre_set: genre_set.append(g)
        for t in INTERNAL_TO_RAWG_TAGS.get(tag, [])[:2]:
            if t not in tag_set:  tag_set.append(t)

    params = {
        "key":        RAWG_KEY,
        "page":       page,
        "page_size":  page_size,
        "ordering":   "-rating",
        "metacritic": "65,100",
    }
    if genre_set: params["genres"]    = ",".join(genre_set[:4])
    if tag_set:   params["tags"]      = ",".join(tag_set[:3])
    if platforms: params["platforms"] = ",".join(str(p) for p in platforms)
    if exclude_ids:
        params["exclude_collection"] = ",".join(str(i) for i in exclude_ids)

    return params


def fetch_games(params: dict) -> list:
    try:
        resp = requests.get(f"{RAWG_BASE}/games", params=params, timeout=12)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        print(f"[RAWG] {len(results)} sonuç | URL: {resp.url}")
        return results
    except Exception as e:
        print(f"[RAWG HATA] {e}")
        return []


def rawg_to_vec(game: dict) -> dict:
    vec = {k: 0 for k in ALL_TAGS}
    sources = (
        [(g["slug"], 1.0)  for g in game.get("genres", [])] +
        [(t["slug"], 0.75) for t in game.get("tags",   [])[:35]]
    )
    for slug, w in sources:
        for itag, val in RAWG_TO_INTERNAL.get(slug, {}).items():
            vec[itag] = min(10, vec[itag] + int(val * w))
    return vec


def score_game(user_vec: dict, game_vec: dict) -> float:
    pos = [k for k in ALL_TAGS if k not in PENALTY_TAGS]
    a = np.array([max(0, user_vec.get(k, 0)) for k in pos], dtype=float)
    b = np.array([game_vec.get(k, 0) for k in pos], dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    sim   = float(np.dot(a, b) / (na * nb)) if na > 0 and nb > 0 else 0.0
    score = (sim + 1) / 2 * 100.0
    for k in PENALTY_TAGS:
        if user_vec.get(k, 0) < 0:
            score -= abs(user_vec[k]) * game_vec.get(k, 0) / 10.0
    return max(0.0, min(100.0, round(score, 1)))


def rank_games(raw_games: list, user_vec: dict) -> list:
    out = []
    for g in raw_games:
        gv = rawg_to_vec(g)
        sc = score_game(user_vec, gv)
        out.append({
            "id":         g.get("id"),
            "title":      g.get("name", ""),
            "genres":     ", ".join(x["name"] for x in g.get("genres", [])[:3]),
            "rating":     round(g.get("rating", 0), 1),
            "metacritic": g.get("metacritic"),
            "released":   (g.get("released") or "")[:4],
            "image":      g.get("background_image", ""),
            "score":      sc,
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def get_player_type(user_vec: dict):
    types = [
        ("⚔️",  "Killer",       "Rekabetçi",     "competitive",   "Kazanmak için yaşıyorsun. Rank zirveye ulaşmak senin için bir yaşam biçimi."),
        ("🗺️",  "Explorer",     "Kaşif",          "exploration",   "Haritanın her köşesi bir sırdır. Kimsenin bakmadığı yerde hep sen varsın."),
        ("🏆",  "Achiever",     "Toplayıcı",      "loot_craft",    "Mükemmel build, %100 tamamlama, maksimum eşya. Optimizasyon senin sanat formun."),
        ("🤝",  "Socializer",   "Sosyal Oyuncu",  "coop_mmo",      "Oyun, insanlarla bağ kurma aracın. Klan, guild, arkadaşlar — asıl deneyim bu."),
        ("📖",  "Storyteller",  "Hikaye Sever",   "story",         "İyi bir karakter seni ağlatabilir. Güçlü bir anlatı günlerce kafanda döner."),
        ("🧠",  "Strategist",   "Stratejist",     "strategy",      "Her hamleyi hesaplıyorsun. Sistemi sen olmasaydın çökerdi."),
        ("😌",  "Relaxer",      "Sakin Oyuncu",   "relaxing",      "Oyun senin için kaçış; stres değil huzur arıyorsun kontrollerin arkasında."),
        ("🎬",  "Cinephile",    "Sinefil",        "cinematic",     "Oyunu etkileşimli bir film gibi görüyorsun. Atmosfer ve görsel yön her şeyden önce."),
    ]
    best = max(types, key=lambda t: user_vec.get(t[3], 0))
    return f"{best[0]} {best[1]} / {best[2]}", best[4]


def select_phase2_questions(user_vec: dict, n: int = 5) -> list:
    """Pozitif etiket sırasına göre en uygun n soruyu seç."""
    pos = {k: v for k, v in user_vec.items() if v > 0 and k not in PENALTY_TAGS}
    ranked = sorted(pos, key=pos.get, reverse=True)
    selected, seen_triggers = [], set()
    for etag in ranked:
        for q in PHASE2_POOL:
            if q["trigger"] == etag and etag not in seen_triggers:
                selected.append(q)
                seen_triggers.add(etag)
                break
        if len(selected) == n:
            break
    # Eksik kalırsa havuzdan doldur
    for q in PHASE2_POOL:
        if len(selected) == n: break
        if q["trigger"] not in seen_triggers:
            selected.append(q)
            seen_triggers.add(q["trigger"])
    return selected[:n]


def get_platforms_from_answers(answers: dict) -> list:
    q1_ans = answers.get("q1", [])
    if isinstance(q1_ans, str): q1_ans = [q1_ans]
    plat = []
    for k in q1_ans:
        plat.extend(PLATFORM_RAWG.get(k, []))
    return list(set(plat))


# ══════════════════════════════════════════════════════════════════
#  HTML
# ══════════════════════════════════════════════════════════════════
HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Oyun Öneri Sistemi</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#c9d1d9;
       padding:20px 16px;max-width:820px;margin:0 auto}
  h1{text-align:center;color:#e94560;font-size:22px;margin-bottom:4px;letter-spacing:.5px}
  .sub{text-align:center;color:#555;font-size:12px;margin-bottom:20px}

  /* ── kart ── */
  .card{background:#161b22;border:1px solid #21262d;border-radius:10px;
        padding:18px;margin-bottom:14px}
  .q-title{font-size:13px;font-weight:600;color:#e6edf3;margin-bottom:12px;line-height:1.5}
  .q-num{color:#e94560;font-weight:700;margin-right:6px}
  .multi-hint{font-size:10px;color:#555;margin-left:4px;font-weight:400}

  /* ── seçenekler ── */
  .choices{display:flex;flex-wrap:wrap;gap:8px}
  .chip{padding:7px 14px;background:#21262d;border:1.5px solid #30363d;
        border-radius:20px;cursor:pointer;font-size:12px;color:#8b949e;
        transition:all .15s;user-select:none;line-height:1.3}
  .chip:hover{border-color:#e94560;color:#e6edf3}
  .chip.selected{background:#e94560;border-color:#e94560;color:#fff;font-weight:600}

  /* ── butonlar ── */
  .btn-primary{display:block;width:100%;padding:13px;background:#e94560;
               color:#fff;border:none;border-radius:8px;font-size:15px;
               font-weight:600;cursor:pointer;margin-top:6px;letter-spacing:.4px}
  .btn-primary:disabled{background:#21262d;color:#444;cursor:not-allowed}
  .btn-secondary{display:block;width:100%;padding:11px;background:transparent;
                 color:#e94560;border:1.5px solid #e94560;border-radius:8px;
                 font-size:14px;cursor:pointer;margin-top:12px;font-weight:600}

  /* ── progress ── */
  .prog-bar-wrap{background:#21262d;border-radius:4px;height:4px;margin-bottom:14px}
  .prog-bar{background:#e94560;height:4px;border-radius:4px;transition:width .3s}
  .prog-text{text-align:center;color:#555;font-size:11px;margin-bottom:8px}

  /* ── loading ── */
  #loading,#loading2{display:none;text-align:center;padding:50px 20px}
  .spinner{width:44px;height:44px;border:3px solid #21262d;border-top-color:#e94560;
           border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 14px}
  @keyframes spin{to{transform:rotate(360deg)}}
  .load-text{color:#555;font-size:13px}

  /* ── sonuç bölümü ── */
  #result,#result2{display:none}

  .player-block{background:#161b22;border:1px solid #30363d;border-radius:10px;
                padding:16px 18px;margin-bottom:16px;
                border-left:3px solid #e94560}
  .pt-name{font-size:17px;font-weight:700;color:#e94560;margin-bottom:5px}
  .pt-desc{font-size:12px;color:#8b949e;line-height:1.6}

  .section-label{font-size:11px;font-weight:700;color:#555;letter-spacing:1.2px;
                 text-transform:uppercase;margin-bottom:10px}

  /* ── oyun kartı ── */
  .game-card{display:flex;gap:12px;align-items:center;padding:12px;
             background:#161b22;border:1px solid #21262d;border-radius:8px;
             margin-bottom:8px;position:relative}
  .game-rank{font-size:11px;font-weight:700;color:#e94560;
             position:absolute;top:8px;left:8px;
             background:#0d1117;padding:1px 6px;border-radius:4px}
  .game-img{width:90px;height:56px;object-fit:cover;border-radius:5px;
            flex-shrink:0;background:#21262d}
  .game-info{flex:1;min-width:0}
  .game-title{font-size:13px;font-weight:700;color:#e6edf3;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .game-meta{font-size:11px;color:#555;margin-top:3px}
  .score-row{display:flex;align-items:center;gap:8px;margin-top:7px}
  .score-bar{flex:1;height:4px;background:#21262d;border-radius:2px}
  .score-fill{height:100%;background:linear-gradient(90deg,#e94560,#ff6b6b);
              border-radius:2px;transition:width .6s ease}
  .score-pct{font-size:11px;color:#e94560;font-weight:700;white-space:nowrap}

  /* ── profil etiketleri ── */
  .tag-cloud{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
  .tag{padding:3px 10px;background:#21262d;border:1px solid #30363d;
       border-radius:12px;font-size:11px;color:#8b949e}
  .tag.hot{border-color:#e94560;color:#e94560}

  /* ── phase2 teaser ── */
  .teaser{background:#161b22;border:1px dashed #30363d;border-radius:10px;
          padding:16px 18px;margin-top:16px;text-align:center}
  .teaser p{color:#8b949e;font-size:13px;margin-bottom:14px;line-height:1.6}

  .divider{border:none;border-top:1px solid #21262d;margin:20px 0}
  .err{color:#e94560;text-align:center;padding:16px;font-size:13px}
  .rawg-badge{text-align:right;font-size:10px;color:#30363d;margin-top:8px}
</style>
</head>
<body>
<h1>🎮 Oyun Profil Analizi</h1>
<p class="sub">Sorulara cevap ver · RAWG üzerinden kişisel öneri al</p>

<!-- ── PHASE 1 ─────────────────────────────── -->
<div id="phase1">
  <div class="prog-text" id="prog-text">0 / 10 yanıtlandı</div>
  <div class="prog-bar-wrap"><div class="prog-bar" id="prog-bar" style="width:0%"></div></div>
  <div id="quiz1"></div>
  <button class="btn-primary" id="btn1" disabled onclick="submitPhase1()">
    Analiz Et &amp; Top 10 Öner →
  </button>
</div>

<!-- ── LOADING 1 ─────────────────────────────── -->
<div id="loading">
  <div class="spinner"></div>
  <div class="load-text">Profil analiz ediliyor &amp; RAWG taranıyor…</div>
</div>

<!-- ── PHASE 1 RESULT ─────────────────────────── -->
<div id="result">
  <div class="player-block">
    <div class="pt-name" id="pt-name"></div>
    <div class="pt-desc" id="pt-desc"></div>
  </div>
  <div class="tag-cloud" id="tags1" style="margin-bottom:16px"></div>

  <div class="section-label">🎯 İlk 10 Kişisel Öneri</div>
  <div id="games1"></div>
  <div class="rawg-badge">RAWG.io API</div>

  <div class="teaser">
    <p>Profilini daha da derinleştir.<br>
    5 ek soru ile 2. tur önerileri tamamen farklı oyunlar içerecek.</p>
    <button class="btn-primary" style="max-width:320px;margin:0 auto"
            onclick="startPhase2()">
      Derinleştir &amp; 2. Tur Önerilerini Al →
    </button>
  </div>
</div>

<!-- ── PHASE 2 ─────────────────────────────── -->
<div id="phase2" style="display:none">
  <div class="prog-text" id="prog-text2">0 / 5 yanıtlandı</div>
  <div class="prog-bar-wrap"><div class="prog-bar" id="prog-bar2" style="width:0%"></div></div>
  <div id="quiz2"></div>
  <button class="btn-primary" id="btn2" disabled onclick="submitPhase2()">
    2. Tur Önerilerini Getir →
  </button>
</div>

<!-- ── LOADING 2 ─────────────────────────────── -->
<div id="loading2">
  <div class="spinner"></div>
  <div class="load-text">Derinleştirilmiş profil işleniyor…</div>
</div>

<!-- ── PHASE 2 RESULT ─────────────────────────── -->
<div id="result2">
  <hr class="divider">
  <div class="player-block">
    <div class="pt-name" id="pt-name2"></div>
    <div class="pt-desc" id="pt-desc2"></div>
  </div>
  <div class="tag-cloud" id="tags2" style="margin-bottom:16px"></div>
  <div class="section-label">🎯 2. Tur — 10 Yeni Öneri</div>
  <div id="games2"></div>
  <div class="rawg-badge">RAWG.io API</div>
  <button class="btn-secondary" onclick="restart()">↺ Baştan Başla</button>
</div>

<script>
const P1_QUESTIONS = {{ p1_questions|tojson }};
const TOTAL1 = P1_QUESTIONS.length;   // 10
const TOTAL2 = 5;

const ans1 = {};  // {q_id: [key,...]}
const ans2 = {};
let phase2Questions = [];
let firstRoundIds   = [];
let userVec1        = {};

/* ─── render quiz ─────────────────────────────────── */
function renderQuiz(questions, containerId, answerStore, totalCount,
                    progTextId, progBarId, btnId) {
  const div = document.getElementById(containerId);
  div.innerHTML = '';
  questions.forEach(q => {
    const card = document.createElement('div');
    card.className = 'card';
    const hint = q.multi ? '<span class="multi-hint">(birden fazla seçilebilir)</span>' : '';
    card.innerHTML = `<div class="q-title"><span class="q-num">${q.id.replace('q','S').replace('p2_','E-')}.</span>${q.text}${hint}</div>
                      <div class="choices" id="choices-${q.id}"></div>`;
    q.choices.forEach(c => {
      const chip = document.createElement('button');
      chip.className = 'chip';
      chip.textContent = c.label;
      chip.dataset.qid = q.id;
      chip.dataset.key = c.key;
      chip.onclick = () => toggleChip(chip, q, answerStore, totalCount, progTextId, progBarId, btnId);
      document.getElementById('choices-' + q.id)?.appendChild(chip);
      card.querySelector('.choices').appendChild(chip);
    });
    div.appendChild(card);
  });
}

function toggleChip(chip, question, answerStore, totalCount, progTextId, progBarId, btnId) {
  const qid = question.id;
  if (!question.multi) {
    // single select: deselect others
    document.querySelectorAll(`[data-qid="${qid}"]`).forEach(c => c.classList.remove('selected'));
    chip.classList.add('selected');
    answerStore[qid] = [chip.dataset.key];
  } else {
    chip.classList.toggle('selected');
    const selected = [...document.querySelectorAll(`[data-qid="${qid}"].selected`)].map(c => c.dataset.key);
    if (selected.length === 0) { delete answerStore[qid]; }
    else { answerStore[qid] = selected; }
  }
  const answered = Object.keys(answerStore).length;
  document.getElementById(progTextId).textContent = `${answered} / ${totalCount} yanıtlandı`;
  document.getElementById(progBarId).style.width = `${answered/totalCount*100}%`;
  document.getElementById(btnId).disabled = (answered < totalCount);
}

/* ─── phase 1 ─────────────────────────────────────── */
renderQuiz(P1_QUESTIONS, 'quiz1', ans1, TOTAL1, 'prog-text', 'prog-bar', 'btn1');

function submitPhase1() {
  show('loading'); hide('phase1');
  fetch('/recommend1', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify(ans1)
  })
  .then(r => r.json())
  .then(d => { hide('loading'); showResult1(d); })
  .catch(() => { hide('loading'); show('result');
    document.getElementById('games1').innerHTML = '<div class="err">RAWG API hatası.</div>'; });
}

function showResult1(d) {
  userVec1 = d.user_vector;
  firstRoundIds = (d.recommendations||[]).map(g => g.id).filter(Boolean);

  document.getElementById('pt-name').textContent = d.player_type;
  document.getElementById('pt-desc').textContent = d.player_desc;

  renderTags(d.user_vector, 'tags1');
  renderGames(d.recommendations || [], 'games1');
  show('result');

  // Dinamik phase2 soruları sakla
  phase2Questions = d.phase2_questions || [];
}

/* ─── phase 2 başlat ──────────────────────────────── */
function startPhase2() {
  hide('result');
  renderQuiz(phase2Questions, 'quiz2', ans2, TOTAL2, 'prog-text2', 'prog-bar2', 'btn2');
  show('phase2');
}

function submitPhase2() {
  show('loading2'); hide('phase2');
  fetch('/recommend2', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ ans1, ans2, first_round_ids: firstRoundIds })
  })
  .then(r => r.json())
  .then(d => { hide('loading2'); showResult2(d); })
  .catch(() => { hide('loading2'); show('result2');
    document.getElementById('games2').innerHTML = '<div class="err">RAWG API hatası.</div>'; });
}

function showResult2(d) {
  document.getElementById('pt-name2').textContent = d.player_type;
  document.getElementById('pt-desc2').textContent = d.player_desc;
  renderTags(d.user_vector, 'tags2');
  renderGames(d.recommendations || [], 'games2');
  show('result2');
  window.scrollTo({ top: document.getElementById('result2').offsetTop - 20, behavior: 'smooth' });
}

/* ─── yardımcılar ─────────────────────────────────── */
function renderGames(list, containerId) {
  const div = document.getElementById(containerId);
  div.innerHTML = '';
  if (!list.length) {
    div.innerHTML = '<div class="err">Oyun bulunamadı.</div>'; return;
  }
  list.forEach((g, i) => {
    const card = document.createElement('div');
    card.className = 'game-card';
    card.innerHTML = `
      <span class="game-rank">#${i+1}</span>
      <img class="game-img" src="${g.image||''}"
           onerror="this.style.display='none'" alt="">
      <div class="game-info">
        <div class="game-title">${g.title}</div>
        <div class="game-meta">${g.genres}${g.released?' · '+g.released:''} · ⭐ ${g.rating} · MC: ${g.metacritic||'–'}</div>
        <div class="score-row">
          <div class="score-bar"><div class="score-fill" style="width:${g.score}%"></div></div>
          <span class="score-pct">${g.score}%</span>
        </div>
      </div>`;
    div.appendChild(card);
  });
}

function renderTags(vec, containerId) {
  const div = document.getElementById(containerId);
  div.innerHTML = '';
  const pos = Object.entries(vec)
    .filter(([k,v]) => v>3 && !['grind','p2w_toxic','shallow_story','buggy'].includes(k))
    .sort((a,b) => b[1]-a[1]).slice(0,10);
  pos.forEach(([k,v]) => {
    const t = document.createElement('span');
    t.className = 'tag' + (v>=12?' hot':'');
    t.textContent = `${k}  +${v}`;
    div.appendChild(t);
  });
}

function show(id){ document.getElementById(id).style.display='block'; }
function hide(id){ document.getElementById(id).style.display='none'; }

function restart() {
  location.reload();
}
</script>
</body>
</html>
"""

# ══════════════════════════════════════════════════════════════════
#  FLASK ROTLARI
# ══════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    # Frontend'e sadece label + meta gönder (weights backend'de kalır)
    p1 = []
    for q in PHASE1_QUESTIONS:
        p1.append({
            "id":      q["id"],
            "text":    q["text"],
            "multi":   q["multi"],
            "choices": [{"key": c["key"], "label": c["label"]} for c in q["choices"]],
        })
    return render_template_string(HTML, p1_questions=p1)


@app.route("/recommend1", methods=["POST"])
def recommend1():
    answers = request.get_json()

    # 1. Vektör
    user_vec = build_vector(answers, PHASE1_QUESTIONS)

    # 2. Platform
    platforms = get_platforms_from_answers(answers)

    # 3. RAWG
    params = build_rawg_params(user_vec, platforms, page_size=50)
    raw = fetch_games(params)
    if len(raw) < 12 and "tags" in params:
        p2 = {k: v for k, v in params.items() if k != "tags"}
        raw += fetch_games(p2)

    # 4. Sırala → Top 10
    ranked = rank_games(raw, user_vec)[:10]

    # 5. Oyuncu tipi
    ptype, pdesc = get_player_type(user_vec)

    # 6. Phase 2 soruları seç (dinamik)
    p2_qs = select_phase2_questions(user_vec, n=5)
    p2_fe = []
    for q in p2_qs:
        p2_fe.append({
            "id":      q["id"],
            "text":    q["text"],
            "multi":   q["multi"],
            "choices": [{"key": c["key"], "label": c["label"]} for c in q["choices"]],
        })

    return jsonify({
        "player_type":      ptype,
        "player_desc":      pdesc,
        "recommendations":  ranked,
        "user_vector":      {k: v for k, v in user_vec.items() if v != 0},
        "phase2_questions": p2_fe,
    })


@app.route("/recommend2", methods=["POST"])
def recommend2():
    body         = request.get_json()
    ans1         = body.get("ans1", {})
    ans2         = body.get("ans2", {})
    first_ids    = set(body.get("first_round_ids", []))

    # 1. Birleşik vektör (phase1 + phase2)
    vec1 = build_vector(ans1, PHASE1_QUESTIONS)
    vec2 = build_vector(ans2, PHASE2_POOL)
    merged = {k: vec1.get(k, 0) + vec2.get(k, 0) for k in ALL_TAGS}

    # 2. Platform
    platforms = get_platforms_from_answers(ans1)

    # 3. RAWG — farklı sayfa / ordering ile al
    params = build_rawg_params(merged, platforms, page=2, page_size=50)
    raw = fetch_games(params)

    # Fallback: sayfada yeterli sonuç yoksa p=1 ordering değiştir
    if len(raw) < 12:
        params2 = build_rawg_params(merged, platforms, page=1, page_size=50)
        params2["ordering"] = "-added"
        raw += fetch_games(params2)

    # 4. Sırala, ilk tur oyunlarını çıkar
    ranked_all = rank_games(raw, merged)
    ranked = [g for g in ranked_all if g.get("id") not in first_ids][:10]

    ptype, pdesc = get_player_type(merged)

    return jsonify({
        "player_type":     ptype,
        "player_desc":     pdesc,
        "recommendations": ranked,
        "user_vector":     {k: v for k, v in merged.items() if v != 0},
    })


if __name__ == "__main__":
    print("=" * 56)
    print("  🎮  Oyun Profil Analizi —  Gökberk")
    print("  👉  http://localhost:5000")
    print("=" * 56)
    app.run(debug=True, port=5000)