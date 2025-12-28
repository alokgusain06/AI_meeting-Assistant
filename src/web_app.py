"""Flask web application for Meeting Assistant UI."""
import asyncio
import threading
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.conversation import ConversationManager
from src.reasoner import MeetingReasoner
from src.transcriber import MockTranscriber
from config.settings import settings

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = 'meeting-assistant-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global instances
conversation_manager: ConversationManager = None
reasoner: MeetingReasoner = None
transcriber: MockTranscriber = None
assistant_running = False
event_loop: asyncio.AbstractEventLoop = None


def run_async(coro):
    """Run async coroutine in the event loop."""
    global event_loop
    if event_loop is None:
        event_loop = asyncio.new_event_loop()
        threading.Thread(target=event_loop.run_forever, daemon=True).start()
    future = asyncio.run_coroutine_threadsafe(coro, event_loop)
    return future.result(timeout=30)


def init_components():
    """Initialize the assistant components."""
    global conversation_manager, reasoner
    conversation_manager = ConversationManager(
        context_window_minutes=settings.CONTEXT_WINDOW_MINUTES
    )
    reasoner = MeetingReasoner()


@app.route('/')
def index():
    """Main page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get assistant status."""
    return jsonify({
        'running': assistant_running,
        'segments': run_async(conversation_manager.get_segment_count()) if conversation_manager else 0
    })


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get meeting summary."""
    if not conversation_manager or not reasoner:
        return jsonify({'error': 'Assistant not initialized'}), 400
    
    context = run_async(conversation_manager.get_recent_context())
    summary = run_async(reasoner.generate_summary(context))
    return jsonify({'summary': summary})


@app.route('/api/ask', methods=['POST'])
def ask_question():
    """Ask a question about the meeting."""
    if not conversation_manager or not reasoner:
        return jsonify({'error': 'Assistant not initialized'}), 400
    
    data = request.json
    question = data.get('question', '')
    
    if not question:
        return jsonify({'error': 'No question provided'}), 400
    
    context = run_async(conversation_manager.get_recent_context())
    answer = run_async(reasoner.answer_question(question, context))
    return jsonify({'answer': answer})


@app.route('/api/topic', methods=['GET'])
def get_current_topic():
    """Get the current topic being discussed."""
    if not conversation_manager or not reasoner:
        return jsonify({'error': 'Assistant not initialized'}), 400
    
    context = run_async(conversation_manager.get_recent_context())
    topic = run_async(reasoner.identify_current_topic(context))
    return jsonify({'topic': topic})


@app.route('/api/transcript', methods=['GET'])
def get_transcript():
    """Get the full transcript."""
    if not conversation_manager:
        return jsonify({'error': 'Assistant not initialized'}), 400
    
    transcript = run_async(conversation_manager.get_full_transcript())
    return jsonify({'transcript': transcript})


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('[WebSocket] Client connected')
    emit('status', {'running': assistant_running})


@socketio.on('start_demo')
def handle_start_demo():
    """Start the demo mode with mock transcription."""
    global transcriber, assistant_running
    
    if assistant_running:
        emit('error', {'message': 'Demo already running'})
        return
    
    async def on_transcript(text: str, is_final: bool):
        """Handle transcript from mock transcriber."""
        if is_final:
            await conversation_manager.add_segment(text, speaker="Demo Speaker")
            socketio.emit('transcript', {
                'text': text,
                'speaker': 'Demo Speaker',
                'is_final': is_final
            })
    
    transcriber = MockTranscriber(on_transcript)
    run_async(transcriber.start())
    assistant_running = True
    
    emit('status', {'running': True, 'message': 'Demo started'})
    print('[Demo] Started mock transcription')


@socketio.on('stop_demo')
def handle_stop_demo():
    """Stop the demo mode."""
    global transcriber, assistant_running
    
    if transcriber:
        run_async(transcriber.stop())
        transcriber = None
    
    assistant_running = False
    emit('status', {'running': False, 'message': 'Demo stopped'})
    print('[Demo] Stopped')


@socketio.on('clear_transcript')
def handle_clear():
    """Clear the transcript."""
    if conversation_manager:
        run_async(conversation_manager.clear())
        emit('status', {'message': 'Transcript cleared'})


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Run the Flask server."""
    init_components()
    print(f"\n🎙️  Meeting Assistant Web UI")
    print(f"   Open http://localhost:{port} in your browser\n")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_server(debug=True)
