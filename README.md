# 🤖 Discord Bot - Railway Hosting 🚀

To jest prosty bot Discord napisany w **Pythonie**, który działa **24/7** dzięki hostingowi **Railway.app**.

## 🔹 Funkcje
✅ Odpowiada na komendę `!ping` 🏓  
✅ Jest **hostowany 24/7** dzięki Flask + Railway  
✅ Używa **`discord.py` 2.x**  

---

## 📌 **Jak uruchomić lokalnie?**
Jeśli chcesz uruchomić bota na swoim komputerze:

### **1️⃣ Pobierz repozytorium**
```sh
git clone https://github.com/TWOJ_GITHUB/my-discord-bot.git
cd my-discord-bot
```

### **2️⃣ Zainstaluj zależności**
```sh
pip install -r requirements.txt
```

### **3️⃣ Stwórz plik `.env` i dodaj token bota**
```sh
DISCORD_TOKEN=twój_token
```

### **4️⃣ Uruchom bota**
```sh
python3 main.py
```

---

## 🚀 **Jak uruchomić bota na Railway?**
Dzięki **Railway** Twój bot działa **24/7** bez potrzeby ciągłego uruchamiania na komputerze.

### **1️⃣ Połącz GitHub z Railway**
1. Wejdź na **[Railway.app](https://railway.app/)**
2. Kliknij **„New Project”** → Wybierz **„Deploy from GitHub”**.
3. Wybierz repozytorium z botem i kliknij **„Deploy”**.

### **2️⃣ Dodaj zmienną środowiskową `DISCORD_TOKEN`**
1. W Railway otwórz **zakładkę „Variables”**.
2. Kliknij **„Add New Variable”**.
3. **Key:** `DISCORD_TOKEN`  
   **Value:** Wklej **swój token bota** (z Discord Developer Portal).
4. Kliknij **„Save”**.

### **3️⃣ Uruchom bota**
1. Przejdź do **zakładki „Deployments”**.
2. Jeśli bot się nie uruchomił, kliknij **„New Deployment”**.
3. Sprawdź **logi Railway** → powinieneś zobaczyć:
   ```
   ✅ Zalogowano jako MyDiscordBot#1234
   ```
🎉 **Twój bot jest teraz ONLINE 24/7!**  

---

## 📜 **Pliki w repozytorium**
📄 **`main.py`** - Główny kod bota  
📄 **`keep_alive.py`** - Serwer Flask dla UptimeRobot  
📄 **`requirements.txt`** - Lista bibliotek  
📄 **`Procfile`** - Plik startowy Railway  
📄 **`.gitignore`** - Pomaga ignorować niepotrzebne pliki  

---

## ❓ **Masz problem?**
Jeśli masz pytania lub problemy, otwórz **issue** na GitHub lub skontaktuj się z nami na Discordzie! 🎉  

🚀 **Miłej zabawy z botem!** 🤖
