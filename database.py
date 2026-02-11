"""
نظام قاعدة البيانات - Database System
"""

import sqlite3
from datetime import datetime
import json
import random
from typing import List, Dict, Optional


class Database:
    """نظام إدارة قاعدة البيانات"""
    
    def __init__(self, db_file: str = "radio_bot.db"):
        self.db_file = db_file
        self.init_database()
    
    def get_connection(self):
        """إنشاء اتصال بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """إنشاء جداول قاعدة البيانات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول المجموعات/القنوات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                chat_title TEXT,
                is_active BOOLEAN DEFAULT 1,
                autoplay BOOLEAN DEFAULT 1,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_plays INTEGER DEFAULT 0
            )
        """)
        
        # جدول الأغاني
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                title TEXT NOT NULL,
                file_id TEXT,
                file_path TEXT,
                duration INTEGER,
                artist TEXT,
                source_type TEXT,
                source_url TEXT,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                play_count INTEGER DEFAULT 0,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
            )
        """)
        
        # جدول حالة التشغيل
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS playback_state (
                chat_id INTEGER PRIMARY KEY,
                current_song_id INTEGER,
                is_playing BOOLEAN DEFAULT 0,
                is_paused BOOLEAN DEFAULT 0,
                position INTEGER DEFAULT 0,
                last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                FOREIGN KEY (current_song_id) REFERENCES songs(id)
            )
        """)
        
        # جدول الإحصائيات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                song_id INTEGER,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (chat_id) REFERENCES chats(chat_id),
                FOREIGN KEY (song_id) REFERENCES songs(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ══════════════════════════════════════════════════════════════
    #                    إدارة المجموعات/القنوات
    # ══════════════════════════════════════════════════════════════
    
    def add_chat(self, chat_id: int, chat_title: str) -> bool:
        """إضافة مجموعة/قناة جديدة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO chats (chat_id, chat_title)
                VALUES (?, ?)
            """, (chat_id, chat_title))
            
            # إضافة حالة تشغيل افتراضية
            cursor.execute("""
                INSERT OR IGNORE INTO playback_state (chat_id)
                VALUES (?)
            """, (chat_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في إضافة المجموعة: {e}")
            return False
        finally:
            conn.close()
    
    def is_chat_active(self, chat_id: int) -> bool:
        """التحقق من تفعيل المجموعة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT is_active FROM chats WHERE chat_id = ?
        """, (chat_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return bool(result and result['is_active'])
    
    def get_all_active_chats(self) -> List[int]:
        """الحصول على جميع المجموعات النشطة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chat_id FROM chats WHERE is_active = 1
        """)
        
        chats = [row['chat_id'] for row in cursor.fetchall()]
        conn.close()
        
        return chats
    
    # ══════════════════════════════════════════════════════════════
    #                    إدارة الأغاني
    # ══════════════════════════════════════════════════════════════
    
    def add_song(self, chat_id: int, title: str, file_id: str = None,
                 file_path: str = None, duration: int = 0, artist: str = None,
                 source_type: str = "file", source_url: str = None,
                 added_by: int = None) -> Optional[int]:
        """إضافة أغنية جديدة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO songs (
                    chat_id, title, file_id, file_path, duration,
                    artist, source_type, source_url, added_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (chat_id, title, file_id, file_path, duration,
                  artist, source_type, source_url, added_by))
            
            song_id = cursor.lastrowid
            conn.commit()
            return song_id
        except Exception as e:
            print(f"خطأ في إضافة الأغنية: {e}")
            return None
        finally:
            conn.close()
    
    def get_playlist(self, chat_id: int) -> List[Dict]:
        """الحصول على قائمة التشغيل"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                s.*,
                CASE WHEN ps.current_song_id = s.id AND ps.is_playing = 1 
                     THEN 1 ELSE 0 END as is_playing
            FROM songs s
            LEFT JOIN playback_state ps ON ps.chat_id = s.chat_id
            WHERE s.chat_id = ?
            ORDER BY s.added_date DESC
        """, (chat_id,))
        
        songs = []
        for row in cursor.fetchall():
            songs.append({
                'id': row['id'],
                'title': row['title'],
                'duration': self._format_duration(row['duration']),
                'artist': row['artist'] or 'غير معروف',
                'file_id': row['file_id'],
                'file_path': row['file_path'],
                'source_type': row['source_type'],
                'play_count': row['play_count'],
                'is_playing': bool(row['is_playing'])
            })
        
        conn.close()
        return songs
    
    def get_next_song(self, chat_id: int) -> Optional[Dict]:
        """الحصول على الأغنية التالية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # الحصول على الأغنية الحالية
        cursor.execute("""
            SELECT current_song_id FROM playback_state WHERE chat_id = ?
        """, (chat_id,))
        
        current = cursor.fetchone()
        current_id = current['current_song_id'] if current else None
        
        # الحصول على الأغنية التالية
        if current_id:
            cursor.execute("""
                SELECT * FROM songs 
                WHERE chat_id = ? AND id > ?
                ORDER BY id ASC LIMIT 1
            """, (chat_id, current_id))
        else:
            cursor.execute("""
                SELECT * FROM songs 
                WHERE chat_id = ?
                ORDER BY id ASC LIMIT 1
            """, (chat_id,))
        
        song = cursor.fetchone()
        
        # إذا لم توجد، ارجع للأولى (التشغيل التلقائي)
        if not song:
            cursor.execute("""
                SELECT * FROM songs 
                WHERE chat_id = ?
                ORDER BY id ASC LIMIT 1
            """, (chat_id,))
            song = cursor.fetchone()
        
        conn.close()
        
        if song:
            return dict(song)
        return None
    
    def remove_song(self, chat_id: int, song_index: int) -> bool:
        """حذف أغنية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # الحصول على ID الأغنية
            cursor.execute("""
                SELECT id FROM songs 
                WHERE chat_id = ?
                ORDER BY added_date DESC
                LIMIT 1 OFFSET ?
            """, (chat_id, song_index))
            
            song = cursor.fetchone()
            if not song:
                return False
            
            # حذف الأغنية
            cursor.execute("""
                DELETE FROM songs WHERE id = ?
            """, (song['id'],))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في حذف الأغنية: {e}")
            return False
        finally:
            conn.close()
    
    def shuffle_playlist(self, chat_id: int) -> bool:
        """خلط قائمة التشغيل"""
        songs = self.get_playlist(chat_id)
        if not songs:
            return False
        
        random.shuffle(songs)
        
        # إعادة ترتيب الأغاني
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for i, song in enumerate(songs):
                cursor.execute("""
                    UPDATE songs SET added_date = datetime('now', '-{} seconds')
                    WHERE id = ?
                """.format(i), (song['id'],))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"خطأ في خلط القائمة: {e}")
            return False
        finally:
            conn.close()
    
    # ══════════════════════════════════════════════════════════════
    #                    إدارة حالة التشغيل
    # ══════════════════════════════════════════════════════════════
    
    def set_playing(self, chat_id: int, song_id: int, is_playing: bool = True):
        """تعيين حالة التشغيل"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE playback_state 
            SET current_song_id = ?, is_playing = ?, is_paused = 0,
                last_update = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        """, (song_id, is_playing, chat_id))
        
        # تحديث عداد التشغيل
        if is_playing:
            cursor.execute("""
                UPDATE songs SET play_count = play_count + 1
                WHERE id = ?
            """, (song_id,))
        
        conn.commit()
        conn.close()
    
    def set_paused(self, chat_id: int, is_paused: bool):
        """إيقاف مؤقت"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE playback_state 
            SET is_paused = ?, last_update = CURRENT_TIMESTAMP
            WHERE chat_id = ?
        """, (is_paused, chat_id))
        
        conn.commit()
        conn.close()
    
    def get_playback_state(self, chat_id: int) -> Optional[Dict]:
        """الحصول على حالة التشغيل"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ps.*, s.title, s.duration
            FROM playback_state ps
            LEFT JOIN songs s ON s.id = ps.current_song_id
            WHERE ps.chat_id = ?
        """, (chat_id,))
        
        state = cursor.fetchone()
        conn.close()
        
        if state:
            return dict(state)
        return None
    
    def stop_playback(self, chat_id: int):
        """إيقاف التشغيل"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE playback_state 
            SET is_playing = 0, is_paused = 0, current_song_id = NULL
            WHERE chat_id = ?
        """, (chat_id,))
        
        conn.commit()
        conn.close()
    
    # ══════════════════════════════════════════════════════════════
    #                    إعدادات التشغيل التلقائي
    # ══════════════════════════════════════════════════════════════
    
    def get_autoplay_status(self, chat_id: int) -> bool:
        """الحصول على حالة التشغيل التلقائي"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT autoplay FROM chats WHERE chat_id = ?
        """, (chat_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        return bool(result and result['autoplay'])
    
    def set_autoplay(self, chat_id: int, enabled: bool):
        """تفعيل/تعطيل التشغيل التلقائي"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE chats SET autoplay = ? WHERE chat_id = ?
        """, (enabled, chat_id))
        
        conn.commit()
        conn.close()
    
    # ══════════════════════════════════════════════════════════════
    #                    دوال مساعدة
    # ══════════════════════════════════════════════════════════════
    
    def _format_duration(self, seconds: int) -> str:
        """تنسيق المدة الزمنية"""
        if not seconds:
            return "غير محدد"
        
        minutes = seconds // 60
        secs = seconds % 60
        
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        
        return f"{minutes:02d}:{secs:02d}"
    
    def get_statistics(self, chat_id: int) -> Dict:
        """الحصول على الإحصائيات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # إجمالي الأغاني
        cursor.execute("""
            SELECT COUNT(*) as total FROM songs WHERE chat_id = ?
        """, (chat_id,))
        total_songs = cursor.fetchone()['total']
        
        # إجمالي التشغيلات
        cursor.execute("""
            SELECT SUM(play_count) as total FROM songs WHERE chat_id = ?
        """, (chat_id,))
        total_plays = cursor.fetchone()['total'] or 0
        
        # الأغنية الأكثر تشغيلاً
        cursor.execute("""
            SELECT title, play_count FROM songs 
            WHERE chat_id = ? 
            ORDER BY play_count DESC LIMIT 1
        """, (chat_id,))
        most_played = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_songs': total_songs,
            'total_plays': total_plays,
            'most_played': dict(most_played) if most_played else None
        }
