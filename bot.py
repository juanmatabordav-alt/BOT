import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from google import genai
from config import PROMPT_MEJOR_VERSION, PROMPT_PEOR_VERSION
from gtts import gTTS  # <--- Nueva librería para la voz

# Cargar las claves del archivo .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Conectar con la Inteligencia Artificial de Google
client = genai.Client(api_key=GEMINI_KEY)

def preguntar_ia(mensaje_usuario, personalidad):
    """Le envía el mensaje a la IA con la personalidad elegida"""
    respuesta = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=mensaje_usuario,
        config={'system_instruction': personalidad}  # <--- Aquí decía 'personality', cámbialo a 'personalidad'
    )
    return respuesta.text

async def responder_en_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Se ejecuta cada vez que tecleas algo en el celular"""
    texto_usuario = update.message.text
    chat_id = update.effective_chat.id
    
    # Enviar un aviso al celular de que está pensando
    mensaje_espera = await update.message.reply_text("⚡ Tus dos versiones están discutiendo... Grabando audios.")
    
    try:
        # 1. Conseguir las respuestas en texto de ambos lados
        mejor_res = preguntar_ia(texto_usuario, PROMPT_MEJOR_VERSION)
        peor_res = preguntar_ia(texto_usuario, PROMPT_PEOR_VERSION)
        
        # 2. Convertir el texto de la MEJOR VERSIÓN a audio
        tts_mejor = gTTS(text=f"Tu mejor versión dice: {mejor_res}", lang='es', tld='com')
        archivo_mejor = "mejor_version.mp3"
        tts_mejor.save(archivo_mejor)
        
        # 3. Convertir el texto de la PEOR VERSIÓN a audio
        tts_peor = gTTS(text=f"Tu peor versión dice: {peor_res}", lang='es', tld='com')
        archivo_peor = "peor_version.mp3"
        tts_peor.save(archivo_peor)
        
        # 4. Borrar el aviso de espera
        await context.bot.delete_message(chat_id=chat_id, message_id=mensaje_espera.message_id)
        
        # 5. Enviar los audios al celular
        await update.message.reply_text("🚀 *[TU MEJOR VERSIÓN]:*", parse_mode="Markdown")
        with open(archivo_mejor, 'rb') as audio:
            await context.bot.send_voice(chat_id=chat_id, voice=audio)
            
        await update.message.reply_text("😈 *[TU PEOR VERSIÓN]:*", parse_mode="Markdown")
        with open(archivo_peor, 'rb') as audio:
            await context.bot.send_voice(chat_id=chat_id, voice=audio)
            
        # 6. Limpieza: Borrar los archivos temporales de la PC
        os.remove(archivo_mejor)
        os.remove(archivo_peor)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    print("📱 Bot por voz encendido y escuchando en Telegram...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_en_telegram))
    app.run_polling()