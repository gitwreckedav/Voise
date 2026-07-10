"""
Sockets are the app's plug points.

The GUI only ever talks to a socket (Recorder, STT, LLM) — never to a
provider like Whisper or Ollama directly. To swap a provider later,
change the socket file; the GUI stays untouched.
"""
