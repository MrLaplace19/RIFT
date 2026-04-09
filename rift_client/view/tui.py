from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Header, Footer, Input, RichLog, Label
import websockets
import asyncio
# ----------------------
from ..api.chatfabric import ChatFabric
from ..models.message import ReceivedMessage

class ChatApp(App):
    BINDINGS = [
        ("q", "quit", "Выход"),
        ("f5", "refresh_users", "Обновить пользователей"),
        ("ctrl+r", "switch_room", "Сменить комнату"),
    ]

    CSS_PATH = "tui.css"

    def __init__(
        self, username: str, password: str, url: str = "ws://localhost:8765"
    ):
        super().__init__()
        self.username = username
        self.password = password
        self.chat_manager: ChatFabric | None = None
        self.websocket = None
        self.url = url
        self.online_users: list[str] = []
        self.current_room = "general"
        self.rooms = ["general", "random", "tech"]

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="main-container"):
            # Левая панель - Беседы
            with Vertical(id="rooms-panel"):
                yield Label("📋 Беседы", id="rooms-title")
                with VerticalScroll(id="rooms-list"):
                    for room in self.rooms:
                        is_active = room == self.current_room
                        room_class = "room-item-active" if is_active else "room-item"
                        yield Label(
                            f"# {room}", classes=room_class, id=f"room-{room}"
                        )

            # Центральная панель - Чат
            with Vertical(id="chat-panel"):
                yield Label(f"💬 {self.current_room}", id="chat-header")
                yield RichLog(id="chat-log", wrap=True, highlight=True, markup=True)

            # Правая панель - Пользователи
            with Vertical(id="users-panel"):
                yield Label("👥 Онлайн (0)", id="users-title")
                with VerticalScroll(id="user-list"):
                    yield Label("Загрузка...", classes="user-item")

        yield Input(
            placeholder="Введите сообщение или /pm <user> <text>",
            id="chat-input",
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        self.log_widget = self.query_one("#chat-log", RichLog)

        try:
            self.websocket = await websockets.connect(self.url)
            self.chat_manager = ChatFabric(self.websocket)

            success, message = await self.chat_manager.sign_in(
                self.username, self.password
            )

            if success:
                self.log_widget.write(
                    "[dim]╔══════════════════════════════╗[/dim]"
                )
                welcome = f"  ✓ Добро пожаловать, {self.username}!"
                self.log_widget.write(f"[bold green]{welcome}[/bold green]")
                self.log_widget.write(
                    "[dim]╚══════════════════════════════╝[/dim]\n"
                )
                await self.chat_manager.get_list_online_users()
                self.run_worker(self.listen_for_message)
            else:
                self.log_widget.write(f"[bold red]✗ Ошибка входа: {message}[/bold red]")
                self.exit("auth_failed")

        except Exception as e:
            self.log_widget.write(f"[bold red]✗ Ошибка подключения: {e}[/bold red]")
            self.exit("connection_failed")

    async def on_unmount(self) -> None:
        """Закрываем соединение при выходе"""
        if self.websocket:
            await self.websocket.close()

    async def action_refresh_users(self) -> None:
        if self.chat_manager:
            await self.chat_manager.get_list_online_users()
            msg = "🔄 Обновление списка пользователей..."
            self.log_widget.write(f"[dim]{msg}[/dim]")

    def action_switch_room(self) -> None:
        """Переключение между комнатами (пока просто визуально)"""
        current_idx = self.rooms.index(self.current_room)
        next_idx = (current_idx + 1) % len(self.rooms)
        self.current_room = self.rooms[next_idx]

        # Обновляем заголовок
        self.query_one("#chat-header", Label).update(f"💬 {self.current_room}")

        # Обновляем подсветку комнат
        for room in self.rooms:
            room_label = self.query_one(f"#room-{room}", Label)
            if room == self.current_room:
                room_label.set_classes("room-item-active")
            else:
                room_label.set_classes("room-item")

        msg = f"→ Переключено на комнату: {self.current_room}"
        self.log_widget.write(f"[dim]{msg}[/dim]")

    async def listen_for_message(self) -> None:
        """Слушает входящие сообщения от websocket и обновляет UI."""
        if not self.chat_manager:
            return

        retry_count = 0
        max_retries = 3

        while retry_count < max_retries:
            try:
                async for message_str in self.chat_manager.websocket:
                    message = ReceivedMessage.from_json(message_str)

                    if message.type == "new_message":
                        username = message.payload.get("username", "unknown")
                        text = message.payload.get("text", "")
                        from datetime import datetime

                        timestamp = datetime.now().strftime("%H:%M")
                        msg = (
                            f"[dim]{timestamp}[/dim] "
                            f"[bold yellow]{username}:[/bold yellow] {text}"
                        )
                        self.log_widget.write(msg)
                        self.log_widget.scroll_end(animate=False)

                    elif message.type == "private_message":
                        from_user = message.payload.get("from", "unknown")
                        text = message.payload.get("text", "")
                        from datetime import datetime

                        timestamp = datetime.now().strftime("%H:%M")
                        msg = (
                            f"[dim]{timestamp}[/dim] "
                            f"[bold magenta]🔒 ЛС от {from_user}:"
                            f"[/bold magenta] {text}"
                        )
                        self.log_widget.write(msg)
                        self.log_widget.scroll_end(animate=False)

                    elif message.type == "private_message_sent":
                        to_user = message.payload.get("to", "unknown")
                        text = message.payload.get("text", "")
                        from datetime import datetime

                        timestamp = datetime.now().strftime("%H:%M")
                        msg = f"{timestamp} Вы → {to_user}: {text}"
                        self.log_widget.write(f"[dim]{msg}[/dim]")
                        self.log_widget.scroll_end(animate=False)

                    elif message.type == "online_users":
                        self.online_users = message.payload.get("users", [])
                        self.update_users_list()
                        count = len(self.online_users)
                        msg = f"📊 {count} пользователей онлайн"
                        self.log_widget.write(f"[dim]{msg}[/dim]")

                    else:
                        msg = f"ℹ️  SERVER: {message.payload}"
                        self.log_widget.write(f"[dim]{msg}[/dim]")

                break  # Выход из цикла при нормальном завершении

            except websockets.ConnectionClosed:
                retry_count += 1
                msg = (
                    f"⚠️  Соединение потеряно. "
                    f"Попытка {retry_count}/{max_retries}..."
                )
                self.log_widget.write(f"[yellow]{msg}[/yellow]")
                if retry_count < max_retries:
                    await asyncio.sleep(2 ** retry_count)
                    try:
                        self.websocket = await websockets.connect(self.url)
                        self.chat_manager.websocket = self.websocket
                        msg = "✓ Переподключение успешно!"
                        self.log_widget.write(f"[green]{msg}[/green]")
                    except Exception:
                        continue

            except Exception as e:
                self.log_widget.write(f"[bold red]✗ Критическая ошибка: {e}[/bold red]")
                break

        if retry_count >= max_retries:
            msg = "✗ Не удалось восстановить соединение"
            self.log_widget.write(f"[bold red]{msg}[/bold red]")
            self.exit("connection_lost")

    def update_users_list(self) -> None:
        """Обновляет список пользователей в правой панели"""
        users_container = self.query_one("#user-list", VerticalScroll)
        users_container.remove_children()

        # Обновляем заголовок с количеством
        count = len(self.online_users)
        self.query_one("#users-title", Label).update(f"👥 Онлайн ({count})")

        # Добавляем пользователей
        for user in self.online_users:
            icon = "👤" if user != self.username else "⭐"
            user_label = Label(f"{icon} {user}", classes="user-item")
            users_container.mount(user_label)
            

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        message_text = event.value.strip()
        if not message_text or not self.chat_manager:
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")

        # Обработка команд
        if message_text.startswith("/pm "):
            parts = message_text.split(" ", 2)
            if len(parts) >= 3:
                recipient, text = parts[1], parts[2]
                await self.chat_manager.send_private_message(recipient, text)
            else:
                msg = "❌ Использование: /pm <username> <message>"
                self.log_widget.write(f"[red]{msg}[/red]")

        elif message_text.startswith("/users"):
            await self.chat_manager.get_list_online_users()

        elif message_text.startswith("/help"):
            self.log_widget.write("[bold cyan]📖 Доступные команды:[/bold cyan]")
            self.log_widget.write("  /pm <user> <text> - Отправить личное сообщение")
            self.log_widget.write("  /users - Обновить список пользователей")
            self.log_widget.write("  /help - Показать эту справку")
            self.log_widget.write("  Ctrl+R - Сменить комнату")
            self.log_widget.write("  F5 - Обновить пользователей")
            self.log_widget.write("  Q - Выход")

        else:
            # Обычное сообщение в комнату
            await self.chat_manager.send_message_room(
                message_text, self.current_room
            )
            # Отображаем свое сообщение
            msg = (
                f"[dim]{timestamp}[/dim] "
                f"[bold cyan]Вы:[/bold cyan] {message_text}"
            )
            self.log_widget.write(msg)
            self.log_widget.scroll_end(animate=False)

        self.query_one(Input).value = ""
