import asyncio
import os
from telethon import TelegramClient, functions, types
from sqlalchemy.orm import Session
from ..models.telegram import TelegramConfig
from ..models.student import Student
from ..models.attendance import AttendanceLog
from datetime import datetime
from .storage_service import StorageService

# Global client to reuse connection
_telegram_client = None

class TelegramService:
    @staticmethod
    async def get_client(api_id: str, api_hash: str, bot_token: str = None):
        global _telegram_client
        
        # Ensure sessions directory exists using absolute path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sessions_dir = os.path.join(base_dir, "sessions")
        os.makedirs(sessions_dir, exist_ok=True)
        session_path = os.path.join(sessions_dir, "user_session")
        
        # Re-create client if credentials changed
        if _telegram_client is not None:
            if str(_telegram_client.api_id) != str(api_id) or _telegram_client.api_hash != api_hash:
                await _telegram_client.disconnect()
                _telegram_client = None

        if _telegram_client is None:
            _telegram_client = TelegramClient(session_path, int(api_id), api_hash)
            await _telegram_client.connect()
            if bot_token and not await _telegram_client.is_user_authorized():
                await _telegram_client.start(bot_token=bot_token)
        elif not _telegram_client.is_connected():
            await _telegram_client.connect()
            
        return _telegram_client

    @staticmethod
    async def send_code_request(api_id: str, api_hash: str, phone: str):
        client = await TelegramService.get_client(api_id, api_hash)
        try:
            sent_code = await client.send_code_request(phone)
            return sent_code.phone_code_hash
        except Exception as e:
            print(f"Error sending MTProto code: {e}")
            raise e

    @staticmethod
    async def resolve_and_add_contact(api_id: str, api_hash: str, identifier: str, first_name: str):
        """
        Attempts to add a contact by phone or resolve by username.
        Returns the permanent user_id (string).
        """
        client = await TelegramService.get_client(api_id, api_hash)
        if not await client.is_user_authorized():
            print("DEBUG: Telegram client not authorized. Cannot resolve/add contact.")
            return None
            
        try:
            # Normalization: Remove spaces, dashes, etc.
            clean_id = identifier.strip().replace(" ", "").replace("-", "")
            
            # Check if identifier is phone or username
            is_probably_phone = clean_id.startswith('+') or clean_id.isdigit()
            
            if is_probably_phone:
                phone = clean_id
                # Peru logic: if 9 digits and doesn't start with +, assume +51
                if len(phone) == 9 and not phone.startswith('+'):
                    phone = f"+51{phone}"
                elif not phone.startswith('+'):
                    phone = f"+{phone}"
                
                print(f"DEBUG: Intentando agregar contacto por teléfono: {phone}")
                
                # Import Contact
                import random
                contact = types.InputPhoneContact(
                    client_id=random.getrandbits(31), 
                    phone=phone,
                    first_name=first_name,
                    last_name=""
                )
                
                result = await client(functions.contacts.ImportContactsRequest([contact]))
                
                if result.users:
                    user = result.users[0]
                    print(f"DEBUG: Contacto importado exitosamente. User ID: {user.id}")
                    return str(user.id)
                else:
                    # Alternativa: intentar obtener entidad directamente si ya existía
                    try:
                        user = await client.get_entity(phone)
                        print(f"DEBUG: Entidad obtenida directamente. User ID: {user.id}")
                        return str(user.id)
                    except:
                        print(f"DEBUG: No se pudo encontrar usuario para el teléfono {phone}")
            else:
                # Resolve username
                username = clean_id.replace('@', '')
                print(f"DEBUG: Intentando resolver username: {username}")
                result = await client(functions.contacts.ResolveUsernameRequest(username))
                if result.users:
                    user = result.users[0]
                    print(f"DEBUG: Username resuelto. User ID: {user.id}")
                    return str(user.id)
                else:
                    print(f"DEBUG: No se pudo resolver el username {username}")
            
            return None
        except Exception as e:
            print(f"Error resolving/adding contact for {identifier}: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    async def sign_in_user(api_id: str, api_hash: str, phone: str, code: str, phone_code_hash: str, password: str = None):
        client = await TelegramService.get_client(api_id, api_hash)
        try:
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash, password=password)
            return await client.is_user_authorized()
        except Exception as e:
            print(f"Error signing in MTProto user: {e}")
            raise e

    @staticmethod
    async def send_message(api_id: str, api_hash: str, bot_token: str, chat_id: str, message: str, phone: str = None, file_path: str = None):
        try:
            # If phone exists, we prioritize user login session
            client = await TelegramService.get_client(api_id, api_hash, bot_token if not phone else None)
            
            if not await client.is_user_authorized():
                print(f"Telegram client not authorized ({'User' if phone else 'Bot'}). Skipping message.")
                return False

            print(f"Sending Telegram message to {chat_id} using {'User session' if phone else 'Bot token'}")

            # Use chat_id as int if possible, Telethon likes it
            try:
                target = int(chat_id)
            except:
                target = chat_id
                # Ensure usernames start with @ if they are not plain numbers
                if isinstance(target, str) and not target.startswith('@') and not target.startswith('+') and not target.isdigit():
                    target = f"@{target}"
                
            if file_path and os.path.exists(file_path):
                await client.send_file(target, file_path, caption=message, parse_mode='html')
            else:
                await client.send_message(target, message, parse_mode='html')
                
            print(f"Successfully sent message to {chat_id}")
            return True
        except Exception as e:
            print(f"Error sending Telethon message: {e}")
            return False

    @staticmethod
    async def broadcast_announcement(db: Session, announcement_id: int):
        """
        Envío masivo de un comunicado a los estudiantes/padres correspondientes vía Telegram.
        """
        try:
            from ..models.announcement import Announcement
            from ..models.student import Student

            # 1. Obtener comunicado y autor
            ann = db.query(Announcement).filter(Announcement.id == announcement_id).first()
            if not ann: return
            
            author = ann.author
            
            # 2. Configuración de Telegram
            config = db.query(TelegramConfig).filter(TelegramConfig.is_active == True).first()
            if not config or not config.api_id or not config.api_hash:
                print("DEBUG: No hay configuración de Telegram activa para el broadcast.")
                return

            # 3. Construir Cabecera de Identidad
            if author.is_superuser:
                header = "🏢 <b>COMUNICADO INSTITUCIONAL</b>"
            elif author.role == "DIRECTOR":
                header = f"👨‍💼 <b>COMUNICADO DE DIRECCIÓN</b>\n👤 <i>{author.full_name}</i>"
            elif author.role == "ADMIN":
                header = "🏢 <b>COMUNICADO DE ADMINISTRACIÓN</b>"
            elif author.role == "DOCENTE":
                header = f"👨‍🏫 <b>COMUNICADO DEL DOCENTE</b>\n👤 <i>{author.full_name}</i>"
            else:
                header = "📩 <b>NUEVO COMUNICADO</b>"

            now_str = datetime.now().strftime("%d/%m/%Y")
            message = (
                f"{header}\n"
                f"📅 {now_str}\n"
                f"📌 <b>{ann.title}</b>\n\n"
                f"{ann.content}"
            )

            # 4. Filtrar destinatarios
            query = db.query(Student).filter(Student.is_active == True, Student.notify_telegram == True)
            
            if ann.target_grade and ann.target_grade != "TODOS":
                query = query.filter(Student.grade == ann.target_grade)
            if ann.target_section and ann.target_section != "TODOS":
                query = query.filter(Student.section == ann.target_section)
                
            recipients = query.all()
            print(f"DEBUG: Iniciando envío masivo de comunicado {ann.id} a {len(recipients)} destinatarios.")

            # 5. Envío Masivo (Bucle controlado)
            count = 0
            for student in recipients:
                target = student.telegram_user_id or student.telegram_chat_id
                if not target: continue
                
                success = await TelegramService.send_message(
                    config.api_id, config.api_hash, config.bot_token,
                    target, message, phone=config.phone
                )
                if success: count += 1
                
                # Pequeña pausa para evitar rate-limits de Telegram en envíos grandes
                if len(recipients) > 10:
                    await asyncio.sleep(0.1)

            print(f"DEBUG: Broadcast finalizado. {count}/{len(recipients)} mensajes enviados.")

        except Exception as e:
            print(f"DEBUG CRITICAL ERROR en broadcast_announcement: {str(e)}")

    @staticmethod
    async def send_attendance_notification(db: Session, student: Student, log: AttendanceLog):
        try:
            # 3. Format message safely
            def get_data(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)

            full_name = get_data(student, "full_name", "Estudiante")
            chat_id = get_data(student, "telegram_chat_id")
            user_id = get_data(student, "telegram_user_id")
            notify = get_data(student, "notify_telegram", True)
            photo = get_data(student, "photo_url")

            # 1. Get Telegram Config
            config = db.query(TelegramConfig).filter(TelegramConfig.is_active == True).first()
            if not config:
                print("DEBUG: No hay configuración de Telegram activa en la DB.")
                return
                
            if not config.api_id or not config.api_hash:
                print(f"DEBUG: Configuración incompleta (ID/Hash faltante). ID: {config.api_id}")
                return

            # 2. Check if student has telegram linked and notify enabled
            if not chat_id:
                print(f"DEBUG: El estudiante {full_name} no tiene chat_id configurado.")
                return
                
            if not notify:
                print(f"DEBUG: Las notificaciones están desactivadas para {full_name}.")
                return

            print(f"DEBUG: Preparando mensaje para chat_id: {chat_id}")

            # 3. Format message contents
            is_entry = log.event_type == 'ENTRY'
            
            if is_entry:
                status_text = "PUNTUAL" if log.status == "PRESENT" else "TARDANZA"
                emoji = "✅" if log.status == "PRESENT" else "⚠️"
                event_name = "ENTRADA"
            else:
                status_text = "SALIDA REGISTRADA"
                emoji = "🚪"
                event_name = "SALIDA"
            
            time_str = log.timestamp.strftime("%H:%M:%S")
            message = (
                f"{emoji} <b>Notificación de {event_name.capitalize()}</b>\n\n"
                f"El estudiante <b>{full_name}</b> ha registrado su "
                f"<b>{event_name.lower()}</b>.\n\n"
                f"📍 <b>Estado:</b> {status_text}\n"
                f"🕒 <b>Hora:</b> {time_str}\n"
                f"📅 <b>Fecha:</b> {log.timestamp.strftime('%d/%m/%Y')}"
            )

            # 4. Resolve Photo Path (S3)
            file_path = None
            is_temp_file = False
            
            if photo:
                if not photo.startswith("http"):
                    file_path = StorageService.download_to_temp_file(photo)
                    if file_path:
                        is_temp_file = True

            # 5. Send message (Async)
            target_chat = user_id or chat_id
            
            try:
                success = await TelegramService.send_message(
                    config.api_id, config.api_hash, config.bot_token, 
                    target_chat, message,
                    phone=config.phone,
                    file_path=file_path
                )
            finally:
                # Cleanup temp file
                if is_temp_file and file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
            
            if success:
                print(f"DEBUG: Notificación enviada correctamente a {full_name}")
            else:
                print(f"DEBUG: Error al intentar enviar la notificación a {full_name}")
        except Exception as e:
            print(f"DEBUG CRITICAL ERROR en send_attendance_notification: {str(e)}")
