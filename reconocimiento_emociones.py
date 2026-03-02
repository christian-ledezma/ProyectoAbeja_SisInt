"""
Módulo de reconocimiento de emociones por voz y síntesis de voz (TTS).

Usa SpeechRecognition para capturar audio del micrófono,
transcribe a texto y detecta emociones mediante palabras clave en español.
Usa pyttsx3 para síntesis de voz offline (espeak en Linux).

Dependencias:
    pip install SpeechRecognition PyAudio pyttsx3
    (Linux: sudo apt install portaudio19-dev espeak antes de PyAudio/pyttsx3)
"""

import threading
import queue
import subprocess
import shutil

try:
    import speech_recognition as sr
    SR_DISPONIBLE = True
except ImportError:
    SR_DISPONIBLE = False
    print("WARNING: Instala SpeechRecognition → pip install SpeechRecognition")

try:
    import pyttsx3
    TTS_DISPONIBLE = True
except ImportError:
    TTS_DISPONIBLE = False

# Detectar espeak-ng o espeak como fallback
_ESPEAK_CMD = shutil.which("espeak-ng") or shutil.which("espeak")
ESPEAK_DISPONIBLE = _ESPEAK_CMD is not None


# ──────────────────────────────────────────────────
#  Mapa de emociones → palabras clave en español
# ──────────────────────────────────────────────────
EMOCIONES = {
    "ira": {
        "keywords": [
            "enojado", "enojada", "furioso", "furiosa", "rabia", "ira",
            "molesto", "molesta", "enfadado", "enfadada", "odio", "coraje",
            "furia", "irritado", "irritada", "rabioso", "rabiosa", "enojo",
        ],
        "zona": "Zona de Calma",
        "consejo": "Respira profundo, todo estará bien.",
    },
    "alegria": {
        "keywords": [
            "feliz", "contento", "contenta", "alegre", "alegría", "bien",
            "genial", "fantástico", "increíble", "maravilloso", "emocionado",
            "emocionada", "divertido", "divertida", "super", "excelente",
            "sonrisa", "risa", "reír", "alegria", "happy",
        ],
        "zona": "Zona de Celebración",
        "consejo": "¡Qué bueno! Compartir la alegría la hace más grande.",
    },
    "verguenza": {
        "keywords": [
            "vergüenza", "avergonzado", "avergonzada", "pena", "bochorno",
            "tímido", "tímida", "nervioso", "nerviosa", "inseguro",
            "insegura", "timidez", "penoso", "penosa", "verguenza",
        ],
        "zona": "Zona de Confianza",
        "consejo": "Todos sentimos vergüenza a veces, ¡eres valiente!",
    },
    "tristeza": {
        "keywords": [
            "triste", "tristeza", "llorar", "solo", "sola", "soledad",
            "mal", "deprimido", "deprimida", "llorando", "lloro",
            "melancolía", "melancólico", "desanimado", "desanimada",
            "aburrido", "aburrida",
        ],
        "zona": "Zona de Juego",
        "consejo": "Está bien sentirse triste, aquí estoy para ti.",
    },
}

# Nombres legibles para mostrar al usuario
NOMBRE_LEGIBLE = {
    "ira": "ira",
    "alegria": "alegría",
    "verguenza": "vergüenza",
    "tristeza": "tristeza",
}


class ReconocedorEmociones:
    """
    Captura voz del micrófono, transcribe con Google Web Speech API
    y detecta la emoción dominante mediante palabras clave.

    Estados posibles:
        idle      – esperando acción del usuario
        listening – capturando audio
        processing – transcribiendo
        done      – emoción detectada (ver .emocion)
        error     – ocurrió un problema (ver .mensaje_error)
    """

    def __init__(self):
        if SR_DISPONIBLE:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
        else:
            self.recognizer = None

        self.estado: str = "idle"
        self.texto: str = ""
        self.emocion: str | None = None
        self.mensaje_error: str = ""
        self._thread: threading.Thread | None = None

    # ────────────────── API pública ──────────────────

    def iniciar_escucha(self):
        """Lanza la captura de audio en un hilo separado (no bloqueante)."""
        if not SR_DISPONIBLE:
            self.estado = "error"
            self.mensaje_error = "SpeechRecognition no está instalado"
            return

        if self.estado in ("listening", "processing"):
            return

        self.estado = "listening"
        self.texto = ""
        self.emocion = None
        self.mensaje_error = ""
        self._thread = threading.Thread(target=self._escuchar, daemon=True)
        self._thread.start()

    def reset(self):
        """Vuelve al estado idle."""
        self.estado = "idle"
        self.texto = ""
        self.emocion = None
        self.mensaje_error = ""

    # ────────────────── Internos ──────────────────

    def _escuchar(self):
        try:
            mic = sr.Microphone()
            with mic as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(
                    source, timeout=6, phrase_time_limit=10
                )

            self.estado = "processing"
            texto = self.recognizer.recognize_google(audio, language="es-ES")
            self.texto = texto.lower()
            print(f"[Reconocimiento] Texto: {self.texto}")

            self.emocion = self._detectar_emocion(self.texto)
            if self.emocion:
                self.estado = "done"
                print(f"[Reconocimiento] Emoción: {self.emocion}")
            else:
                self.estado = "error"
                self.mensaje_error = (
                    "No detecté una emoción clara. "
                    "¿Estás triste, enojado, alegre o avergonzado?"
                )

        except sr.WaitTimeoutError:
            self.estado = "error"
            self.mensaje_error = "Presiona el botón cuando quieras hablar"
        except sr.UnknownValueError:
            self.estado = "error"
            self.mensaje_error = (
                "No entendí bien, ¿puedes repetirlo más despacio?"
            )
        except sr.RequestError:
            self.estado = "error"
            self.mensaje_error = "Error de conexión. Intenta de nuevo."
        except Exception as exc:
            self.estado = "error"
            self.mensaje_error = f"Error: {exc}"
            print(f"[Reconocimiento] Excepción: {exc}")

    @staticmethod
    def _detectar_emocion(texto: str) -> str | None:
        """Busca la primera palabra clave que coincida en el texto."""
        for emocion, datos in EMOCIONES.items():
            for keyword in datos["keywords"]:
                if keyword in texto:
                    return emocion
        return None


# ──────────────────────────────────────────────────
#  Síntesis de voz (TTS) — pyttsx3 con fallback a espeak-ng
# ──────────────────────────────────────────────────
class Hablador:
    """
    Síntesis de voz en un hilo dedicado.

    Intenta usar pyttsx3 primero. Si falla (error común con espeak-ng
    reciente), cae automáticamente a llamar espeak-ng/espeak directamente
    via subprocess — sin dependencias extra.

    Uso:
        hablador = Hablador()      # arranca el hilo
        hablador.decir("Hola")     # no bloqueante
        hablador.detener()         # al cerrar el programa
    """

    def __init__(self, rate: int = 155, volume: float = 1.0):
        self._cola: queue.Queue[tuple[str, callable] | None] = queue.Queue()
        self._rate = rate
        self._volume = volume
        self._backend: str = "none"       # "pyttsx3" | "espeak" | "none"
        self._engine = None
        self._hilo = threading.Thread(target=self._worker, daemon=True)
        self._hilo.start()

    # ────────────────── API pública ──────────────────

    def decir(self, texto: str, al_terminar: callable = None):
        """Encola un mensaje para ser hablado (no bloqueante).
        Si hay un mensaje anterior aún sonando, este lo reemplaza.
        *al_terminar* se ejecuta justo después de que el TTS termine."""
        while not self._cola.empty():
            try:
                self._cola.get_nowait()
            except queue.Empty:
                break
        self._cola.put((texto, al_terminar))

    def detener(self):
        """Señala al hilo worker que termine."""
        # None puro (no tupla) es la señal de cierre
        self._cola.put(None)

    # ────────────────── Inicialización ──────────────────

    def _init_pyttsx3(self) -> bool:
        """Intenta inicializar pyttsx3. Devuelve True si tuvo éxito."""
        if not TTS_DISPONIBLE:
            return False
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self._rate)
            engine.setProperty('volume', self._volume)
            # Seleccionar voz en español
            try:
                for v in engine.getProperty('voices'):
                    vid = v.id.lower()
                    langs = [str(l).lower() for l in (getattr(v, 'languages', []) or [])]
                    if any('es' in l for l in langs) or 'spanish' in vid or '/es' in vid:
                        engine.setProperty('voice', v.id)
                        break
            except Exception:
                pass
            # Prueba rápida: si say + runAndWait no explotan, funciona
            engine.say("")
            engine.runAndWait()
            self._engine = engine
            self._backend = "pyttsx3"
            print("[Hablador] Backend: pyttsx3")
            return True
        except Exception as exc:
            print(f"[Hablador] pyttsx3 falló ({exc}), probando espeak directo...")
            return False

    def _init_espeak(self) -> bool:
        """Verifica que espeak-ng/espeak esté disponible."""
        if not ESPEAK_DISPONIBLE:
            return False
        # Verificar que la voz en español exista
        try:
            subprocess.run(
                [_ESPEAK_CMD, "--voices=es"], capture_output=True, timeout=5
            )
        except Exception:
            pass  # si falla el listado, igual intentamos
        self._backend = "espeak"
        print(f"[Hablador] Backend: {_ESPEAK_CMD}")
        return True

    # ────────────────── Hablar ──────────────────

    def _hablar_pyttsx3(self, texto: str):
        try:
            self._engine.say(texto)
            self._engine.runAndWait()
        except Exception as exc:
            print(f"[Hablador] Error pyttsx3: {exc}")

    def _hablar_espeak(self, texto: str):
        """Llama a espeak-ng/espeak directamente como subproceso."""
        try:
            # -v es  → voz en español
            # -s N   → velocidad (palabras por minuto)
            # -a N   → amplitud (0-200)
            speed = str(self._rate)
            amp = str(int(self._volume * 100))
            subprocess.run(
                [_ESPEAK_CMD, "-v", "es", "-s", speed, "-a", amp, texto],
                capture_output=True, timeout=30
            )
        except subprocess.TimeoutExpired:
            print("[Hablador] espeak timeout")
        except Exception as exc:
            print(f"[Hablador] Error espeak: {exc}")

    # ────────────────── Worker ──────────────────

    def _worker(self):
        # Intentar backends en orden de preferencia
        if not self._init_pyttsx3():
            if not self._init_espeak():
                print("[Hablador] No hay motor TTS disponible. "
                      "Instala espeak-ng: sudo apt install espeak-ng")
                return

        hablar_fn = (self._hablar_pyttsx3 if self._backend == "pyttsx3"
                     else self._hablar_espeak)

        while True:
            item = self._cola.get()
            if item is None:
                break
            texto, callback = item
            hablar_fn(texto)
            if callback:
                try:
                    callback()
                except Exception as exc:
                    print(f"[Hablador] Error en callback: {exc}")
