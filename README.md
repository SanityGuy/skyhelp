# 🌌 SuperNova

SuperNova is a private, module-based Discord bot built with **discord.py 2.0+** using native slash commands. While designed and hosted specifically for a private community server, the codebase is entirely open-source, extensible, and open for developer contributions.

## 🚀 Features

- **Slash Commands Ready**: Built entirely around `app_commands` without legacy text prefixes.
- **Dynamic Extension Loading**: Automatically scans and loads modules inside the `commands/` and `listeners/` directories on startup.
- **Robust System Tools**: Includes built-in advanced moderation and information utilities (`/purge`, `/userinfo`, `/ping`).
- **Event-Driven Listeners**: Modular background processes for server activity monitoring (`greet`, `joinleave`, `messages`, `startup`).

## 📁 Project Structure

```text
├── SuperNova/
│   ├── commands/          # Application slash command cogs
│   │   ├── ping.py
│   │   ├── purge.py
│   │   └── userinfo.py
│   ├── listeners/         # Event handlers (on_message, on_member_join, etc.)
│   │   ├── greet.py
│   │   ├── joinleave.py
│   │   ├── messages.py
│   │   ├── startup.py
│   │   └── swear_words.txt
│   ├── .env               # Local environment secrets (Token)
│   ├── .gitignore         # Untracked runtime configurations
│   ├── client.py          # Custom Bot initialization subclass
│   └── main.py            # Main gateway runner application
```

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8 or higher
- A valid Discord Bot Token from the [Discord Developer Portal](https://discord.com)

### Installation Steps
1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd SuperNova
   ```

2. **Install dependencies:**
   ```bash
   pip install requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root directory matching your project configuration:
   ```env
   TOKEN=your_discord_bot_token_here
   ```

4. **Run the bot:**
   ```bash
   python main.py
   ```

## 🤝 Contributing

We welcome contributions! Even though this bot runs live on a private community server, the framework is built for anyone to build upon, test, or enhance.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT License
