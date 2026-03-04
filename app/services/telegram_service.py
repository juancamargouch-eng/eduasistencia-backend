import asyncio
import os
from telethon import TelegramClient, functions, types
from sqlalchemy.orm import Session
from ..models.telegram import TelegramConfig
from ..models.student import Student
from ..models.attendance import AttendanceLog
from datetime import datetime

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
            # Check if identifier is phone (starts with + or digits only) or username
            is_phone = identifier.startswith('+') or identifier.isdigit()
            
            if is_phone:
                phone = identifier if identifier.startswith('+') else f"+{identifier}"
                print(f"DEBUG: Attempting to add contact by phone: {phone}")
                # Add as contact
                contact = types.InputPhoneContact(
                    client_id=0, # Any random long
                    phone=phone,
                    first_name=first_name,
                    last_name=""
                )
                result = await client(functions.contacts.ImportContactsRequest([contact]))
                if result.users:
                    user = result.users[0]
                    print(f"DEBUG: Contact imported. User ID: {user.id}")
                    return str(user.id)
                else:
                    print(f"DEBUG: Contact import request returned no users for {phone}")
            else:
                # Resolve username
                username = identifier.replace('@', '')
                print(f"DEBUG: Attempting to resolve username: {username}")
                result = await client(functions.contacts.ResolveUsernameRequest(username))
                if result.users:
                    user = result.users[0]
                    print(f"DEBUG: Username resolved. User ID: {user.id}")
                    return str(user.id)
                else:
                    print(f"DEBUG: Username resolution returned no users for {username}")
            
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
    async def send_attendance_notification(db: Session, student: Student, log: AttendanceLog):
        try:
            print(f"DEBUG: Iniciando proceso de notificación para {student.full_name}")
            
            # 1. Get Telegram Config
            config = db.query(TelegramConfig).filter(TelegramConfig.is_active == True).first()
            if not config:
                print("DEBUG: No hay configuración de Telegram activa en la DB.")
                return
                
            if not config.api_id or not config.api_hash:
                print(f"DEBUG: Configuración incompleta (ID/Hash faltante). ID: {config.api_id}")
                return

            print(f"DEBUG: Configuración encontrada. Usando modo: {'Usuario' if config.phone else 'Bot'}")

            # Check if we have at least user phone or bot token
            if not config.phone and not config.bot_token:
                print("DEBUG: Ni sesión de usuario ni token de bot disponibles.")
                return

            # 2. Check if student has telegram linked and notify enabled
            if not student.telegram_chat_id:
                print(f"DEBUG: El estudiante {student.full_name} no tiene chat_id configurado.")
                return
                
            if not student.notify_telegram:
                print(f"DEBUG: Las notificaciones están desactivadas para {student.full_name}.")
                return

            print(f"DEBUG: Preparando mensaje para chat_id: {student.telegram_chat_id}")

            # 3. Format message
            status_text = "PUNTUAL" if log.status == "PRESENT" else "TARDANZA"
            emoji = "✅" if log.status == "PRESENT" else "⚠️"
            
            time_str = log.timestamp.strftime("%H:%M:%S")
            message = (
                f"{emoji} <b>Notificación de Asistencia</b>\n\n"
                f"El estudiante <b>{student.full_name}</b> ha registrado su "
                f"{'entrada' if log.event_type == 'ENTRY' else 'salida'}.\n\n"
                f"📍 <b>Estado:</b> {status_text}\n"
                f"🕒 <b>Hora:</b> {time_str}\n"
                f"📅 <b>Fecha:</b> {log.timestamp.strftime('%d/%m/%Y')}"
            )

            # 4. Resolve Photo Path
            file_path = None
            if student.photo_url:
                # photo_url is typically "/static/students/filename.jpg"
                # Physical path is "backend/backend/static/students/filename.jpg"
                # __file__ is at backend/app/services/telegram_service.py
                # Root is dirname(dirname(dirname(abspath(__file__))))
                # __file__ is at backend/app/services/telegram_service.py
                root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                filename = os.path.basename(student.photo_url)
                
                # Constructing path to root/static/students/filename
                file_path = os.path.join(root_dir, "static", "students", filename)
                
                print(f"DEBUG: Buscando foto en path: {file_path}")
                
                if not os.path.exists(file_path):
                    print(f"DEBUG: Archivo de foto no encontrado físicamente en: {file_path}")
                    file_path = None
                else:
                    print(f"DEBUG: Foto encontrada. Tamaño: {os.path.getsize(file_path)} bytes")

            # 5. Send message (Async)
            # Prioritize telegram_user_id if we have it
            target_chat = student.telegram_user_id or student.telegram_chat_id
            
            success = await TelegramService.send_message(
                config.api_id, config.api_hash, config.bot_token, 
                target_chat, message,
                phone=config.phone,
                file_path=file_path
            )
            
            if success:
                print(f"DEBUG: Notificación enviada correctamente a {student.full_name}")
            else:
                print(f"DEBUG: Error al intentar enviar la notificación a {student.full_name}")
        except Exception as e:
            print(f"DEBUG CRITICAL ERROR en send_attendance_notification: {str(e)}")
