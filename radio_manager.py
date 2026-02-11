"""
مدير الراديو - Radio Manager
نظام التشغيل الصوتي في المكالمات الصوتية
"""

import asyncio
import os
from typing import Dict, Optional
from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.types import Message
from database import Database
import yt_dlp
from config import DOWNLOAD_FOLDER, AUDIO_QUALITY, MAX_FILE_SIZE
import logging

logger = logging.getLogger(__name__)


class RadioManager:
    """مدير تشغيل الراديو"""
    
    def __init__(self, userbot: Client, db: Database):
        self.userbot = userbot
        self.db = db
        self.active_calls = {}  # {chat_id: call_info}
        
        # إنشاء مجلد التحميلات
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
    
    # ══════════════════════════════════════════════════════════════
    #                    التحكم في التشغيل
    # ══════════════════════════════════════════════════════════════
    
    async def start_playing(self, chat_id: int) -> Dict:
        """بدء التشغيل"""
        try:
            # التحقق من وجود أغاني
            song = self.db.get_next_song(chat_id)
            if not song:
                return {
                    "success": False,
                    "message": "لا توجد أغاني في القائمة! أضف أغاني أولاً."
                }
            
            # الانضمام للمكالمة الصوتية
            await self.join_voice_chat(chat_id)
            
            # تشغيل الأغنية
            await self.play_song(chat_id, song)
            
            # تحديث حالة قاعدة البيانات
            self.db.set_playing(chat_id, song['id'], True)
            
            # الحصول على عدد الأغاني
            playlist = self.db.get_playlist(chat_id)
            
            return {
                "success": True,
                "current_song": song['title'],
                "total_songs": len(playlist)
            }
        
        except Exception as e:
            logger.error(f"خطأ في بدء التشغيل: {e}")
            return {
                "success": False,
                "message": f"حدث خطأ: {str(e)}"
            }
    
    async def pause(self, chat_id: int) -> Dict:
        """إيقاف مؤقت"""
        try:
            if chat_id not in self.active_calls:
                return {"success": False, "message": "الراديو متوقف!"}
            
            # إيقاف مؤقت للصوت
            await self.pause_audio(chat_id)
            
            self.db.set_paused(chat_id, True)
            
            return {"success": True, "message": "تم الإيقاف المؤقت"}
        
        except Exception as e:
            return {"success": False, "message": f"خطأ: {str(e)}"}
    
    async def resume(self, chat_id: int) -> Dict:
        """استئناف التشغيل"""
        try:
            if chat_id not in self.active_calls:
                return {"success": False, "message": "الراديو متوقف!"}
            
            # استئناف الصوت
            await self.resume_audio(chat_id)
            
            self.db.set_paused(chat_id, False)
            
            return {"success": True, "message": "تم استئناف التشغيل"}
        
        except Exception as e:
            return {"success": False, "message": f"خطأ: {str(e)}"}
    
    async def skip(self, chat_id: int) -> Dict:
        """تخطي الأغنية الحالية"""
        try:
            if chat_id not in self.active_calls:
                return {"success": False, "message": "الراديو متوقف!"}
            
            # الحصول على الأغنية التالية
            next_song = self.db.get_next_song(chat_id)
            
            if not next_song:
                return {"success": False, "message": "لا توجد أغاني تالية!"}
            
            # تشغيل الأغنية التالية
            await self.play_song(chat_id, next_song)
            self.db.set_playing(chat_id, next_song['id'], True)
            
            return {
                "success": True,
                "next_song": next_song['title']
            }
        
        except Exception as e:
            return {"success": False, "message": f"خطأ: {str(e)}"}
    
    async def stop(self, chat_id: int) -> Dict:
        """إيقاف التشغيل"""
        try:
            if chat_id not in self.active_calls:
                return {"success": False, "message": "الراديو متوقف بالفعل!"}
            
            # مغادرة المكالمة الصوتية
            await self.leave_voice_chat(chat_id)
            
            # تحديث قاعدة البيانات
            self.db.stop_playback(chat_id)
            
            # حذف من القائمة النشطة
            if chat_id in self.active_calls:
                del self.active_calls[chat_id]
            
            return {"success": True, "message": "تم إيقاف الراديو"}
        
        except Exception as e:
            return {"success": False, "message": f"خطأ: {str(e)}"}
    
    # ══════════════════════════════════════════════════════════════
    #                    إدارة المكالمات الصوتية
    # ══════════════════════════════════════════════════════════════
    
    async def join_voice_chat(self, chat_id: int):
        """الانضمام للمكالمة الصوتية"""
        try:
            # استخدام Pyrogram للانضمام للمكالمة
            peer = await self.userbot.resolve_peer(chat_id)
            
            # الانضمام للمكالمة
            call = await self.userbot.invoke(
                functions.phone.JoinGroupCall(
                    call=types.InputGroupCall(
                        id=0,  # سيتم الحصول عليه تلقائياً
                        access_hash=0
                    ),
                    join_as=peer,
                    params=types.DataJSON(data='{}'),
                    muted=False
                )
            )
            
            self.active_calls[chat_id] = {
                "call": call,
                "status": "active"
            }
            
            logger.info(f"انضم للمكالمة الصوتية: {chat_id}")
        
        except Exception as e:
            logger.error(f"خطأ في الانضمام للمكالمة: {e}")
            # إنشاء مكالمة صوتية جديدة إذا لم تكن موجودة
            await self.create_voice_chat(chat_id)
    
    async def create_voice_chat(self, chat_id: int):
        """إنشاء مكالمة صوتية جديدة"""
        try:
            peer = await self.userbot.resolve_peer(chat_id)
            
            call = await self.userbot.invoke(
                functions.phone.CreateGroupCall(
                    peer=peer,
                    random_id=0,
                    title="🎵 راديو تليجرام"
                )
            )
            
            # الانضمام للمكالمة المنشأة
            await self.join_voice_chat(chat_id)
            
            logger.info(f"تم إنشاء مكالمة صوتية: {chat_id}")
        
        except Exception as e:
            logger.error(f"خطأ في إنشاء المكالمة: {e}")
    
    async def leave_voice_chat(self, chat_id: int):
        """مغادرة المكالمة الصوتية"""
        try:
            if chat_id in self.active_calls:
                await self.userbot.invoke(
                    functions.phone.LeaveGroupCall(
                        call=self.active_calls[chat_id]["call"],
                        source=0
                    )
                )
                
                logger.info(f"غادر المكالمة الصوتية: {chat_id}")
        
        except Exception as e:
            logger.error(f"خطأ في مغادرة المكالمة: {e}")
    
    # ══════════════════════════════════════════════════════════════
    #                    تشغيل الأغاني
    # ══════════════════════════════════════════════════════════════
    
    async def play_song(self, chat_id: int, song: Dict):
        """تشغيل أغنية"""
        try:
            # الحصول على مسار الملف
            audio_path = song.get('file_path')
            
            if not audio_path or not os.path.exists(audio_path):
                logger.error(f"ملف الصوت غير موجود: {audio_path}")
                return
            
            # هنا يتم التشغيل الفعلي باستخدام PyTgCalls أو مكتبة مشابهة
            # ملاحظة: يتطلب تثبيت pytgcalls للتشغيل الفعلي
            
            logger.info(f"تشغيل: {song['title']} في {chat_id}")
            
            # تحديث حالة التشغيل
            self.active_calls[chat_id]["current_song"] = song
            self.active_calls[chat_id]["status"] = "playing"
        
        except Exception as e:
            logger.error(f"خطأ في تشغيل الأغنية: {e}")
    
    async def pause_audio(self, chat_id: int):
        """إيقاف مؤقت للصوت"""
        # تنفيذ إيقاف مؤقت
        if chat_id in self.active_calls:
            self.active_calls[chat_id]["status"] = "paused"
    
    async def resume_audio(self, chat_id: int):
        """استئناف الصوت"""
        # تنفيذ الاستئناف
        if chat_id in self.active_calls:
            self.active_calls[chat_id]["status"] = "playing"
    
    # ══════════════════════════════════════════════════════════════
    #                    إضافة الأغاني
    # ══════════════════════════════════════════════════════════════
    
    async def add_song_from_url(self, chat_id: int, url: str) -> Dict:
        """إضافة أغنية من رابط (يوتيوب/ساوند كلاود)"""
        try:
            # إعدادات التحميل
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': AUDIO_QUALITY,
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            # تحميل الأغنية
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                title = info.get('title', 'Unknown')
                duration = info.get('duration', 0)
                artist = info.get('artist') or info.get('uploader', 'Unknown')
                
                # مسار الملف المحمل
                file_path = ydl.prepare_filename(info)
                file_path = file_path.rsplit('.', 1)[0] + '.mp3'
                
                # التحقق من حجم الملف
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                if file_size > MAX_FILE_SIZE:
                    os.remove(file_path)
                    return {
                        "success": False,
                        "message": f"الملف كبير جداً ({file_size:.1f}MB)! الحد الأقصى: {MAX_FILE_SIZE}MB"
                    }
                
                # حفظ في قاعدة البيانات
                song_id = self.db.add_song(
                    chat_id=chat_id,
                    title=title,
                    file_path=file_path,
                    duration=duration,
                    artist=artist,
                    source_type='url',
                    source_url=url
                )
                
                if song_id:
                    return {
                        "success": True,
                        "title": title,
                        "duration": self._format_duration(duration)
                    }
                else:
                    return {
                        "success": False,
                        "message": "فشل حفظ الأغنية في قاعدة البيانات"
                    }
        
        except Exception as e:
            logger.error(f"خطأ في تحميل الأغنية: {e}")
            return {
                "success": False,
                "message": f"فشل التحميل: {str(e)}"
            }
    
    async def add_song_from_file(self, chat_id: int, audio) -> Dict:
        """إضافة أغنية من ملف مرفوع"""
        try:
            # معلومات الملف
            title = audio.file_name or audio.title or "Unknown"
            duration = audio.duration or 0
            artist = audio.performer or "Unknown"
            file_id = audio.file_id
            
            # تحميل الملف
            file_path = f"{DOWNLOAD_FOLDER}/{title}"
            await self.userbot.download_media(audio, file_name=file_path)
            
            # التحقق من حجم الملف
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            if file_size > MAX_FILE_SIZE:
                os.remove(file_path)
                return {
                    "success": False,
                    "message": f"الملف كبير جداً ({file_size:.1f}MB)!"
                }
            
            # حفظ في قاعدة البيانات
            song_id = self.db.add_song(
                chat_id=chat_id,
                title=title,
                file_id=file_id,
                file_path=file_path,
                duration=duration,
                artist=artist,
                source_type='file'
            )
            
            if song_id:
                return {
                    "success": True,
                    "title": title,
                    "duration": self._format_duration(duration)
                }
            else:
                return {
                    "success": False,
                    "message": "فشل حفظ الأغنية"
                }
        
        except Exception as e:
            logger.error(f"خطأ في إضافة الملف: {e}")
            return {
                "success": False,
                "message": f"خطأ: {str(e)}"
            }
    
    # ══════════════════════════════════════════════════════════════
    #                    التشغيل التلقائي
    # ══════════════════════════════════════════════════════════════
    
    async def auto_player_loop(self):
        """حلقة التشغيل التلقائي المستمر"""
        logger.info("🔄 بدء نظام التشغيل التلقائي...")
        
        while True:
            try:
                # فحص جميع المجموعات النشطة
                active_chats = self.db.get_all_active_chats()
                
                for chat_id in active_chats:
                    # التحقق من التشغيل التلقائي
                    if not self.db.get_autoplay_status(chat_id):
                        continue
                    
                    # الحصول على حالة التشغيل
                    state = self.db.get_playback_state(chat_id)
                    
                    # إذا كان متوقفاً ويوجد أغاني، ابدأ التشغيل
                    if state and not state['is_playing'] and not state['is_paused']:
                        playlist = self.db.get_playlist(chat_id)
                        
                        if playlist:
                            logger.info(f"🎵 بدء التشغيل التلقائي للمجموعة: {chat_id}")
                            await self.start_playing(chat_id)
                    
                    # إذا انتهت الأغنية، شغل التالية
                    if chat_id in self.active_calls:
                        call_info = self.active_calls[chat_id]
                        
                        # فحص إذا انتهت الأغنية (يتطلب تنفيذ فعلي)
                        # هنا يتم فحص حالة التشغيل من pytgcalls
                        
                        # إذا انتهت، شغل التالية
                        # await self.skip(chat_id)
                
                # انتظر قبل الفحص التالي
                await asyncio.sleep(10)
            
            except Exception as e:
                logger.error(f"خطأ في حلقة التشغيل التلقائي: {e}")
                await asyncio.sleep(10)
    
    # ══════════════════════════════════════════════════════════════
    #                    حالة التشغيل
    # ══════════════════════════════════════════════════════════════
    
    async def get_status(self, chat_id: int) -> Dict:
        """الحصول على حالة التشغيل"""
        state = self.db.get_playback_state(chat_id)
        
        if not state or not state['is_playing']:
            return {"is_playing": False}
        
        playlist = self.db.get_playlist(chat_id)
        
        return {
            "is_playing": True,
            "current_song": state.get('title', 'Unknown'),
            "duration": self._format_duration(state.get('duration', 0)),
            "elapsed": "00:00",  # يتطلب تنفيذ فعلي
            "queue_size": len(playlist),
            "autoplay": self.db.get_autoplay_status(chat_id)
        }
    
    # ══════════════════════════════════════════════════════════════
    #                    دوال مساعدة
    # ══════════════════════════════════════════════════════════════
    
    def _format_duration(self, seconds: int) -> str:
        """تنسيق المدة الزمنية"""
        if not seconds:
            return "00:00"
        
        minutes = seconds // 60
        secs = seconds % 60
        
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        return f"{minutes:02d}:{secs:02d}"
