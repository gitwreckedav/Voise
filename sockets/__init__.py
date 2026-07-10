"""
Sockets are the app's plug points.

The GUI only ever talks to a socket (Recorder, STT, LLM) - never to a
provider like Whisper or Ollama directly. To swap a provider later,
change the socket file; the GUI stays untouched.

Every socket keeps a simple `info` dictionary (provider, model, status,
current operation, last operation...). The GUI polls these dictionaries
a few times per second to fill the status row and the developer panel -
that's how Voise stays a glass box instead of a black box.
"""
