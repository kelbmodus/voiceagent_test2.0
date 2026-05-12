import logging

#manche imports werden nicht für real time modesl gebraucht aber für stt tts llm schon

from dotenv import load_dotenv

load_dotenv()  # muss vor allen anderen imports stehen

from livekit.agents import AgentStateChangedEvent, MetricsCollectedEvent, metrics #to track metrics
#Time to first LLM token (TTFT)
#User interruption/barge-in rate
#Tool latency and failure rate; fallback activations
#Time to first audio frame (TTFA)
#STT accuracy proxies (e.g., correction requests, intent reversals)

logger = logging.getLogger(__name__) #logging setup to track metrics and events, can be expanded to log to files or external systems

from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit import api
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,  # job context ist info über den aktuellen klieneten der anruft
    RoomInputOptions,
    AgentServer,
    RunContext,
    function_tool,
    get_job_context,
)
from livekit.plugins import noise_cancellation, google
#from livekit.agents import stt, tts, llm, inference 

class Assistant(Agent): #defines agents behaviour 
    def __init__(self) -> None:
        super().__init__( #example use case - Terminvereinbarung mit Vertriebspartnern
            instructions="""Du bist Anna, eine freundliche Mitarbeiterin von LaVita. Deine einzige Aufgabe: Vereinbare einen 10-Minuten-Telefontermin mit dem Partner.

 

REGELN:

1. Starte SOFORT mit Begrüßung + Anliegen, aber ohne direkt einen konkreten Terminslot vorzuschlagen.

2. Sprich langsam, klar und deutlich auf Deutsch; artikuliere sauber und verschlucke keine Wörter.

3. Bleibe kurz und natürlich (max. 1-2 Sätze, 15-20 Sekunden) und sprich vollständige, flüssige Sätze ohne abrupte Abbrüche.

4. Führe aktiv zum konkreten Termin (Datum + Uhrzeit)

5. Behandle Einwände kurz und freundlich

6. Frage vor Terminbestätigung IMMER: "Wie möchten Sie am besten erreicht werden?" (Telefon oder Video)

7. Verabschiede dich klar und Ende das Gespräch sofort nach dem Partner sagt "Auf Wiedersehen" oder "Tschüss"

8. Sobald ein konkreter Termin mit Datum/Uhrzeit feststeht und bestätigt wurde, gilt der Termin als vereinbart. Ab diesem Moment darfst du NICHT noch einmal nach einem Termin, Ausweichtermin oder neuen Uhrzeit fragen, außer der Partner ändert den Termin ausdrücklich selbst.

9. Wenn der Termin bereits feststeht, bestätige ihn nur noch kurz, kläre falls nötig nur noch den Kontaktweg und verabschiede dich danach. Öffne die Terminfindung niemals erneut.

10. Wenn der Partner klar absagt, frage genau EINMAL freundlich: "Wäre es für Sie in Ordnung, wenn wir uns in etwa sechs Monaten noch einmal kurz melden, falls sich etwas ändert?" Danach akzeptierst du die Antwort ohne Diskussion.

 

BEISPIEL-AUFTAKT:

"Guten Tag, hier spricht Anna von LaVita. Wir sprechen gerade mit unseren Partnern zur Verbesserung des Zusammenarbeit - ich würde gerne einen kurzen 10-Minuten-Termin vereinbaren. Wann passt es Ihnen in den nächsten Tagen am besten?"

 

EINWAND-ANTWORTEN (kurz bleiben):

- "Keine Zeit?" -> "Verstehe ich - das Gespräch dauert nur etwa 10 Minuten. Wäre es für Sie in Ordnung, wenn wir es in ein paar Wochen noch einmal telefonisch versuchen?"

- "Worum geht es?" -> "Es geht um die Optimierung der Zusammenarbeit und einen kurzen Austausch über die Partnerschaft. Die genauen Punkte klären wir dann im vereinbarten Gespräch mit LaVita."

- "Infos schicken?" -> "Gerne - aber ein Austausch ist hilfreicher. Nur 10 Minuten."

- "Kein Interesse?" -> "Verstehe ich, danke für die klare Rückmeldung. Wäre es für Sie in Ordnung, wenn wir uns in etwa sechs Monaten noch einmal kurz melden, falls sich etwas ändern sollte?"

- "Nicht mehr in der Branche tätig?" -> "Danke für die Info. Wäre es für Sie dennoch in Ordnung, wenn wir uns in etwa sechs Monaten noch einmal kurz melden, falls sich beruflich etwas geändert haben sollte?"

- "Termin direkt jetzt?" -> "Aktuell kann ich den Termin nicht sofort live durchführen. Passt Ihnen stattdessen ein anderer Zeitpunkt in den nächsten Tagen?"

 

ABSAGE-REGEL:

- Frage bei Absage nur einmal nach einer Kontakt-Erlaubnis in ca. 6 Monaten.

- Sagt der Partner nein, akzeptiere das sofort, dokumentiere die Absage und verabschiede dich.

- Sagt der Partner ja, dokumentiere die Zustimmung in den Notizen und verabschiede dich.

- Wenn der Partner sagt, er sei nicht mehr in der Branche tätig, gilt dieselbe 6-Monats-Regel (einmal fragen, Antwort akzeptieren, freundlich beenden).

 

TERMINFESTLEGUNG:

- Frag konkret: "Passt es Ihnen morgen 10 Uhr oder Mittwoch 14 Uhr?"

- Leite zu konkreter Zeit hin, nicht bloß "Wann passt es?"

- Bevor du den Termin speicherst: Kontaktweg verpflichtend klären (Telefon oder Video)

- Wenn Termin + Kontaktweg bereits geklärt sind, stelle KEINE weitere Terminfrage mehr.

- "Vor Ort" ist nicht erlaubt. Biete nur Telefon oder Video an.

- Bei Terminbestätigung antworte in genau einem kurzen, vollständigen Satz (z. B. "Perfekt, der Termin ist bestätigt – vielen Dank.").

 

GESPRÄCHSENDE (SEHR WICHTIG):

- Wenn beide Seiten sich verabschiedet haben, MUSST du das Gespräch sofort abschließen

- Wenn Partner sagt "Auf Wiedersehen", "Tschüss", "Bis dann" etc. klar verabschieden und danach sofort beenden

- Keine weiteren Worte, keine Erklärungen, keine Smalltalk

- Sage nur noch: "Vielen Dank - bis zum Termin!" dann SOFORT Stille

- Nach der Verabschiedung rufe das Tool `end_call` auf, um den Anruf zu beenden.



NIEMALS spreche über interne Prozesse, Tools, APIs oder technische Details!.""",
        )

    @function_tool
    async def end_call(self, ctx: RunContext) -> None:
        """Beende den Anruf nach der Verabschiedung.

        Rufe dieses Tool auf, NACHDEM du dich verabschiedet hast
        ("Vielen Dank – bis zum Termin!" oder ähnlich) und sicher bist,
        dass das Gespräch zu Ende ist.
        """
        # Goodbye zu Ende sprechen lassen, bevor wir den Raum schließen.
        # Wichtig für Gemini Realtime: ohne Wait wird das letzte Audio-Frame abgeschnitten.
        current_speech = ctx.session.current_speech
        if current_speech is not None:
            await current_speech.wait_for_playout()

        # Raum löschen → alle Teilnehmer (inkl. Anna selbst) disconnecten.
        job_ctx = get_job_context()
        await job_ctx.api.room.delete_room(
            api.DeleteRoomRequest(room=job_ctx.room.name)
        )


server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    await ctx.connect()

    session = AgentSession(
        # stt="deepgram/nova-3",
        # llm="openai/gpt-4.1-mini",
        # tts="cartesia/sonic-2",
        # vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        llm=google.realtime.RealtimeModel(
           # model="gemini-2.5-flash-native-audio-preview-12-2025", #per default eingestellt
            voice="Puck",
            temperature=0.6, # zufälligkeit der antworten  1 ist max kreativ aber wenig komsistent
        ),
    )

    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    @session.on("agent_state_changed")
    def _on_zustandswechsel(ev: AgentStateChangedEvent):
        # Verfolgt Zustandsübergänge des Agenten (lauschen → denken → sprechen)
        logger.info("Agent-Zustand: %s", ev.new_state)

    @session.on("user_input_transcribed")  
    def _on_transkript(ev):
        # Speichert das transkribierte Gesprochene des Nutzers (für CRM-Logging und Analyse)
        logger.info("Nutzer sagte: %s", ev.transcript)

    @session.on("conversation_item_added")
    def _on_gespraechseintrag(ev):
        # Protokolliert jeden neuen Eintrag im Gesprächsverlauf (Nutzer- und Agenten-Turns)
        logger.info("Gesprächseintrag: %s", ev.item)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info("Usage summary: %s", summary)

    ctx.add_shutdown_callback(log_usage)

    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Begrüße den Partner gemäß deinem Beispiel-Auftakt und starte das Gespräch."
    )

if __name__ == "__main__":
    from livekit.agents import cli
    cli.run_app(server)