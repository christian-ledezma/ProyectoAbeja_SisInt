"""
Módulo de reconocimiento de emociones por voz.

Usa SpeechRecognition para capturar audio del micrófono,
transcribe a texto y detecta emociones mediante palabras clave en español.

Dependencias:
    pip install SpeechRecognition PyAudio
    (Linux: sudo apt install portaudio19-dev antes de PyAudio)
"""

import threading

try:
    import speech_recognition as sr
    SR_DISPONIBLE = True
except ImportError:
    SR_DISPONIBLE = False
    print("WARNING: Instala SpeechRecognition → pip install SpeechRecognition")


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
